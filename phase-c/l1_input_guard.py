"""
Phase C — L1 Input Guardrail
Responsibilities:
  1. PII detection & anonymization via Microsoft Presidio
  2. Vietnamese-specific Regex recognizers: CCCD (12 digits) & phone (10 digits, 03/05/07/08/09 prefix)
  3. Topic Validator — rejects off-topic queries outside HR/company-policy domain
"""

import sys
import os
import re
import time

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ─── Presidio Setup ─────────────────────────────────────────────────────────────

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


# Entity types to DENY in Presidio scan (cause high false-positive on Vietnamese text)
_DENIED_ENTITY_TYPES = {
    "DATE_TIME", "US_BANK_NUMBER", "US_DRIVER_LICENSE",
    "US_SSN", "US_ITIN", "IBAN_CODE", "ORGANIZATION",
}

# Pre-scan regexes applied BEFORE Presidio (higher priority)
_PRE_SCAN_RULES = [
    (re.compile(r"\b(03|05|07|08|09)\d{8}\b"), "<PHONE_NUMBER>"),  # VN phone
    (re.compile(r"\b\d{12}\b"), "<VN_CCCD>"),                       # CCCD
]


def _build_analyzer() -> AnalyzerEngine:
    """Build Presidio AnalyzerEngine with Vietnamese custom recognizers."""
    try:
        configuration = {"nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]}
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
    except Exception:
        analyzer = AnalyzerEngine()

    # ── Vietnamese CCCD recognizer (12 consecutive digits) ───────────────────
    cccd_pattern = Pattern(
        name="VN_CCCD_pattern",
        regex=r"\b\d{12}\b",
        score=0.85,
    )
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[cccd_pattern],
        supported_language="en",  # applied regardless of detected language
    )

    # ── Vietnamese phone recognizer (10 digits, prefix 03/05/07/08/09) ──────
    phone_pattern = Pattern(
        name="VN_PHONE_pattern",
        regex=r"\b(03|05|07|08|09)\d{8}\b",
        score=0.90,
    )
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[phone_pattern],
        supported_language="en",
    )

    analyzer.registry.add_recognizer(cccd_recognizer)
    analyzer.registry.add_recognizer(phone_recognizer)

    return analyzer


_ANALYZER = _build_analyzer()
_ANONYMIZER = AnonymizerEngine()

