"""
Agent nodes — each function is one step in the agent's reasoning.

Why: Breaking the agent into discrete steps lets LangGraph route
between them conditionally. The agent doesn't just classify-and-reply
anymore — it investigates, gathers context, and makes decisions.
"""

import os
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from .state import AgentState
from app.tools.tools import (
    search_knowledge_base,
    check_outage_status,
    lookup_billing_status,
    recommend_escalation,
)

load_dotenv()
logger = logging.getLogger(__name__)

llm = ChatGroq(model="openai/gpt-oss-20b", api_key=os.getenv("GROQ_API_KEY"))


# ── Node 1: Clean and prep ──────────────────────────────────────

def clean_text(state: AgentState) -> dict:
    """Strip whitespace and normalize. Why: Garbage in = garbage out."""
    return {
        "cleaned_text": state["text"].strip(),
        "actions_taken": "Cleaned input text",
    }


# ── Node 2: Classify intent ─────────────────────────────────────

def classify_intent(state: AgentState) -> dict:
    """
    Determine what the customer needs.
    Why: Different categories trigger different tools and response strategies.
    """
    prompt = (
        "You are an ISP support classifier. Read this customer message and reply with "
        "ONLY one of these exact words: NetworkOutage, Billing, SlowSpeed, Installation, Other.\n\n"
        f"Customer message: {state['cleaned_text']}"
    )
    result = llm.invoke(prompt).content.strip()

    valid = {"NetworkOutage", "Billing", "SlowSpeed", "Installation", "Other"}
    category = result if result in valid else "Other"

    logger.info(f"Classified as: {category}")
    return {
        "category": category,
        "actions_taken": f"{state.get('actions_taken', '')} → Classified: {category}",
    }


# ── Node 3: Detect priority and sentiment ───────────────────────

def analyze_urgency(state: AgentState) -> dict:
    """
    Detect priority AND sentiment in one LLM call.
    Why: Two separate calls was wasteful. One call, two outputs, half the latency.
    """
    prompt = (
        "Analyze this ISP customer complaint. Reply with EXACTLY two lines:\n"
        "Priority: LOW or MEDIUM or HIGH or CRITICAL\n"
        "Sentiment: Positive or Neutral or Negative or Angry\n\n"
        f"Complaint: {state['cleaned_text']}"
    )
    result = llm.invoke(prompt).content.strip()

    priority = "MEDIUM"
    sentiment = "Neutral"
    for line in result.split("\n"):
        line = line.strip()
        if line.upper().startswith("PRIORITY:"):
            val = line.split(":", 1)[1].strip().upper()
            if val in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
                priority = val
        elif line.upper().startswith("SENTIMENT:"):
            val = line.split(":", 1)[1].strip().capitalize()
            if val in {"Positive", "Neutral", "Negative", "Angry"}:
                sentiment = val

    return {
        "priority": priority,
        "sentiment": sentiment,
        "actions_taken": f"{state.get('actions_taken', '')} → Priority: {priority}, Sentiment: {sentiment}",
    }


# ── Node 4: Gather context (tools) ──────────────────────────────

def gather_context_network(state: AgentState) -> dict:
    """
    For network issues: check outages FIRST, then search KB.
    Why: If there's a known outage, troubleshooting is pointless — just inform the customer.
    """
    outage_info = check_outage_status()
    kb_results = search_knowledge_base(state["cleaned_text"])

    return {
        "tool_results": outage_info,
        "kb_context": kb_results,
        "actions_taken": f"{state.get('actions_taken', '')} → Checked outages, searched KB",
    }


def gather_context_billing(state: AgentState) -> dict:
    """
    For billing issues: look up billing status, then search billing FAQ.
    Why: Customer wants specific answers about their bill, not generic advice.
    """
    customer_id = state.get("customer_id", "")
    billing_info = lookup_billing_status(customer_id)
    kb_results = search_knowledge_base(f"billing payment {state['cleaned_text']}")

    return {
        "tool_results": billing_info,
        "kb_context": kb_results,
        "actions_taken": f"{state.get('actions_taken', '')} → Checked billing, searched FAQ",
    }


