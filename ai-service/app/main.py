"""
FastAPI entry point.

Why: This is what uvicorn runs. We add logging config here
so every node's decisions show up in the console.
"""

import logging
from fastapi import FastAPI
from app.routers import ai

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s"
)

app = FastAPI(
    title="NetDesk AI Agent",
    version="2.0.0",
    description="Agentic AI service with RAG, tool use, and conditional routing"
)

app.include_router(ai.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "netdesk-ai-agent", "version": "2.0.0"}