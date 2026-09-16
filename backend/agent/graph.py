from langgraph.graph import StateGraph, START, END

from agent.state import RouterState
from agent.edges import route_after_decision
from agent.nodes import (
    classify_task,
    select_models,
    execute_tier1,
    decide_escalation,
    execute_tier2,
    evaluate_quality,
    recover_quality,
    compute_costs,
    finalize,
)


def build_router_graph() -> StateGraph:
    """Build the LangGraph StateGraph for the cascading LLM router."""
    graph = StateGraph(RouterState)

    graph.add_node("classify_task", classify_task)
    graph.add_node("select_models", select_models)
    graph.add_node("execute_tier1", execute_tier1)
    graph.add_node("decide_escalation", decide_escalation)
    graph.add_node("execute_tier2", execute_tier2)
    graph.add_node("evaluate_quality", evaluate_quality)
    graph.add_node("recover_quality", recover_quality)
    graph.add_node("compute_costs", compute_costs)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "classify_task")
    graph.add_edge("classify_task", "select_models")
    graph.add_edge("select_models", "execute_tier1")
    graph.add_edge("execute_tier1", "decide_escalation")

    graph.add_conditional_edges(
        "decide_escalation",
        route_after_decision,
        {"escalate": "execute_tier2", "direct": "evaluate_quality"},
    )

    graph.add_edge("execute_tier2", "evaluate_quality")
    graph.add_edge("evaluate_quality", "recover_quality")
    graph.add_edge("recover_quality", "compute_costs")
    graph.add_edge("compute_costs", "finalize")
    graph.add_edge("finalize", END)

    return graph
