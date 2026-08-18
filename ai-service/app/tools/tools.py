"""
Tools the AI agent can invoke during its reasoning.

Why: These give the agent real capabilities beyond text generation.
Instead of guessing, it can look up actual data before responding.
Each tool takes simple inputs and returns structured results.
"""

import httpx
import logging
from app.knowledge_base.retriever import search as kb_search

logger = logging.getLogger(__name__)

# Backend URL — the AI service calls back to Django for live data
BACKEND_URL = "http://127.0.0.1:8000/api"


def search_knowledge_base(query: str) -> str:
    """
    Search the troubleshooting knowledge base for relevant guides.
    Why: Grounds the AI's reply in real documentation instead of hallucinating.
    """
    results = kb_search(query, top_k=3)

    if not results:
        return "No relevant knowledge base articles found."

    output = "Knowledge base results:\n\n"
    for i, r in enumerate(results, 1):
        output += f"[{i}] (from {r['source']}):\n{r['text']}\n\n"
    return output


def check_outage_status(area: str = "all") -> str:
    """
    Check if there are any known network outages.
    Why: If there's a known outage, the AI can immediately tell the customer
    instead of walking them through useless troubleshooting steps.
    """
    try:
        response = httpx.get(f"{BACKEND_URL}/outages/", timeout=5.0)
        if response.status_code == 200:
            outages = response.json()
            if not outages.get("results", []):
                return "No active outages reported in any area."
            lines = []
            for o in outages["results"]:
                lines.append(f"- {o['area']}: {o['description']} (since {o['started_at']})")
            return "Active outages:\n" + "\n".join(lines)
    except Exception:
        pass

    return "No active outages reported. (Note: Live outage data will be available after Day 3 backend update.)"


def lookup_billing_status(customer_id: str = "") -> str:
    """
    Check a customer's recent billing status.
    Why: If the complaint is about billing, the AI can reference actual data
    instead of giving generic advice.
    """
    if customer_id:
        try:
            response = httpx.get(
                f"{BACKEND_URL}/billing/",
                params={"customer": customer_id},
                timeout=5.0
            )
            if response.status_code == 200:
                bills = response.json().get("results", [])
                if not bills:
                    return "No billing records found for this customer."
                latest = bills[0]
                return (
                    f"Latest bill: Rs. {latest['amount']} | "
                    f"Status: {latest['status']} | "
                    f"Due: {latest['due_date']}"
                )
        except Exception:
            pass

    return "Billing details: Customer can check their latest bill in the portal under 'My Bills'. For specific billing queries, a support agent can pull up the full history."


def recommend_escalation(reason: str, priority: str = "HIGH") -> str:
    """
    Signal that this ticket should be escalated to a human agent.
    Why: The agent recognizes it can't solve everything — knowing when to
    hand off is as important as knowing how to help.
    """
    return (
        f"ESCALATE: {reason} | Recommended priority: {priority}. "
        f"This issue requires human agent intervention."
    )