import asyncio
import concurrent.futures
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict

from fastmcp import Client as FastMCPSDKClient

from app.core.config import get_settings
from app.graph.state import DebateState, Evidence, Message
from app.llm.base import BaseLLM
from app.llm.factory import get_llm

# Worker가 사용할 LLM. BaseLLM 인터페이스로만 다루며, provider는 LLM_PROVIDER
# 설정(get_llm)으로 고른다.
_llm: BaseLLM = get_llm()

logger = logging.getLogger(__name__)


# ---------- Tool ----------


class Tool(ABC):
    """Worker가 사용할 수 있는 Tool의 공통 인터페이스."""

    name: str
    description: str

    @abstractmethod
    def run(self, query: str) -> str:
        """Tool을 실행하고 Observation 문자열을 반환한다."""
        raise NotImplementedError


class MCPClient(ABC):
    """MCP 서버와 통신하는 클라이언트 인터페이스. Tool 내부에서만 사용되며,
    Worker는 이 클래스의 존재를 알지 못한다(Worker는 Tool.run()만 호출)."""

    @abstractmethod
    def call_tool(self, tool_name: str, query: str) -> str:
        raise NotImplementedError


def _run_async(coro: Any) -> Any:
    """동기 Tool.run()에서 fastmcp의 비동기 Client를 호출하기 위한 브리지.

    FastAPI 요청 처리 중(이미 실행 중인 이벤트 루프 안)에 불려도 동작하도록,
    그 경우엔 별도 스레드에서 asyncio.run()을 돈다.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def _extract_text(result: Any) -> str:
    """fastmcp CallToolResult에서 사람이 읽을 텍스트만 뽑아낸다."""
    if isinstance(result.data, str):
        return result.data
    texts = [getattr(block, "text", None) for block in result.content]
    texts = [t for t in texts if t]
    if texts:
        return "\n".join(texts)
    return str(result.data if result.data is not None else result.content)


class FastMCPClient(MCPClient):
    """실제 MCP 서버(fastmcp)에 연결해 tool을 호출하는 클라이언트."""

    def __init__(self, server_url: str):
        self.server_url = server_url

    def call_tool(self, tool_name: str, query: str) -> str:
        return _run_async(self._call_tool_async(tool_name, query))

    async def _call_tool_async(self, tool_name: str, query: str) -> str:
        async with FastMCPSDKClient(self.server_url) as client:
            result = await client.call_tool(tool_name, {"query": query})
        return _extract_text(result)


class MockMCPClient(MCPClient):
    """MCP 서버 없이 고정된 Mock 데이터를 반환하는 클라이언트.

    MCP_SERVER_URL이 설정되지 않았을 때 기본으로 쓰여, 서버 없이도 시연 가능하다.
    """

    def call_tool(self, tool_name: str, query: str) -> str:
        return f"[MOCK] '{query}' 검색 결과: 관련 자료를 찾을 수 없음(검색 미연결)."


def _default_mcp_client() -> MCPClient:
    server_url = get_settings().mcp_server_url
    return FastMCPClient(server_url) if server_url else MockMCPClient()


class SearchTool(Tool):
    """자료 검색 Tool. 내부적으로 MCPClient를 통해 검색 결과를 가져온다.

    MCP_SERVER_URL이 설정되어 있으면 FastMCPClient, 없으면 MockMCPClient를 쓴다.
    시연용으로 고정하려면 SearchTool(mcp_client=MockMCPClient())처럼 직접 넘기면 된다.
    """

    name = "search"
    description = "주어진 질의와 관련된 자료를 검색한다."

    def __init__(self, mcp_client: Optional[MCPClient] = None):
        self._mcp = mcp_client or _default_mcp_client()

    def run(self, query: str) -> str:
        try:
            return self._mcp.call_tool(self.name, query)
        except Exception:
            # 실제 MCP 서버가 죽어있거나 접속 실패해도 토론 전체가 죽지 않도록
            # Mock으로 폴백한다.
            logger.warning("[search] MCP 호출 실패, Mock으로 폴백", exc_info=True)
            return MockMCPClient().call_tool(self.name, query)


# ---------- Tool Registry ----------


class ToolRegistry:
    """이름으로 Tool을 조회하는 레지스트리."""

    def __init__(self, tools: Optional[List[Tool]] = None):
        self._tools: Dict[str, Tool] = {tool.name: tool for tool in (tools or [])}

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def describe(self) -> str:
        """Reason 프롬프트에 넣을 사용 가능 Tool 목록 설명."""
        return "\n".join(f"- {t.name}: {t.description}" for t in self._tools.values())


DEFAULT_TOOL_REGISTRY = ToolRegistry([SearchTool()])


# ---------- Reason 프롬프트 ----------

# stance("pro"/"con")를 영어 토큰 그대로 주면 모델이 무시하는 경우가 있어
# (실제 확인됨: con으로 배정된 worker가 찬성 발언을 함) 한국어로 명확히 못박는다.
_STANCE_LABELS = {
    "pro": "찬성 (토론 주제에 적극 동의하는 입장)",
    "con": "반대 (토론 주제에 반대하는 입장)",
}


def _stance_label(stance: Optional[str]) -> str:
    return _STANCE_LABELS.get(stance, "중립 (특정 편을 들지 않는 입장)")


REASON_PROMPT = """당신은 AI 토론 참가자 '{role}'입니다. 당신에게 배정된 입장: {stance_label}
토론 주제: "{topic}"

