from agent.state import RouterState


def route_after_decision(state: RouterState) -> str:
    """Conditional edge after decide_escalation node."""
    if state.get("status") == "escalated":
        return "escalate"
    return "direct"
