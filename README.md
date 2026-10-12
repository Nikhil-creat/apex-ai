# APEX-AI

Agentic hybrid multimodal assistant: Groq + LangGraph + MCP, GraphRAG (Qdrant + Neo4j), a custom PyTorch/ONNX CNN, local SLM triage, and six Docker services.

## Website (GitHub Pages)
1. Push this repo to GitHub (branch `main`).
2. Settings, Pages, Source: **GitHub Actions**.
3. The workflow in `.github/workflows/pages.yml` publishes `site/`.

## Run the stack
```
cp .env.example .env     # set GROQ_API_KEY and NEO4J_PASSWORD
docker compose up --build
```
## Ingest documents
`docker compose exec apex-agent python -m scripts.ingest notes.txt` (or POST a file to `/api/ingest`).

## Train the CNN
Put images in `vision/data/<label>/` and run `python -m app.train` inside `apex-vision`. The image ships with untrained placeholder weights.

## Status
Included but untested end to end: Dockerfiles, `/chat` SSE route, voice routes (`/voice/stt`, `/voice/tts`), MCP tools (send `/tool sqlite list_tables` in chat), memory, telemetry, ingestion, CI. Still to do: train the CNN, run Ollama (`ollama pull qwen2.5:0.5b`), and stream tokens straight from Groq.

---
Designed and developed by **NIKHIL CHARY SRIRAMOJU** · [GitHub](https://github.com/Nikhil-creat) · [LinkedIn](https://in.linkedin.com/in/nikhil-chary-sriramoju-95041b38a)

**Keywords:** agentic-ai, langgraph, groq, mcp, graphrag, rag, qdrant, neo4j, pytorch, onnx, fastapi, nextjs, docker, multimodal, prompt-injection
