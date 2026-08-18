"""
AI Service API routes.

Why: The /analyze endpoint is the main entry point that Django calls.
It returns rich data (confidence, escalation, actions) so the backend
can make better decisions about each ticket.
"""

import logging
from fastapi import APIRouter
from app.graph.pipeline import agent_pipeline
from app.schemas.complaint import (
    ComplaintInput, ClassificationOutput, PriorityOutput,
    SentimentOutput, SuggestedReplyOutput, FullAnalysisOutput
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI"])


def _empty_state(text: str, customer_id: str = "") -> dict:
    """Build a fresh state dict for a pipeline call."""
    return {
        "text": text,
        "customer_id": customer_id,
        "cleaned_text": "",
        "category": "",
        "priority": "MEDIUM",
        "sentiment": "Neutral",
        "kb_context": "",
        "tool_results": "",
        "confidence": 0.0,
        "should_escalate": False,
        "suggested_reply": "",
        "escalation_reason": "",
        "actions_taken": "",
    }


@router.post("/analyze", response_model=FullAnalysisOutput)
async def full_analysis(data: ComplaintInput):
    """Run the full agentic pipeline: classify → route → gather context → decide → reply."""
    logger.info(f"Analyzing complaint: {data.text[:100]}...")

    result = agent_pipeline.invoke(_empty_state(data.text, data.customer_id or ""))

    logger.info(
        f"Result: category={result['category']}, priority={result['priority']}, "
        f"confidence={result.get('confidence', 0)}, escalate={result.get('should_escalate', False)}"
    )

    return FullAnalysisOutput(
        category=result["category"],
        priority=result["priority"],
        sentiment=result["sentiment"],
        suggested_reply=result["suggested_reply"],
        confidence=result.get("confidence", 0.5),
        should_escalate=result.get("should_escalate", False),
        escalation_reason=result.get("escalation_reason"),
        actions_taken=result.get("actions_taken"),
    )


@router.post("/classify", response_model=ClassificationOutput)
async def classify_complaint(data: ComplaintInput):
    result = agent_pipeline.invoke(_empty_state(data.text))
    return ClassificationOutput(category=result["category"])


@router.post("/priority", response_model=PriorityOutput)
async def detect_priority(data: ComplaintInput):
    result = agent_pipeline.invoke(_empty_state(data.text))
    return PriorityOutput(priority=result["priority"])


@router.post("/sentiment", response_model=SentimentOutput)
async def analyze_sentiment(data: ComplaintInput):
    result = agent_pipeline.invoke(_empty_state(data.text))
    return SentimentOutput(sentiment=result["sentiment"])


@router.post("/suggested-reply", response_model=SuggestedReplyOutput)
async def suggest_reply(data: ComplaintInput):
    result = agent_pipeline.invoke(_empty_state(data.text))
    return SuggestedReplyOutput(reply=result["suggested_reply"])