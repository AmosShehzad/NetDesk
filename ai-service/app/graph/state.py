"""
Agent state — everything the graph carries between nodes.

Why: LangGraph passes this dict from node to node. Each node reads
what it needs and writes its results. This is the agent's "working memory"
for a single request.
"""

from typing import TypedDict, Optional


class AgentState(TypedDict):
    # Input
    text: str                          # raw customer message
    customer_id: Optional[str]         # for billing/history lookups

    # Analysis
    cleaned_text: str                  # preprocessed text
    category: str                      # NetworkOutage, Billing, SlowSpeed, Installation, Other
    priority: str                      # LOW, MEDIUM, HIGH, CRITICAL
    sentiment: str                     # Positive, Neutral, Negative, Angry

    # Agent reasoning
    kb_context: str                    # knowledge base search results
    tool_results: str                  # results from tools (outage check, billing, etc.)
    confidence: float                  # 0.0-1.0 how confident the agent is in its reply
    should_escalate: bool              # agent's decision to hand off to human

    # Output
    suggested_reply: str               # final reply for the customer
    escalation_reason: str             # why it escalated (if it did)
    actions_taken: str                 # log of what the agent did (for transparency)