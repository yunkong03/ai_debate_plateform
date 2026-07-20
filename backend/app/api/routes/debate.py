import json
import logging
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.schemas import DebateResponse, DebateRequest, ExpertOpinion
from app.graph.build_graph import build_graph
from app.graph.state import DebateState

router = APIRouter(prefix="/debate", tags=["debate"])
logger = logging.getLogger(__name__)

# state.py의 operator.add 리듀서가 붙은 필드. 스트림 중간 결과를 로컬에서
# 다시 합칠 때도 덮어쓰지 않고 이 필드만 이어붙여야 그래프 동작과 일치한다.
_LIST_REDUCER_KEYS = {"messages", "evidence", "history"}


def _initial_state(topic: str) -> DebateState:
    return {
        "topic": topic,
        "plan": {},
        "workers": [],
        "messages": [],
        "evidence": [],
        "scores": {},
        "history": [],
        "current_round": 0,
        "max_round": 0,
        "judge_result": None,
    }


def _apply_update(state: Dict[str, Any], update: Dict[str, Any]) -> None:
    for key, value in update.items():
        if key in _LIST_REDUCER_KEYS and isinstance(value, list):
            state[key] = state.get(key, []) + value
        else:
            state[key] = value


def _stage_name(node_name: str, node_output: Dict[str, Any]) -> str:
    """SSE event 이름. worker 노드는 실행된 expert(economist_pro 등)로 구분한다."""
    if node_name == "worker":
        messages = node_output.get("messages") or []
        if messages:
            return messages[0].get("speaker", node_name)
    return node_name


def _sse(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _to_response(topic: str, state: Dict[str, Any]) -> DebateResponse:
    plan = state.get("plan") or {}
    history = state.get("history") or []
    judge_result = state.get("judge_result") or {}
    return DebateResponse(
        topic=topic,
        experts=state.get("workers", []),
        rounds=plan.get("rounds", 0),
        opinions=[
            ExpertOpinion(expert=m["speaker"], content=m["content"])
            for m in state.get("messages", [])
        ],
        summary=history[-1]["summary"] if history else None,
        verdict=judge_result.get("verdict"),
    )


async def _stream_debate(topic: str) -> AsyncGenerator[str, None]:
    """Planner → Worker(들) → Aggregate → Judge → 최종 응답 순서로 SSE 이벤트를 내보낸다."""
    state = _initial_state(topic)
    try:
        graph = build_graph()
        for chunk in graph.stream(state, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                _apply_update(state, node_output)
                yield _sse(_stage_name(node_name, node_output), node_output)
        yield _sse("final", _to_response(topic, state).model_dump())
    except Exception as exc:
        # 스트림은 이미 200으로 시작된 뒤라 상태코드를 바꿀 수 없으므로
        # SSE error 이벤트로 실패를 알린다.
        logger.exception("debate stream failed")
        yield _sse("error", {"message": str(exc)})


@router.post("")
def start_debate(request: DebateRequest) -> StreamingResponse:
    """토론을 시작하고 Worker 실행 과정을 SSE(Server-Sent Events)로 스트리밍한다."""
    topic = request.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="topic은 비어 있을 수 없습니다.")

    return StreamingResponse(_stream_debate(topic), media_type="text/event-stream")
