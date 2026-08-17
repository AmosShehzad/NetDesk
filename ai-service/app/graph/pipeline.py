from langgraph.graph import StateGraph, END
from .state import ComplaintState
from .nodes import clean_text, classify_category, detect_priority, detect_sentiment, generate_reply

graph = StateGraph(ComplaintState)

graph.add_node("clean", clean_text)
graph.add_node("classify", classify_category)
graph.add_node("priority", detect_priority)
graph.add_node("sentiment", detect_sentiment)
graph.add_node("reply", generate_reply)

graph.set_entry_point("clean")
graph.add_edge("clean", "classify")
graph.add_edge("classify", "priority")
graph.add_edge("priority", "sentiment")
graph.add_edge("sentiment", "reply")
graph.add_edge("reply", END)

complaint_pipeline = graph.compile()