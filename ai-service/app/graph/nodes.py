import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from .state import ComplaintState

load_dotenv()
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))


def clean_text(state: ComplaintState) -> ComplaintState:
    state["cleaned_text"] = state["text"].strip()
    return state


def classify_category(state: ComplaintState) -> ComplaintState:
    prompt = f"Reply with ONLY one word: NetworkOutage, Billing, SlowSpeed, Installation, or Other. Category of this ISP complaint: {state['cleaned_text']}"
    state["category"] = llm.invoke(prompt).content.strip()
    return state


def detect_priority(state: ComplaintState) -> ComplaintState:
    prompt = f"Reply with ONLY one of these exact words, nothing else: LOW, MEDIUM, HIGH, CRITICAL. Urgency of this ISP complaint: {state['cleaned_text']}"
    result = llm.invoke(prompt).content.strip().upper()
    state["priority"] = result if result in ["LOW", "MEDIUM", "HIGH", "CRITICAL"] else "MEDIUM"
    return state


def detect_sentiment(state: ComplaintState) -> ComplaintState:
    prompt = f"Reply with ONLY one word: Positive, Neutral, Negative, or Angry. Sentiment of this complaint: {state['cleaned_text']}"
    state["sentiment"] = llm.invoke(prompt).content.strip()
    return state


def generate_reply(state: ComplaintState) -> ComplaintState:
    prompt = f"Write a short, professional 2-sentence reply to this ISP customer complaint: {state['cleaned_text']}"
    state["suggested_reply"] = llm.invoke(prompt).content.strip()
    return state