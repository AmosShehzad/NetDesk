"""
LangGraph pipeline with conditional routing.

Why: A straight pipeline (A→B→C→D) is not agentic. This graph BRANCHES:
- Different complaint types trigger different tools
- Low confidence triggers escalation instead of a bad reply
- The agent makes routing decisions, not just text generation
"""

from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    clean_text,
    classify_intent,
    analyze_urgency,
    gather_context_network,
    gather_context_billing,
    gather_context_general,
    evaluate_confidence,
    generate_reply,
    escalate_to_human,
)


def route_by_category(state: AgentState) -> str:
    """Route to the right tool-gathering node based on complaint category.
    Why: Billing complaints need billing tools, network issues need outage checks."""
    category = state.get("category", "Other")
    if category in ("NetworkOutage", "SlowSpeed"):
        return "gather_network"
    elif category == "Billing":
        return "gather_billing"
    else:
        return "gather_general"


def route_by_confidence(state: AgentState) -> str:
    """Route based on whether the agent can help or should hand off.
    Why: A wrong answer is worse than no answer — escalate when unsure."""
    if state.get("should_escalate", False):
        return "escalate"
    return "reply"


graph = StateGraph(AgentState)

graph.add_node("clean", clean_text)
graph.add_node("classify", classify_intent)
graph.add_node("urgency", analyze_urgency)
graph.add_node("gather_network", gather_context_network)
graph.add_node("gather_billing", gather_context_billing)
graph.add_node("gather_general", gather_context_general)
graph.add_node("confidence", evaluate_confidence)
graph.add_node("reply", generate_reply)
graph.add_node("escalate", escalate_to_human)

graph.set_entry_point("clean")
graph.add_edge("clean", "classify")
graph.add_edge("classify", "urgency")

graph.add_conditional_edges("urgency", route_by_category, {
    "gather_network": "gather_network",
    "gather_billing": "gather_billing",
    "gather_general": "gather_general",
})

graph.add_edge("gather_network", "confidence")
graph.add_edge("gather_billing", "confidence")
graph.add_edge("gather_general", "confidence")

graph.add_conditional_edges("confidence", route_by_confidence, {
    "reply": "reply",
    "escalate": "escalate",
})

graph.add_edge("reply", END)
graph.add_edge("escalate", END)

agent_pipeline = graph.compile()