"""
API request/response schemas.

Why: Pydantic models validate inputs and document outputs.
The new schemas expose the agent's reasoning (confidence, actions)
so the backend can make smarter decisions about the ticket.
"""

from pydantic import BaseModel
from typing import Optional


class ComplaintInput(BaseModel):
    text: str
    customer_id: Optional[str] = None


class FullAnalysisOutput(BaseModel):
    category: str
    priority: str
    sentiment: str
    suggested_reply: str
    confidence: float
    should_escalate: bool
    escalation_reason: Optional[str] = None
    actions_taken: Optional[str] = None


class ClassificationOutput(BaseModel):
    category: str

class PriorityOutput(BaseModel):
    priority: str

class SentimentOutput(BaseModel):
    sentiment: str

class SuggestedReplyOutput(BaseModel):
    reply: str