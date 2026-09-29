from pathlib import Path
import json, pickle
import numpy as np
from app.rag.documents import load_documents, DocumentChunk
from app.rag.embeddings import TfidfEmbedder
from app.utils.errors import RAGError

class LocalVectorStore:
    def __init__(self, kb_dir: Path, store_dir: Path):
        self.kb_dir, self.store_dir = kb_dir, store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.embedder = TfidfEmbedder()
        self.documents: list[DocumentChunk] = []
        self.vectors: np.ndarray | None = None

    @property
    def ready(self) -> bool:
        return bool(self.documents) and self.vectors is not None

    def build(self) -> None:
        self.documents = load_documents(self.kb_dir)
        if not self.documents:
            raise RAGError("Knowledge base is empty.")
        self.embedder.fit([d.text for d in self.documents])
        self.vectors = self.embedder.encode([d.text for d in self.documents])
        with open(self.store_dir / "store.pkl", "wb") as f:
            pickle.dump((self.documents, self.embedder.vectorizer, self.vectors), f)

    def load(self) -> None:
        p = self.store_dir / "store.pkl"
        if not p.exists():
            self.build(); return
        with open(p, "rb") as f:
            self.documents, vectorizer, self.vectors = pickle.load(f)
        self.embedder.vectorizer = vectorizer
        self.embedder.fitted = True

    def search(self, query: str, top_k: int = 3, threshold: float = 0.12) -> list[dict]:
        if not self.ready:
            raise RAGError("Knowledge base is not ready.")
        q = self.embedder.encode([query])[0]
        norms = np.linalg.norm(self.vectors, axis=1) * np.linalg.norm(q)
        scores = np.divide(self.vectors @ q, norms, out=np.zeros_like(norms), where=norms != 0)
        # Small source hint improves precision for explicit policy questions.
        lowered = query.lower()
        hints = {
            "refund": "refund_policy.md",
            "cancel": "cancellation_policy.md",
            "cancellation": "cancellation_policy.md",
            "delivery": "delivery_policy.md",
            "operating": "operating_policy.md",
            "hours": "operating_policy.md",
        }
        hinted_source = next((source for word, source in hints.items() if word in lowered), None)
        if hinted_source:
            for i, doc in enumerate(self.documents):
                if doc.source == hinted_source:
                    scores[i] += 0.25
        indices = np.argsort(scores)[::-1]
        results = []
        for idx in indices[:top_k]:
            score = float(scores[idx])
            if score < threshold:
                continue
            d = self.documents[idx]
            results.append({"text": d.text, "source": d.source, "version": d.version, "score": round(score, 4)})
        return results