지금까지의 토론 내용:
{transcript}

사용 가능한 Tool:
{tools}

먼저 현재 상황을 판단하고, 발언 전에 Tool 사용이 필요한지 스스로 결정하세요.
반드시 아래 JSON 형식만 반환하세요. 다른 텍스트는 포함하지 않습니다.

{{
  "need_tool": <true 또는 false>,
  "tool": "<사용할 tool 이름, 필요 없으면 null>",
  "reason": "<need_tool을 그렇게 판단한 이유>"
}}
"""

# 일반 토론 참가자(전문가)용. 다른 참가자 발언에 반박/보강할 수 있게 transcript를 준다.
DEBATER_ANSWER_PROMPT = """당신은 AI 토론 참가자 '{role}'입니다. 당신에게 배정된 입장: {stance_label}
이 입장을 절대 바꾸지 말고 끝까지 유지하며 발언하세요. 같은 role이라도 입장이 다른 참가자가 있다면 그 주장을 반박하세요.

토론 주제: "{topic}"

지금까지의 토론 내용:
{transcript}

판단(reason): {reason}
Observation: {observation}

위 내용을 반영해 이번 라운드 발언을 작성하세요.
JSON이 아닌 발언 텍스트만 출력합니다.
"""

# role="judge"인 Worker용. "이번 라운드 발언"이 아니라 최종 판정을 요구한다.
JUDGE_ANSWER_PROMPT = """당신은 AI 토론의 Judge입니다.
토론 주제: "{topic}"

지금까지의 토론 내용:
{transcript}

판단(reason): {reason}
Observation: {observation}

