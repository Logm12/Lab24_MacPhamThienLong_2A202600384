"""Module 3: Reranking — Cross-encoder top-20 → top-3 + latency benchmark."""

import os, sys, time
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RERANK_TOP_K


@dataclass
class RerankResult:
    text: str
    original_score: float
    rerank_score: float
    metadata: dict
    rank: int


class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder
            try:
                self._model = CrossEncoder(self.model_name)
            except Exception as e:
                print(f"Error loading {self.model_name}: {e}. Falling back to a smaller model.")
                self._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        return self._model

    def rerank(self, query: str, documents: list[dict], top_k: int = RERANK_TOP_K) -> list[RerankResult]:
        """Rerank documents: top-20 → top-k."""
        if not documents:
            return []
            
        model = self._load_model()
        pairs = [(query, doc["text"]) for doc in documents]
        scores = model.predict(pairs)
        
        # Combine and sort
        combined = []
        for i, (doc, score) in enumerate(zip(documents, scores)):
            combined.append({
                "doc": doc,
                "score": float(score)
            })
            
        combined.sort(key=lambda x: x["score"], reverse=True)
        
        results = []
        for i, item in enumerate(combined[:top_k]):
            doc = item["doc"]
            results.append(RerankResult(
                text=doc["text"],
                original_score=doc["score"],
                rerank_score=item["score"],
                metadata=doc["metadata"],
                rank=i + 1
            ))
        return results


def benchmark_reranker(reranker, query: str, documents: list[dict], n_runs: int = 5) -> dict:
    """Benchmark latency over n_runs."""
    import numpy as np
    times = []
    # Warmup
    reranker.rerank(query, documents)
    
    for _ in range(n_runs):
        start = time.perf_counter()
        reranker.rerank(query, documents)
        times.append((time.perf_counter() - start) * 1000)  # ms
        
    return {
        "avg_ms": float(np.mean(times)), 
        "min_ms": float(np.min(times)), 
        "max_ms": float(np.max(times))
    }


if __name__ == "__main__":
    query = "Nhân viên được nghỉ phép bao nhiêu ngày?"
    docs = [
        {"text": "Nhân viên được nghỉ 12 ngày/năm.", "score": 0.8, "metadata": {}},
        {"text": "Mật khẩu thay đổi mỗi 90 ngày.", "score": 0.7, "metadata": {}},
        {"text": "Thời gian thử việc là 60 ngày.", "score": 0.75, "metadata": {}},
    ]
    reranker = CrossEncoderReranker()
    for r in reranker.rerank(query, docs):
        print(f"[{r.rank}] {r.rerank_score:.4f} | {r.text}")
