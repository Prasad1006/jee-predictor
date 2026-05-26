"""Ingest counselling markdown/PDF text into ChromaDB."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / "datasets" / "counselling-rules"
CHROMA_DIR = ROOT / "datasets" / "embeddings"
COLLECTION = "josaa_counselling"


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 80) -> list[str]:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}".strip() if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) <= chunk_size:
                current = para
            else:
                words = para.split()
                buf: list[str] = []
                for word in words:
                    if sum(len(w) + 1 for w in buf) + len(word) < chunk_size:
                        buf.append(word)
                    else:
                        chunks.append(" ".join(buf))
                        buf = [word]
                current = " ".join(buf)
    if current:
        chunks.append(current)

    # sliding overlap for long single paragraphs already split
    if overlap and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            overlapped.append(f"{prev_tail} {chunks[i]}")
        return overlapped
    return chunks


def load_documents(rules_dir: Path | None = None) -> list[dict]:
    rules_dir = rules_dir or RULES_DIR
    documents: list[dict] = []
    for path in sorted(rules_dir.glob("**/*")):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for idx, chunk in enumerate(chunk_text(text)):
            documents.append(
                {
                    "id": f"{path.stem}_{idx}",
                    "text": chunk,
                    "metadata": {"source": path.name, "doc_type": "counselling_rules"},
                }
            )
    return documents


def ingest_chroma(persist_dir: Path | None = None) -> int:
    import chromadb

    persist_dir = persist_dir or CHROMA_DIR
    persist_dir.mkdir(parents=True, exist_ok=True)
    docs = load_documents()
    if not docs:
        return 0

    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"description": "JoSAA counselling knowledge"},
    )

    collection.upsert(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[d["metadata"] for d in docs],
    )
    return len(docs)