위 토론 내용을 검토해 최종 판정을 내리세요. 어느 쪽 주장이 더 설득력 있었는지와 그 이유를 밝히세요.
JSON이 아닌 판정 텍스트만 출력합니다.
"""


class ReasonDecision(TypedDict):
    need_tool: bool
    tool: Optional[str]
    reason: str


def _split_expert(expert: str) -> Tuple[str, Optional[str]]:
    """'economist_pro' -> ('economist', 'pro'), 'fact_checker' -> ('fact_checker', None)."""
    if expert.endswith("_pro"):
        return expert[: -len("_pro")], "pro"
    if expert.endswith("_con"):
        return expert[: -len("_con")], "con"
    return expert, None


def _format_transcript(messages: List[Message]) -> str:
    if not messages:
        return "(아직 발언 없음)"
    return "\n".join(f"- {m['speaker']}: {m['content']}" for m in messages)


def _reason_prompt(
    topic: str, role: str, stance: Optional[str], registry: ToolRegistry, transcript: str
) -> str:
    return REASON_PROMPT.format(
        role=role,
        stance_label=_stance_label(stance),
        topic=topic,
        tools=registry.describe(),
        transcript=transcript,
    )


def _parse_reason(raw_response: str) -> ReasonDecision:
    data = json.loads(raw_response)
    return ReasonDecision(
        need_tool=bool(data.get("need_tool", False)),
        tool=data.get("tool"),
        reason=data.get("reason", ""),
    )


def _answer_prompt(
    topic: str, role: str, stance: Optional[str], reason: str, observation: Optional[str], transcript: str
) -> str:
    template = JUDGE_ANSWER_PROMPT if role == "judge" else DEBATER_ANSWER_PROMPT
    return template.format(
        role=role,
        stance_label=_stance_label(stance),
        topic=topic,
        reason=reason,
        observation=observation or "-",
        transcript=transcript,
    )


def make_worker_node(
    expert: str, tools: Optional[ToolRegistry] = None
) -> Callable[[DebateState], DebateState]:
    """Reason → Tool → Observation → 답변 순서로 동작하는 Worker 노드를 생성한다.

    expert: "economist_pro"처럼 planner가 만든 flat id (role[_stance]).
    """
    registry = tools or DEFAULT_TOOL_REGISTRY
    role, stance = _split_expert(expert)

    def worker_node(state: DebateState) -> DebateState:
        transcript = _format_transcript(state.get("messages", []))

        # 1. Reason (LLM): 현재 상황을 보고 Tool이 필요한지 판단
        reason_raw = _llm.generate(_reason_prompt(state["topic"], role, stance, registry, transcript))
        decision = _parse_reason(reason_raw)
        logger.info("[%s] [Reason] %s", expert, decision["reason"])

        # 2. Tool Decision(JSON): LLM이 반환한 need_tool로만 분기(규칙 기반 아님)
        observation: Optional[str] = None
        evidence: List[Evidence] = []
        if decision["need_tool"] and decision.get("tool"):
            tool = registry.get(decision["tool"])
            if tool is None:
                logger.info("[%s] [Tool] %s (등록되지 않은 tool, 건너뜀)", expert, decision["tool"])
            else:
                logger.info("[%s] [Tool] %s", expert, tool.name)
                # 3. Tool.run() → 4. Observation
                observation = tool.run(state["topic"])
                logger.info("[%s] [Observation] %s", expert, observation)
                evidence.append(
                    {
                        "round": state["current_round"],
                        "speaker": expert,
                        "source": tool.name,
                        "content": observation,
                    }
                )
        else:
            logger.info("[%s] [Tool] 불필요", expert)

        # 5. Final Answer (LLM): Observation을 Prompt에 추가해 한 번 더 호출
        answer = _llm.generate(
            _answer_prompt(state["topic"], role, stance, decision["reason"], observation, transcript)
        )
        logger.info("[%s] [Final] %s", expert, answer)

        message: Message = {
            "round": state["current_round"],
            "speaker": expert,
            "content": answer,
        }

        update: DebateState = {"messages": [message]}
        if evidence:
            update["evidence"] = evidence
        return update

    return worker_node


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    class _FakeLLM(BaseLLM):
        """Reason에서 search tool을 요청한 뒤 최종 답변을 내는 가짜 LLM (self-check용)."""

        def __init__(self):
            self._step = 0

        def generate(self, prompt: str) -> str:
            self._step += 1
            if self._step == 1:
                return json.dumps(
                    {
                        "need_tool": True,
                        "tool": "search",
                        "reason": "최신 통계가 필요하기 때문",
                    }
                )
            return "최종 주장: 기본소득은 소비 진작 효과가 있다."

    _llm = _FakeLLM()  # 모듈 전역 _llm을 self-check 동안만 교체

    node = make_worker_node("economist_pro")
    result = node({"topic": "기본소득 도입", "current_round": 1})

    assert result["messages"][0]["speaker"] == "economist_pro"
    assert result["messages"][0]["content"] == "최종 주장: 기본소득은 소비 진작 효과가 있다."
    assert result["evidence"][0]["source"] == "search"
    print("worker self-check OK")

    # FastMCPClient가 실제 MCP 서버와 통신하는지도 in-process로 검증한다.
    from fastmcp import FastMCP

    _test_server = FastMCP("test-search-server")

    @_test_server.tool
    def search(query: str) -> str:
        return f"OK: {query}"

    # server_url 자리에 FastMCP 인스턴스를 바로 넘기면 네트워크 없이 in-process로 붙는다.
    assert FastMCPClient(_test_server).call_tool("search", "기본소득") == "OK: 기본소득"
    print("FastMCPClient self-check OK")
