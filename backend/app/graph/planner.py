import json
from typing import List, Optional, TypedDict

from app.graph.state import DebateState
from app.graph.worker import DEFAULT_TOOL_REGISTRY, ToolRegistry
from app.llm.base import BaseLLM
from app.llm.factory import get_llm

# Planner가 사용할 LLM. BaseLLM 인터페이스로만 다루며, provider는 LLM_PROVIDER
# 설정(get_llm)으로 고른다.
_llm: BaseLLM = get_llm()


PLANNER_PROMPT = """당신은 AI 토론 플랫폼의 Planner입니다.
사용자가 입력한 토론 주제를 분석하여 아래 JSON 형식으로만 답하세요.
설명이나 코드블록 없이 JSON 객체 하나만 출력합니다.

{{
  "topic": "<주제를 한 문장으로 정리>",
  "workers": [
    {{"role": "<전문가 역할>", "stance": "<pro|con|null>", "tools": ["<이 worker가 쓸 tool 이름>"]}}
  ],
  "rounds": <라운드 수(정수)>
}}

규칙:
- 찬반이 갈리는 주제는 같은 role을 stance만 다르게(pro/con) 두 번 넣습니다.
- 사실 검증이 필요하면 role "fact_checker"를 추가합니다. stance는 없어도 됩니다.
- 마지막 항목은 항상 role "judge"이며 보통 tools가 필요 없습니다.
- rounds는 주제의 복잡도에 따라 1~5 사이 정수로 정합니다.
- tools는 해당 worker만 사용할 수 있는 tool 이름 배열입니다(없으면 빈 배열).
  현재 구현된 tool은 "search"뿐입니다. 다른 이름을 적어도 아직 실행되지는 않습니다.

예시 workers 출력:
[
  {{"role": "economist", "stance": "pro", "tools": ["search"]}},
  {{"role": "economist", "stance": "con", "tools": ["search"]}},
  {{"role": "fact_checker", "tools": ["search", "filesystem"]}},
  {{"role": "judge", "tools": []}}
]

토론 주제: "{topic}"
"""


class WorkerSpec(TypedDict):
    role: str
    stance: Optional[str]
    tools: List[str]


class PlanResult(TypedDict):
    topic: str
    workers: List[WorkerSpec]
    rounds: int


def _build_prompt(topic: str) -> str:
    return PLANNER_PROMPT.format(topic=topic)


def _normalize_stance(raw: object) -> Optional[str]:
    """LLM이 JSON null 대신 문자열 "null"/"none"을 주는 경우까지 처리한다.

    (실제 확인된 버그: stance="null" 문자열이 그대로 들어가 워커 id가
    'economist_null'처럼 생성됨 — _worker_id/​build_graph._flat_id가
    전부 이 함수의 출력을 기준으로 동작하므로 여기서 한 번만 정리하면 된다.)
    """
    if not isinstance(raw, str):
        return None
    normalized = raw.strip()
    if not normalized or normalized.lower() in ("null", "none"):
        return None
    return normalized


def _parse_plan(raw_response: str) -> PlanResult:
    """LLM이 반환한 JSON 문자열을 PlanResult로 파싱한다."""
    data = json.loads(raw_response)
    return PlanResult(
        topic=data["topic"],
        workers=[
            WorkerSpec(role=w["role"], stance=_normalize_stance(w.get("stance")), tools=w.get("tools", []))
            for w in data["workers"]
        ],
        rounds=data["rounds"],
    )


def _worker_id(worker: WorkerSpec) -> str:
    """그래프 노드 이름으로 쓸 flat id. 예: economist+pro -> 'economist_pro'."""
    stance = worker.get("stance")
    return f"{worker['role']}_{stance}" if stance else worker["role"]


def tool_registry_for(worker: WorkerSpec) -> ToolRegistry:
    """worker의 tools 목록만 담은 ToolRegistry. worker는 자신의 tool만 쓸 수 있다."""
    tools = [DEFAULT_TOOL_REGISTRY.get(name) for name in worker.get("tools", [])]
    return ToolRegistry([t for t in tools if t is not None])


def planner_node(state: DebateState) -> DebateState:
    """주제를 분석해 workers(role+stance+tools)/rounds가 담긴 plan을 만든다.

    LLM 호출은 BaseLLM 인터페이스(_llm.generate)로만 이루어지며,
    concrete 구현체가 아직 없어 실제 모델은 호출되지 않는다.
    """
    prompt = _build_prompt(state["topic"])
    raw_response = _llm.generate(prompt)  # TODO: 실제 provider 연결 후 그대로 동작
    plan = _parse_plan(raw_response)

    return {
        "plan": dict(plan),
        "workers": [_worker_id(w) for w in plan["workers"]],
        "max_round": plan["rounds"],
        "current_round": 0,
    }