# Replacement tags
_OPERATOR_CONFIGS = {
    "VN_CCCD":      OperatorConfig("replace", {"new_value": "<VN_CCCD>"}),
    "VN_PHONE":     OperatorConfig("replace", {"new_value": "<PHONE_NUMBER>"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE_NUMBER>"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
    "PERSON":       OperatorConfig("replace", {"new_value": "<PERSON>"}),
    "LOCATION":     OperatorConfig("replace", {"new_value": "<LOCATION>"}),
    "CREDIT_CARD":  OperatorConfig("replace", {"new_value": "<CREDIT_CARD>"}),
}


def anonymize_pii(text: str) -> tuple[str, list[str]]:
    """
    Detect and replace PII in text.
    Strategy:
      1. Pre-scan with high-priority VN regex (CCCD, phone) — these win over Presidio.
      2. Pass the pre-scanned text to Presidio for remaining entity types.

    Returns:
        (anonymized_text, list_of_detected_entity_types)
    """
    detected: list[str] = []

    # Step 1: High-priority VN regex pre-scan
    pre_scanned = text
    for pattern, replacement in _PRE_SCAN_RULES:
        if pattern.search(pre_scanned):
            entity_label = "VN_CCCD" if "CCCD" in replacement else "VN_PHONE"
            detected.append(entity_label)
            pre_scanned = pattern.sub(replacement, pre_scanned)

    # Step 2: Presidio scan on pre-scanned text (VN entities already masked)
    results = _ANALYZER.analyze(text=pre_scanned, language="en")
    # Filter out noisy/false-positive entity types
    results = [r for r in results if r.entity_type not in _DENIED_ENTITY_TYPES]

    if not results:
        return pre_scanned, detected

    presidio_detected = [r.entity_type for r in results]
    detected.extend(presidio_detected)
    operators = {etype: _OPERATOR_CONFIGS[etype] for etype in presidio_detected if etype in _OPERATOR_CONFIGS}

    anonymized = _ANONYMIZER.anonymize(text=pre_scanned, analyzer_results=results, operators=operators)
    return anonymized.text, detected


# ─── Topic Validator ─────────────────────────────────────────────────────────────

# HR / company-policy domain keywords (Vietnamese + English)
_ALLOWED_KEYWORDS = [
    # Vietnamese
    "nghỉ phép", "bảo hiểm", "lương", "thưởng", "phúc lợi", "hợp đồng",
    "tuyển dụng", "đào tạo", "nội quy", "quy định", "làm việc", "hr portal",
    "nhân viên", "công ty", "thâm niên", "khen thưởng", "kỷ luật",
    "thời gian", "ca làm việc", "chính sách", "phòng ban", "quản lý",
    "đăng ký", "hồ sơ", "hợp đồng lao động", "tết", "lễ", "nghỉ lễ",
    # English
    "leave", "annual leave", "insurance", "salary", "bonus", "benefit",
    "contract", "recruitment", "training", "policy", "regulation",
    "employee", "company", "seniority", "discipline", "hr", "remote",
    "work from home", "wfh", "overtime", "probation", "onboarding",
]

# Off-topic signals (hard reject patterns)
_BLOCKED_PATTERNS = [
    r"\bthời tiết\b", r"\bweather\b",
    r"\bchính trị\b", r"\bpolitics?\b",
    r"\bchứng khoán\b", r"\bstock\b", r"\bcoin\b", r"\bcrypto\b",
    r"\bbóng đá\b", r"\bsports?\b", r"\bfootball\b",
    r"\bhôm nay ăn\b", r"\bnên ăn gì\b", r"\brecip[ei]\b",
    r"\bgame\b", r"\bgiải trí\b", r"\bentertainment\b",
]

_BLOCKED_RE = re.compile("|".join(_BLOCKED_PATTERNS), re.IGNORECASE)


def validate_topic(text: str) -> tuple[bool, str]:
    """
    Check if the query is on-topic for the HR/company-policy domain.

    Returns:
        (is_allowed: bool, reason: str)
    """
    text_lower = text.lower()

    # Hard reject: explicitly off-topic signals
    if _BLOCKED_RE.search(text_lower):
        return False, "Câu hỏi nằm ngoài phạm vi hỗ trợ (off-topic). Hệ thống chỉ hỗ trợ các câu hỏi liên quan đến chính sách và quy định công ty."

    # Soft allow: check for any domain keyword
    for kw in _ALLOWED_KEYWORDS:
        if kw in text_lower:
            return True, "on-topic"

    # Default: reject short queries with no domain signal
    if len(text.split()) <= 3:
        return False, "Câu hỏi quá ngắn hoặc không rõ chủ đề. Vui lòng cung cấp thêm ngữ cảnh."

    # Longer queries with no signal — pass through with warning (lenient policy)
    return True, "on-topic (no strong signal, permitting)"


# ─── Public API ──────────────────────────────────────────────────────────────────

class L1InputGuard:
    """Two-step input guardrail: anonymize PII then validate topic."""

    def run(self, query: str) -> dict:
        """
        Process a raw user query through L1.

        Returns a dict with:
            - allowed (bool)
            - processed_query (str) — PII-anonymized version
            - pii_detected (list[str])
            - reject_reason (str | None)
            - latency_ms (float)
        """
        t0 = time.perf_counter()

        # Step 1: Anonymize PII
        processed, pii_detected = anonymize_pii(query)

        # Step 2: Topic validation (run on anonymized text)
        is_allowed, reason = validate_topic(processed)

        latency_ms = (time.perf_counter() - t0) * 1000

        return {
            "allowed": is_allowed,
            "processed_query": processed,
            "pii_detected": pii_detected,
            "reject_reason": None if is_allowed else reason,
            "latency_ms": round(latency_ms, 2),
        }


# ─── CLI Demo ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    guard = L1InputGuard()
    test_cases = [
        "Cập nhật hộ tôi số CCCD 001099123456 vào hệ thống",
        "Liên hệ tôi qua SĐT 0987654321 để xác nhận nghỉ phép",
        "Hôm nay ăn gì?",
        "Nhân viên chính thức được nghỉ phép bao nhiêu ngày?",
        "Chính sách bảo hiểm y tế của công ty như thế nào?",
    ]

    print("=" * 60)
    print("L1 INPUT GUARD — Demo")
    print("=" * 60)
    for q in test_cases:
        result = guard.run(q)
        status = " ALLOWED" if result["allowed"] else " BLOCKED"
        print(f"\n[INPUT]  {q}")
        print(f"[OUTPUT] {result['processed_query']}")
        print(f"[STATUS] {status} | PII={result['pii_detected']} | {result['latency_ms']:.1f}ms")
        if not result["allowed"]:
            print(f"[REASON] {result['reject_reason']}")
    print("\n" + "=" * 60)
