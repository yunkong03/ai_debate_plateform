from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

try:
    from langgraph.types import Send
except ImportError:  # 구버전 langgraph
    from langgraph.constants import Send

from app.graph.aggregate import aggregate_node
from app.graph.planner import planner_node, tool_registry_for
from app.graph.state import DebateState
from app.graph.worker import make_worker_node

WORKER_NODE = "worker"


def _flat_id(worker: Dict[str, Any]) -> str:
    """planner.py의 flat id 규칙과 동일: 'economist_pro', 'fact_checker', 'judge'."""
    stance = worker.get("stance")
    return f"{worker['role']}_{stance}" if stance else worker["role"]


def _dispatch_to_worker(state: DebateState) -> DebateState:
    """Send로 전달된 expert/tool 정보로 해당 worker 노드를 만들어 실행한다."""
    expert = state["expert"]
    registry = state.get("_tool_registry")
    return make_worker_node(expert, tools=registry)(state)


def _fan_out_workers(state: DebateState) -> List[Send]:
    """planner가 만든 workers를 기반으로 Worker를 Send API로 동적 병렬 실행한다.

    judge는 워커가 아니라 Aggregate 이후 별도 노드에서 실행하므로 제외한다.
    각 Send에는 해당 worker가 쓸 수 있는 tool만 담은 ToolRegistry를 함께 넘겨,
    worker가 자신에게 배정된 tool만 사용하도록 한다.
    """
    sends = []
    for worker in state["plan"]["workers"]:
        expert = _flat_id(worker)
        if expert == "judge":
            continue
        sends.append(
            Send(
                WORKER_NODE,
                {
                    "expert": expert,
                    "topic": state["topic"],
                    "current_round": state["current_round"],
                    "_tool_registry": tool_registry_for(worker),
                },
            )
        )
    return sends


def _judge_node(state: DebateState) -> DebateState:
    """Judge는 Worker(role="judge")를 그대로 재사용한다.

    Aggregate까지 거치며 모인 workers 결과(state["messages"]/["evidence"])를
    Worker Agent 루프(Reason→Tool→Observation→Final)에 그대로 태워 최종 판정을 내고,
    그 결과를 judge_result에도 담는다.
    """
    judge_spec = next(
        (w for w in state["plan"]["workers"] if _flat_id(w) == "judge"),
        {"role": "judge", "stance": None, "tools": []},
    )
    result = make_worker_node("judge", tools=tool_registry_for(judge_spec))(state)
    result["judge_result"] = {"verdict": result["messages"][0]["content"]}
    return result


def build_graph():
    """START → Planner → Workers(병렬, Send로 동적 생성) → Aggregate → Judge → END."""
    graph = StateGraph(DebateState)
    graph.add_node("planner", planner_node)
    graph.add_node(WORKER_NODE, _dispatch_to_worker)
    graph.add_node("aggregate", aggregate_node)
    graph.add_node("judge", _judge_node)

    graph.add_edge(START, "planner")
    graph.add_conditional_edges("planner", _fan_out_workers, [WORKER_NODE])
    graph.add_edge(WORKER_NODE, "aggregate")
    graph.add_edge("aggregate", "judge")
    graph.add_edge("judge", END)

    return graph.compile()
