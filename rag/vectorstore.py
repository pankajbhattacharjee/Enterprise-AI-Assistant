import json
from pathlib import Path
import numpy as np
from backend.config import get_settings


class LocalVectorStore:
    """Persisted hashed bag-of-words vectors; replaceable with FAISS in production."""
    dimensions = 512

    def __init__(self) -> None:
        self.path = get_settings().index_dir / "chunks.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _embed(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimensions, dtype=np.float32)
        for raw_token in text.lower().split():
            # Lightweight normalization improves retrieval without requiring a
            # model download (e.g. "refund" matches "refunds").
            token = raw_token.strip(".,;:!?()[]{}\"'").rstrip("s")
            if not token:
                continue
            vector[hash(token) % self.dimensions] += 1
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    def _load(self) -> list[dict]:
        return json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []

    def add(self, chunks: list[dict]) -> int:
        records = self._load()
        for chunk in chunks:
            chunk["vector"] = self._embed(chunk["text"]).tolist()
            records.append(chunk)
        self.path.write_text(json.dumps(records), encoding="utf-8")
        return len(chunks)

    def search(self, query: str, owner_id: int, limit: int = 4) -> list[dict]:
        query_vector = self._embed(query)
        scored = []
        for record in self._load():
            if record.get("owner_id") != owner_id:
                continue
            score = float(np.dot(query_vector, np.array(record["vector"], dtype=np.float32)))
            # Suppress zero-similarity chunks; this prevents irrelevant documents
            # becoming accidental sources when the user has no matching content.
            if score > 0:
                scored.append({**record, "score": round(score, 3)})
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]