def gather_context_general(state: AgentState) -> dict:
    """
    For installation/other: just search the knowledge base.
    Why: These categories don't need real-time data checks.
    """
    kb_results = search_knowledge_base(state["cleaned_text"])

    return {
        "tool_results": "",
        "kb_context": kb_results,
        "actions_taken": f"{state.get('actions_taken', '')} → Searched KB",
    }


# ── Node 5: Evaluate confidence ─────────────────────────────────

def evaluate_confidence(state: AgentState) -> dict:
    """
    Decide if the agent has enough context to help, or should escalate.
    Why: An agent that doesn't know its limits is worse than no agent.
    """
    has_kb = bool(state.get("kb_context")) and "No relevant" not in state.get("kb_context", "")
    is_angry_critical = state.get("sentiment") == "Angry" and state.get("priority") == "CRITICAL"

    if is_angry_critical:
        return {
            "confidence": 0.2,
            "should_escalate": True,
            "escalation_reason": "Customer is angry with a critical issue — human empathy needed.",
            "actions_taken": f"{state.get('actions_taken', '')} → Auto-escalate (angry + critical)",
        }

    if has_kb:
        return {
            "confidence": 0.8,
            "should_escalate": False,
            "escalation_reason": "",
            "actions_taken": f"{state.get('actions_taken', '')} → Confident (KB match found)",
        }

    return {
        "confidence": 0.5,
        "should_escalate": False,
        "escalation_reason": "",
        "actions_taken": f"{state.get('actions_taken', '')} → Moderate confidence (no KB match)",
    }


# ── Node 6a: Generate reply ─────────────────────────────────────

def generate_reply(state: AgentState) -> dict:
    """
    Generate a helpful reply using all gathered context.
    Why: The reply is grounded in KB articles and tool results,
    not just the LLM's training data.
    """
    context_parts = []
    if state.get("kb_context"):
        context_parts.append(f"Relevant documentation:\n{state['kb_context']}")
    if state.get("tool_results"):
        context_parts.append(f"System data:\n{state['tool_results']}")

    context = "\n\n".join(context_parts) if context_parts else "No additional context available."

    prompt = (
        "You are a helpful ISP customer support AI assistant. "
        "Use the provided context to give an accurate, specific reply. "
        "Be concise (2-4 sentences), professional, and empathetic. "
        "If the context contains step-by-step instructions, include the most relevant steps. "
        "Do NOT make up information not in the context.\n\n"
        f"Context:\n{context}\n\n"
        f"Customer complaint ({state.get('category', 'Other')} | "
        f"Priority: {state.get('priority', 'MEDIUM')} | "
        f"Sentiment: {state.get('sentiment', 'Neutral')}):\n"
        f"{state['cleaned_text']}\n\n"
        "Your reply:"
    )

    reply = llm.invoke(prompt).content.strip()
    return {
        "suggested_reply": reply,
        "actions_taken": f"{state.get('actions_taken', '')} → Generated context-aware reply",
    }


# ── Node 6b: Escalate ───────────────────────────────────────────

def escalate_to_human(state: AgentState) -> dict:
    """
    Hand off to a human agent with a summary of what the AI tried.
    Why: The human agent gets a briefing instead of starting from scratch.
    """
    reason = state.get("escalation_reason", "AI confidence too low to resolve.")
    escalation = recommend_escalation(reason, state.get("priority", "HIGH"))

    summary_prompt = (
        "Summarize this customer interaction in 2 sentences for a human support agent. "
        "Include what the customer wants and what was already checked.\n\n"
        f"Customer message: {state['cleaned_text']}\n"
        f"Category: {state.get('category', 'Other')}\n"
        f"Priority: {state.get('priority', 'MEDIUM')}\n"
        f"Actions taken: {state.get('actions_taken', 'None')}\n"
        f"Tool results: {state.get('tool_results', 'None')}\n"
    )
    summary = llm.invoke(summary_prompt).content.strip()

    reply = (
        "I understand your concern, and I want to make sure you get the best help possible. "
        "I'm connecting you with a support specialist who can assist you further. "
        "They'll have the full context of your issue."
    )

    return {
        "suggested_reply": reply,
        "escalation_reason": f"{reason}\n\nAgent summary: {summary}",
        "should_escalate": True,
        "actions_taken": f"{state.get('actions_taken', '')} → Escalated to human",
    }