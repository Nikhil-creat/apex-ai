"""Semantic-ish chunking, embeddings into Qdrant, and entity links into Neo4j."""
import os, re, uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding
from neo4j import GraphDatabase

emb = TextEmbedding("BAAI/bge-small-en-v1.5")
qd = QdrantClient(url=os.getenv("QDRANT_URL"))
neo = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")))

def chunk(text, size=800):
    out, cur = [], ""
    for para in re.split(r"\n\s*\n", text):
        if len(cur) + len(para) > size and cur: out.append(cur.strip()); cur = ""
        cur += para + "\n\n"
    return out + ([cur.strip()] if cur.strip() else [])

def ingest_text(text, source="upload"):
    if not qd.collection_exists("docs"):
        qd.create_collection("docs", vectors_config=VectorParams(size=384, distance=Distance.COSINE))
    parts = chunk(text)
    vecs = list(emb.embed(parts))
    qd.upsert("docs", [PointStruct(id=str(uuid.uuid4()), vector=v.tolist(), payload={"text": p, "source": source}) for p, v in zip(parts, vecs)])
    with neo.session() as s:   # naive entity linking: capitalized phrases co-occurring in a chunk
        for p in parts:
            ents = list(dict.fromkeys(re.findall(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)*\b", p)))[:8]
            for a, b in zip(ents, ents[1:]):
                s.run("MERGE (x:Entity {name:$a}) MERGE (y:Entity {name:$b}) MERGE (x)-[:RELATED_TO]->(y)", a=a, b=b)
    return len(parts)

if __name__ == "__main__":
    import sys; print(ingest_text(open(sys.argv[1]).read(), sys.argv[1]))
