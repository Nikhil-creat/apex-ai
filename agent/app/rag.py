"""Hybrid RAG: Qdrant dense retrieval + Neo4j graph context, reranked with FlashRank."""
import os
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
from flashrank import Ranker, RerankRequest

emb = TextEmbedding("BAAI/bge-small-en-v1.5")
qd = QdrantClient(url=os.getenv("QDRANT_URL"))
neo = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")))
ranker = Ranker()

def graph_context(entities: list[str], limit=10) -> list[str]:
    q = "MATCH (a)-[r]->(b) WHERE a.name IN $e RETURN a.name+' -'+type(r)+'-> '+b.name AS t LIMIT $n"
    with neo.session() as s:
        return [r["t"] for r in s.run(q, e=entities, n=limit)]

def hybrid_search(query: str, k=20, keep=5, max_chars=6000) -> str:
    vec = list(emb.embed([query]))[0].tolist()
    hits = qd.search("docs", query_vector=vec, limit=k)
    passages = [{"id": h.id, "text": h.payload["text"]} for h in hits]
    top = ranker.rerank(RerankRequest(query=query, passages=passages))[:keep]
    facts = graph_context([w for w in query.split() if w.istitle()])
    ctx = "\n".join(p["text"] for p in top) + "\n\nGraph facts:\n" + "\n".join(facts)
    return ctx[:max_chars]          # dynamic trimming for the context window
