"""
Phase C — Full Async E2E Pipeline
Architecture: User Query → L1 Guard → RAG Backend → L3 Guard → Final Response
Each stage has a precise latency counter. Target: guardrail overhead < 200ms P95.
"""

import sys
import os
import asyncio
import time

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import importlib.util
import types

def _import_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_phase_c_dir = os.path.join(PROJECT_ROOT, "phase-c")
_l1_mod = _import_from_path("l1_input_guard", os.path.join(_phase_c_dir, "l1_input_guard.py"))
_l3_mod = _import_from_path("l3_output_guard", os.path.join(_phase_c_dir, "l3_output_guard.py"))

L1InputGuard = _l1_mod.L1InputGuard
L3OutputGuard = _l3_mod.L3OutputGuard


# ─── Lazy RAG Backend (sync, run in executor) ────────────────────────────────────

_search = None
_reranker = None

def _init_rag():
    """Initialize RAG pipeline once (lazy singleton)."""
    global _search, _reranker
    if _search is None:
        from src.m1_chunking import load_documents, chunk_hierarchical
        from src.m2_search import HybridSearch
        from src.m3_rerank import CrossEncoderReranker

        docs = load_documents()
        all_chunks = []
        for doc in docs:
            _, children = chunk_hierarchical(doc["text"], metadata=doc["metadata"])
            for child in children:
                all_chunks.append({"text": child.text, "metadata": {**child.metadata, "parent_id": child.parent_id}})

        _search = HybridSearch()
        _search.index(all_chunks)
        _reranker = CrossEncoderReranker()


def _rag_query_sync(query: str) -> str:
    """Synchronous RAG call — runs in thread executor."""
    _init_rag()
    from src.pipeline import run_query
    answer, _ = run_query(query, _search, _reranker)
    return answer


# ─── Async Pipeline ───────────────────────────────────────────────────────────────

class FullPipeline:
    """Async end-to-end pipeline with per-stage latency telemetry."""

    def __init__(self):
        self.l1 = L1InputGuard()
        self.l3 = L3OutputGuard()

    async def run(self, raw_query: str) -> dict:
        """
        Process one user query through the full guardrail stack.

        Returns a dict with:
            - final_response: str
            - allowed: bool
            - blocked_by_l3: bool
            - pii_detected: list
            - latency: dict (l1_ms, rag_ms, l3_ms, total_ms, guardrail_overhead_ms)
        """
        pipeline_start = time.perf_counter()

        # ── Stage 1: L1 Input Guard (sync — fast, < 50ms) ───────────────────
        t1 = time.perf_counter()
        l1_result = self.l1.run(raw_query)
        l1_ms = (time.perf_counter() - t1) * 1000

        if not l1_result["allowed"]:
            total_ms = (time.perf_counter() - pipeline_start) * 1000
            return {
                "final_response": l1_result["reject_reason"],
                "allowed": False,
                "blocked_by_l3": False,
                "pii_detected": l1_result["pii_detected"],
                "latency": {
                    "l1_ms": round(l1_ms, 2),
                    "rag_ms": 0,
                    "l3_ms": 0,
                    "total_ms": round(total_ms, 2),
                    "guardrail_overhead_ms": round(l1_ms, 2),
                },
            }

        processed_query = l1_result["processed_query"]

        # ── Stage 2: RAG Backend (async via executor to avoid blocking) ──────
        t2 = time.perf_counter()
        try:
            loop = asyncio.get_event_loop()
            rag_answer = await loop.run_in_executor(None, _rag_query_sync, processed_query)
        except Exception as e:
            rag_answer = f"Không tìm thấy thông tin. (RAG error: {e})"
        rag_ms = (time.perf_counter() - t2) * 1000

        # ── Stage 3: L3 Output Guard (sync — Groq API call) ──────────────────
        t3 = time.perf_counter()
        l3_result = self.l3.run(processed_query, rag_answer)
        l3_ms = (time.perf_counter() - t3) * 1000

        total_ms = (time.perf_counter() - pipeline_start) * 1000
        guardrail_overhead_ms = l1_ms + l3_ms

        return {
            "final_response": l3_result["final_response"],
            "allowed": True,
            "blocked_by_l3": l3_result["blocked"],
            "pii_detected": l1_result["pii_detected"],
            "latency": {
                "l1_ms": round(l1_ms, 2),
                "rag_ms": round(rag_ms, 2),
                "l3_ms": round(l3_ms, 2),
                "total_ms": round(total_ms, 2),
                "guardrail_overhead_ms": round(guardrail_overhead_ms, 2),
            },
        }


# ─── Main Runner ─────────────────────────────────────────────────────────────────

async def main():
    pipeline = FullPipeline()

    queries = [
        "Nhân viên chính thức được nghỉ phép bao nhiêu ngày?",
        "Chính sách bảo hiểm PVI áp dụng sau mấy năm công tác?",
        "Liên hệ tôi qua SĐT 0987654321 để xác nhận đăng ký nghỉ phép",
        "Hôm nay ăn gì thì ngon?",
    ]

    print("=" * 70)
    print("FULL ASYNC E2E PIPELINE — Phase C")
    print("=" * 70)

    for q in queries:
        print(f"\n{'─'*60}")
        print(f" QUERY: {q}")
        result = await pipeline.run(q)

        if not result["allowed"]:
            print(f" BLOCKED by L1: {result['final_response']}")
        elif result["blocked_by_l3"]:
            print(f" BLOCKED by L3: {result['final_response'][:80]}")
        else:
            print(f" ANSWER: {result['final_response'][:120]}")

        lat = result["latency"]
        print(f"Latencies: L1={lat['l1_ms']:.0f}ms | RAG={lat['rag_ms']:.0f}ms | "
              f"L3={lat['l3_ms']:.0f}ms | Total={lat['total_ms']:.0f}ms | "
              f"Guardrail overhead={lat['guardrail_overhead_ms']:.0f}ms")

        if result["pii_detected"]:
            print(f" PII detected & anonymized: {result['pii_detected']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
