from fastapi import FastAPI
from app.routers import ai

app = FastAPI(title="NetDesk AI Service", version="1.0.0")

app.include_router(ai.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "netdesk-ai"}