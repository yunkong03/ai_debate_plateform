from typing import List

from app.graph.state import DebateState, Message, RoundSummary
from app.llm.base import BaseLLM
from app.llm.factory import get_llm

# Aggregate(사회자)가 사용할 LLM. 최종 판정은 judge 노드(Worker role="judge")가 담당한다.
_llm: BaseLLM = get_llm()

AGGREGATE_PROMPT = """당신은 AI 토론의 사회자입니다.
토론 주제: "{topic}"

지금까지 나온 발언:
{transcript}

각 참가자의 핵심 주장을 균형 있게 정리해 요약하세요. JSON이 아닌 요약 텍스트만 출력합니다.
"""


def _format_transcript(messages: List[Message]) -> str:
    if not messages:
        return "(아직 발언 없음)"
    return "\n".join(f"- {m['speaker']}: {m['content']}" for m in messages)


def aggregate_node(state: DebateState) -> DebateState:
    """Worker들의 발언을 모아 사회자 요약을 만들고 history에 기록한다."""
    transcript = _format_transcript(state.get("messages", []))
    prompt = AGGREGATE_PROMPT.format(topic=state["topic"], transcript=transcript)
    summary = _llm.generate(prompt)

    entry: RoundSummary = {"round": state["current_round"], "summary": summary}
    return {"history": [entry]}
