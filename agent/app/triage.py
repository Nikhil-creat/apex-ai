"""Local SLM triage via Ollama (Qwen2.5-0.5B). Falls back to regex rules if Ollama is down."""
import os, re, httpx
RULES = re.compile(r"(ignore (all|your|previous)|system prompt|developer mode|reveal.*instructions)", re.I)

def classify(query: str) -> str:
    if RULES.search(query): return "blocked"
    try:
        r = httpx.post(os.getenv("OLLAMA_URL", "") + "/api/generate", timeout=3, json={
            "model": "qwen2.5:0.5b", "stream": False,
            "prompt": f"Reply with one word: safe, unsafe, or injection.\nText: {query}"})
        if any(w in r.json()["response"].lower() for w in ("unsafe", "injection")): return "blocked"
    except Exception:
        pass
    return "ok"
