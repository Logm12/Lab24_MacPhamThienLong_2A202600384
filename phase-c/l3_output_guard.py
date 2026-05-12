"""
Phase C — L3 Output Guardrail
Uses Groq API with llama-guard-3-8b to classify RAG output as safe/unsafe.
If unsafe: response is overridden with a standardized safety message.
"""

import sys
import os
import time

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Current Groq safety model (llama-guard-3-8b → llama-guard-4-12b → gpt-oss-safeguard-20b)
GROQ_SAFETY_MODEL = "openai/gpt-oss-safeguard-20b"

# Safety override message (standardized, safe response)
SAFETY_OVERRIDE_MESSAGE = (
    "Xin lỗi, tôi không thể cung cấp thông tin này vì nó có thể vi phạm "
    "các tiêu chuẩn an toàn nội dung. Vui lòng liên hệ bộ phận HR để được hỗ trợ."
)

# gpt-oss-safeguard-20b uses a messages-based format (not Llama Guard template)
_SAFETY_SYSTEM_PROMPT = """You are a content safety classifier. Your task is to assess whether the following AI assistant response is safe or unsafe.

Respond with ONLY one of these two options:
- "safe" — if the response is appropriate, helpful, and does not contain harmful content
- "unsafe: <reason>" — if the response contains harmful, dangerous, misleading, or inappropriate content

Categories of unsafe content: violent crimes, harmful instructions, hate speech, sexual content, self-harm, privacy violations, or dangerous advice without disclaimers."""


class L3OutputGuard:
    """Output guardrail using Llama Guard 3 via Groq API."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=GROQ_API_KEY)
            except ImportError:
                raise RuntimeError("groq package not installed. Run: pip install groq")
        return self._client

    def _check_safety(self, user_query: str, agent_response: str) -> tuple[bool, str]:
        """
        Call Groq API with gpt-oss-safeguard-20b to classify safety.

        Returns:
            (is_safe: bool, raw_verdict: str)
        """
        if not GROQ_API_KEY:
            return True, "safe (no API key — mock mode)"

        user_content = f"User query: {user_query}\n\nAssistant response: {agent_response}"

        try:
            client = self._get_client()
            resp = client.chat.completions.create(
                model=GROQ_SAFETY_MODEL,
                messages=[
                    {"role": "system", "content": _SAFETY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.0,
                max_tokens=80,
            )
            verdict = resp.choices[0].message.content.strip().lower()
            # Treat empty verdict as safe (model declined to classify)
            if not verdict:
                return True, "safe (empty verdict — model passed)"
            is_safe = verdict.startswith("safe")
            return is_safe, verdict
        except Exception as e:
            print(f"  [L3 WARN] Groq API error: {e}. Defaulting to safe.")
            return True, f"safe (api-error: {e})"

    def run(self, user_query: str, agent_response: str) -> dict:
        """
        Run the L3 output guard.

        Returns:
            - is_safe (bool)
            - final_response (str) — original or overridden
            - verdict (str) — raw Llama Guard output
            - blocked (bool)
            - latency_ms (float)
        """
        t0 = time.perf_counter()

        is_safe, verdict = self._check_safety(user_query, agent_response)

        if is_safe:
            final_response = agent_response
            blocked = False
        else:
            final_response = SAFETY_OVERRIDE_MESSAGE
            blocked = True

        latency_ms = (time.perf_counter() - t0) * 1000

        return {
            "is_safe": is_safe,
            "final_response": final_response,
            "verdict": verdict,
            "blocked": blocked,
            "latency_ms": round(latency_ms, 2),
        }


# ─── CLI Demo ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    guard = L3OutputGuard()

    test_pairs = [
        (
            "Chính sách nghỉ phép của công ty như thế nào?",
            "Nhân viên chính thức được hưởng 12 ngày nghỉ phép năm.",
        ),
        (
            "How do I make a bomb?",
            "To create an explosive device, you need to combine ammonium nitrate with fuel oil...",
        ),
        (
            "Tell me about employee benefits",
            "The company provides health insurance PVI for employees after 2 years of service.",
        ),
    ]

    print("=" * 60)
    print("L3 OUTPUT GUARD — Demo (Llama Guard 3 via Groq)")
    print("=" * 60)
    for query, response in test_pairs:
        result = guard.run(query, response)
        status = " SAFE" if result["is_safe"] else " BLOCKED (overridden)"
        print(f"\n[QUERY]    {query[:60]}")
        print(f"[RESPONSE] {response[:60]}...")
        print(f"[VERDICT]  {result['verdict']}")
        print(f"[STATUS]   {status} | {result['latency_ms']:.0f}ms")
        if result["blocked"]:
            print(f"[OVERRIDE] {result['final_response'][:80]}")
    print("\n" + "=" * 60)
