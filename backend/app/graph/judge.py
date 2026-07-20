from app.graph.state import DebateState


def judge_node(state: DebateState) -> DebateState:
    """Aggregate(사회자 요약) 이후, 토론 전체를 검토해 최종 판정을 내린다."""
    # TODO: LLM 호출로 judge_result(승자/근거/점수) 결정
    raise NotImplementedError
