from fastapi import APIRouter
from app.graph.pipeline import complaint_pipeline
from app.schemas.complaint import (
    ComplaintInput, ClassificationOutput, PriorityOutput,
    SentimentOutput, SummaryOutput, SuggestedReplyOutput, FullAnalysisOutput
)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/classify", response_model=ClassificationOutput)
async def classify_complaint(data: ComplaintInput):
    # Stub for now — Day 11 replaces this with a real LangGraph call
    return ClassificationOutput(category="Network Outage")


@router.post("/priority", response_model=PriorityOutput)
async def detect_priority(data: ComplaintInput):
    return PriorityOutput(priority="HIGH")


@router.post("/sentiment", response_model=SentimentOutput)
async def analyze_sentiment(data: ComplaintInput):
    return SentimentOutput(sentiment="Negative")


@router.post("/summary", response_model=SummaryOutput)
async def summarize_ticket(data: ComplaintInput):
    return SummaryOutput(summary="Customer reports internet outage since morning.")


@router.post("/suggested-reply", response_model=SuggestedReplyOutput)
async def suggest_reply(data: ComplaintInput):
    return SuggestedReplyOutput(reply="We're sorry for the inconvenience. Our team is investigating.")


@router.post("/analyze", response_model=FullAnalysisOutput)
async def full_analysis(data: ComplaintInput):
    result = complaint_pipeline.invoke({"text": data.text})
    return FullAnalysisOutput(
        category=result["category"],
        priority=result["priority"],
        sentiment=result["sentiment"],
        suggested_reply=result["suggested_reply"]
    )