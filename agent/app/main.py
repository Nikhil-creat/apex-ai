"""FastAPI entrypoint: /chat streams Server-Sent Events, /ingest adds documents."""
import json, asyncio
from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .agent import graph
from .memory import remember_turn, history
from .telemetry import run_span

app = FastAPI(title="APEX-AI agent")
class ChatIn(BaseModel):
    query: str
    session: str = "default"

def sse(type_, data): return f"data: {json.dumps({'type': type_, 'data': data})}\n\n"

@app.get("/health")
def health(): return {"ok": True}

@app.post("/chat")
async def chat(req: ChatIn):
    async def stream():
        yield sse("tool", "triage")
        with run_span("agent_run", session=req.session):
            state = await asyncio.to_thread(graph.invoke, {
                "query": req.query, "image": None, "intent": "", "context": "",
                "answer": "", "errors": [], "attempts": 0, "blocked": False})
        if state["blocked"]:
            yield sse("token", "Request blocked by the safety filter."); return
        if state["intent"] == "rag": yield sse("tool", "hybrid-rag")
        if state["intent"] == "tool": yield sse("tool", "mcp")
        remember_turn(req.session, "user", req.query)
        for word in state["answer"].split(" "):
            yield sse("token", word + " "); await asyncio.sleep(0.01)
        remember_turn(req.session, "assistant", state["answer"])
    return StreamingResponse(stream(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})

@app.post("/ingest")
async def ingest(file: UploadFile):
    from scripts.ingest import ingest_text
    return {"chunks": ingest_text((await file.read()).decode("utf-8", "ignore"), file.filename)}

from .voice import router as voice_router
app.include_router(voice_router, prefix="/voice")
