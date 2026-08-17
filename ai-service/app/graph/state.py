from typing import TypedDict


class ComplaintState(TypedDict):
    text: str
    cleaned_text: str
    category: str
    priority: str
    sentiment: str
    suggested_reply: str