from pydantic import BaseModel


class ComplaintInput(BaseModel):
    text: str


class ClassificationOutput(BaseModel):
    category: str


class PriorityOutput(BaseModel):
    priority: str


class SentimentOutput(BaseModel):
    sentiment: str


class SummaryOutput(BaseModel):
    summary: str


class SuggestedReplyOutput(BaseModel):
    reply: str


class FullAnalysisOutput(BaseModel):
    category: str
    priority: str
    sentiment: str
    suggested_reply: str