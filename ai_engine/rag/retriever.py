"""Retrieve counselling knowledge chunks (ChromaDB + keyword fallback)."""
from __future__ import annotations

import re
from pathlib import Path

from ai_engine.rag.ingest import COLLECTION, CHROMA_DIR, load_documents

ROOT = Path(__file__).resolve().parents[2]


class KnowledgeRetriever:
    def __init__(self, persist_dir: Path | None = None):
        self.persist_dir = persist_dir or CHROMA_DIR
        self._collection = None
        self._fallback_docs = load_documents()

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        try:
            import chromadb

            client = chromadb.PersistentClient(path=str(self.persist_dir))
            self._collection = client.get_or_create_collection(name=COLLECTION)
            if self._collection.count() == 0:
                from ai_engine.rag.ingest import ingest_chroma

                ingest_chroma(self.persist_dir)
            return self._collection
        except Exception:
            return None

    def retrieve(self, query: str, top_k: int = 4) -> list[dict]:
        collection = self._get_collection()
        if collection is not None:
            try:
                result = collection.query(query_texts=[query], n_results=top_k)
                docs = result.get("documents", [[]])[0]
                metas = result.get("metadatas", [[]])[0]
                return [
                    {"text": doc, "source": meta.get("source", "unknown")}
                    for doc, meta in zip(docs, metas)
                ]
            except Exception:
                pass
        return self._keyword_fallback(query, top_k)

    def _keyword_fallback(self, query: str, top_k: int) -> list[dict]:
        tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
        scored: list[tuple[int, dict]] = []
        for doc in self._fallback_docs:
            text_lower = doc["text"].lower()
            score = sum(1 for t in tokens if t in text_lower)
            if score:
                scored.append(
                    (
                        score,
                        {"text": doc["text"], "source": doc["metadata"].get("source", "")},
                    )
                )
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]
