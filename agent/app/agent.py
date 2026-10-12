"""LangGraph agent: triage -> plan -> tools -> answer, with self-healing and fallback."""
import os, re, time
from typing import TypedDict, Optional
from groq import Groq, RateLimitError
from langgraph.graph import StateGraph, END
from .rag import hybrid_search
from .triage import classify

client = Groq(api_key=os.environ["GROQ_API_KEY"])
PRIMARY, FALLBACK = os.getenv("GROQ_MODEL"), os.getenv("GROQ_FALLBACK_MODEL")
INJECTION = re.compile(r"(ignore (all|your|previous)|system prompt|developer mode|reveal.*instructions)", re.I)

class S(TypedDict):
    query: str; image: Optional[bytes]; intent: str; context: str
    answer: str; errors: list; attempts: int; blocked: bool

def llm(messages, model=PRIMARY):
    try:
        return client.chat.completions.create(model=model, messages=messages).choices[0].message.content
    except RateLimitError:
        if model != FALLBACK:
            return llm(messages, FALLBACK)          # fallback node behavior
        time.sleep(2); return llm(messages, FALLBACK)

def triage(s: S):
    """Local-first guard. Replace the regex with a local SLM + Llama-Guard call."""
    if classify(s["query"]) == "blocked": return {"blocked": True, "intent": "blocked"}
    intent = "vision" if s.get("image") else "rag" if "?" in s["query"] else "chat"
    return {"intent": intent, "blocked": False}

def retrieve(s: S):
    return {"context": hybrid_search(s["query"])}

def classify_image(s: S):
    import httpx
    r = httpx.post(os.getenv("VISION_URL") + "/classify", files={"file": s["image"]}).json()
    if r["escalate"]:   # deep track: send to a Groq vision-capable model
        return {"context": "CNN unsure; use cloud vision."}
    return {"context": f"CNN label={r['label']} conf={r['confidence']:.2f}"}

def answer(s: S):
    try:
        out = llm([{"role": "system", "content": "Answer using the context. Cite sources."},
                   {"role": "user", "content": f"Context:\n{s.get('context','')}\n\nQ: {s['query']}"}])
        return {"answer": out}
    except Exception as e:                           # self-healing loop
        return {"errors": s["errors"] + [repr(e)], "attempts": s["attempts"] + 1}

route = lambda s: END if s["blocked"] else {"rag": "retrieve", "vision": "classify_image"}.get(s["intent"], "answer")
retry = lambda s: "answer" if s["errors"] and s["attempts"] < 3 and not s.get("answer") else END

g = StateGraph(S)
for n, f in [("triage", triage), ("retrieve", retrieve), ("classify_image", classify_image), ("answer", answer)]:
    g.add_node(n, f)
g.set_entry_point("triage")
g.add_conditional_edges("triage", route)
g.add_edge("retrieve", "answer"); g.add_edge("classify_image", "answer")
g.add_conditional_edges("answer", retry)
graph = g.compile()
