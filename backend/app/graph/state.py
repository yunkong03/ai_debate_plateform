import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class Message(TypedDict):
    """토론 중 한 발언 단위 (전문가/사회자 등)."""

    round: int
    speaker: str
    content: str


class Evidence(TypedDict):
    """팩트체커가 MCP로 조사한 근거 자료 한 건."""

    round: int
    speaker: str
    source: str
    content: str


class RoundSummary(TypedDict):
    """라운드별 요약 로그 (history 항목)."""

    round: int
    summary: str


class DebateState(TypedDict):
    """LangGraph 노드 간에 공유되는 토론 상태.

    workers는 병렬로 실행되며 messages/evidence/history에 동시에 기록하므로,
    해당 리스트 필드는 operator.add 리듀서로 병합한다. 리듀서가 없으면
    병렬 브랜치가 같은 키를 동시에 덮어써 LangGraph에서 충돌 오류가 난다.
    """

    topic: str
    plan: Dict[str, Any]
    workers: List[str]
    messages: Annotated[List[Message], operator.add]
    evidence: Annotated[List[Evidence], operator.add]
    scores: Dict[str, float]
    history: Annotated[List[RoundSummary], operator.add]
    current_round: int
    max_round: int
    judge_result: Optional[Dict[str, Any]]
