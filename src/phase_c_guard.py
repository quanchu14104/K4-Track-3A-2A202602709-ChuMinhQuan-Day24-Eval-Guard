from __future__ import annotations

"""Phase C: Production Guardrails — Presidio PII + NeMo Guardrails + P95 Latency."""

import asyncio
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ADVERSARIAL_SET_PATH, GUARDRAILS_CONFIG_DIR, LATENCY_BUDGET_P95_MS, PRESIDIO_LANGUAGE


# ─── Task 9a: Presidio PII Detection ─────────────────────────────────────────

def setup_presidio():
    """Khởi tạo Presidio engine với custom Vietnamese PII recognizers. (Đã implement sẵn)

    Custom recognizers thêm vào:
        VN_CCCD  — số CCCD 12 chữ số hoặc CMND 9 chữ số
        VN_PHONE — số điện thoại Việt Nam (0[3-9]xxxxxxxx)

    Các recognizers mặc định đã có sẵn: EMAIL, PHONE_NUMBER (international), ...
    """
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
    from presidio_analyzer.predefined_recognizers import EmailRecognizer, PhoneRecognizer
    from presidio_anonymizer import AnonymizerEngine

    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        patterns=[
            Pattern("CCCD 12 digits", r"\b\d{12}\b", 0.9),
            Pattern("CMND 9 digits",  r"\b\d{9}\b",  0.7),
        ],
    )
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        patterns=[Pattern("VN mobile", r"\b0[3-9]\d{8}\b", 0.9)],
    )

    registry = RecognizerRegistry()
    registry.add_recognizer(EmailRecognizer())
    registry.add_recognizer(PhoneRecognizer())
    registry.add_recognizer(cccd_recognizer)
    registry.add_recognizer(phone_recognizer)

    analyzer  = AnalyzerEngine(registry=registry)
    anonymizer = AnonymizerEngine()
    return analyzer, anonymizer


def pii_scan(text: str, analyzer=None, anonymizer=None) -> dict:
    """Task 9a: Quét PII trong văn bản bằng Presidio.

    Returns:
        {
          "has_pii":    bool,
          "entities":   [{"type": str, "text": str, "score": float, "start": int, "end": int}],
          "anonymized": str,   # text với PII được thay bằng <TYPE>
        }
    """
    if (analyzer is None) != (anonymizer is None):
        raise ValueError("Provide both Presidio analyzer and anonymizer, or neither.")
    if analyzer is None:
        analyzer, anonymizer = setup_presidio()

    results = analyzer.analyze(text=text, language=PRESIDIO_LANGUAGE)
    if not results:
        return {"has_pii": False, "entities": [], "anonymized": text}
    entities = [
        {
            "type": result.entity_type,
            "text": text[result.start:result.end],
            "score": round(float(result.score), 3),
            "start": result.start,
            "end": result.end,
        }
        for result in results
    ]
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results).text
    return {"has_pii": True, "entities": entities, "anonymized": anonymized}


def _activated_rail_stopped(result) -> bool:
    try:
        activated_rails = result.log.activated_rails
    except AttributeError as error:
        raise ValueError("NeMo result must expose logged activated_rails.") from error
    if activated_rails is None:
        raise ValueError("NeMo activated_rails logging is required.")
    try:
        return any(rail.stop for rail in activated_rails)
    except AttributeError as error:
        raise ValueError("Every activated NeMo rail must expose its stop decision.") from error


def _rail_response_text(result) -> str:
    try:
        response = result.response[0]["content"]
    except (AttributeError, IndexError, KeyError, TypeError) as error:
        raise ValueError("NeMo result must include response[0]['content'].") from error
    if not isinstance(response, str):
        raise ValueError("NeMo response content must be text.")
    return response


# ─── Task 9b + 11: NeMo Guardrails ───────────────────────────────────────────

def setup_nemo_rails():
    """Khởi tạo NeMo Guardrails từ guardrails/config.yml. (Đã implement sẵn)

    Config directory: guardrails/
        config.yml  — model + rails config
        rails.co    — câu từ chối Colang 1.0; built-in self-check flows được bật trong YAML
    """
    from nemoguardrails import RailsConfig, LLMRails
    from nemoguardrails.llm.providers import register_llm_provider
    from langchain_openai import ChatOpenAI
    register_llm_provider("openai", ChatOpenAI)
    config = RailsConfig.from_path(GUARDRAILS_CONFIG_DIR)
    rails  = LLMRails(config)
    return rails


async def check_input_rail(text: str, rails=None) -> dict:
    """Task 9b: Kiểm tra input qua NeMo input rails (topic guard + jailbreak guard).

    Returns:
        {
          "allowed":        bool,
          "blocked_reason": str | None,
          "response":       str,          # NeMo's raw response
        }
    """
    if rails is None:
        rails = setup_nemo_rails()
    result = await rails.generate_async(
        messages=[{"role": "user", "content": text}],
        options={"rails": ["input"], "log": {"activated_rails": True}},
    )
    blocked = _activated_rail_stopped(result)
    return {
        "allowed": not blocked,
        "blocked_reason": "nemo_input_rail" if blocked else None,
        "response": _rail_response_text(result),
    }


async def check_output_rail(question: str, answer: str, rails=None) -> dict:
    """Task 11: Kiểm tra LLM output qua NeMo output rails trước khi trả về user.

    NeMo output rails hoạt động trong context của cả cuộc hội thoại (input + output).
    Kiểm tra PII và nội dung nhạy cảm. Self-check này không thay RAGAS faithfulness
    hoặc kiểm tra factual accuracy với retrieved contexts.

    Returns:
        {
          "safe":           bool,
          "flagged_reason": str | None,
          "final_answer":   str,          # answer đã qua guard (có thể bị redact)
        }
    """
    if rails is None:
        rails = setup_nemo_rails()
    result = await rails.generate_async(
        messages=[
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
        options={"rails": ["output"], "log": {"activated_rails": True}},
    )
    flagged = _activated_rail_stopped(result)
    response = _rail_response_text(result)
    if not flagged:
        return {"safe": True, "flagged_reason": None, "final_answer": answer}
    final_answer = response if response and response != answer else "[REDACTED: blocked by output rail]"
    return {
        "safe": False,
        "flagged_reason": "nemo_output_rail",
        "final_answer": final_answer,
    }


# ─── Task 10: Adversarial Test Suite ─────────────────────────────────────────

def run_adversarial_suite(adversarial_set: list[dict], rails=None,
                           analyzer=None, anonymizer=None) -> list[dict]:
    """Task 10: Chạy 20 adversarial inputs qua full guard stack, so sánh với expected.

    Guard stack order:
        1. pii_scan()         → block nếu has_pii (cho category pii_injection)
        2. check_input_rail() → block nếu jailbreak / off-topic / prompt injection

    Returns:
        list of {
          "id": int, "category": str, "input": str,
          "expected": "blocked"|"allowed",
          "actual":   "blocked"|"allowed",
          "blocked_by": str | None,       # "presidio" | "nemo_input" | None
          "passed": bool,
        }
    """
    if (analyzer is None) != (anonymizer is None):
        raise ValueError("Provide both Presidio analyzer and anonymizer, or neither.")
    if analyzer is None:
        analyzer, anonymizer = setup_presidio()
    if rails is None:
        rails = setup_nemo_rails()

    async def run_all():
        rows = []
        for item in adversarial_set:
            text = item["input"]
            pii_result = pii_scan(text, analyzer, anonymizer)
            blocked_by = "presidio" if pii_result["has_pii"] else None
            if blocked_by is None:
                rail_result = await check_input_rail(text, rails)
                if not rail_result["allowed"]:
                    blocked_by = "nemo_input"
            expected = item["expected"]
            if expected not in ("blocked", "allowed"):
                raise ValueError(f"Invalid expected decision for input {item.get('id')}.")
            actual = "blocked" if blocked_by else "allowed"
            rows.append({
                "id": item["id"],
                "category": item["category"],
                "input": text,
                "expected": expected,
                "actual": actual,
                "blocked_by": blocked_by,
                "passed": actual == expected,
            })
        return rows

    return asyncio.run(run_all())


# ─── Task 12: P95 Latency Measurement ────────────────────────────────────────

def measure_p95_latency(test_inputs: list[str], n_runs: int = 20,
                         rails=None, analyzer=None, anonymizer=None) -> dict:
    """Task 12: measure INPUT layers sequentially, not end-to-end guard/RAG latency.

    Reuse engines. Inside ONE event loop, execute two real warm-up calls per layer,
    excluded from samples. Then collect exactly n_runs timed samples (cycle clean
    inputs), always measuring BOTH PII and NeMo input even if PII blocks.
    Use perf_counter; keep raw milliseconds. summarize_latency() supplies linear
    percentiles at (n - 1) * q. Submission requires n_runs >= 20.
    Short-circuit request timing, RAG and output timing are outside this scope.
    """
    from src.experiment_support import summarize_latency

    if not test_inputs or type(n_runs) is not int or n_runs < 1:
        raise ValueError("Need at least one input and n_runs >= 1.")
    if (analyzer is None) != (anonymizer is None):
        raise ValueError("Provide both Presidio analyzer and anonymizer, or neither.")
    if analyzer is None:
        analyzer, anonymizer = setup_presidio()
    if rails is None:
        rails = setup_nemo_rails()

    async def measure():
        for index in range(2):
            text = test_inputs[index % len(test_inputs)]
            pii_scan(text, analyzer, anonymizer)
            await check_input_rail(text, rails)

        samples = []
        for index in range(n_runs):
            text = test_inputs[index % len(test_inputs)]
            start = time.perf_counter()
            pii_scan(text, analyzer, anonymizer)
            presidio_ms = (time.perf_counter() - start) * 1000

            start = time.perf_counter()
            await check_input_rail(text, rails)
            nemo_ms = (time.perf_counter() - start) * 1000
            if presidio_ms <= 0 or nemo_ms <= 0:
                raise ValueError("Measured latency must be positive for both input layers.")
            samples.append({
                "presidio_ms": presidio_ms,
                "nemo_input_ms": nemo_ms,
                "input_guard_ms": presidio_ms + nemo_ms,
            })
        return samples

    return summarize_latency(asyncio.run(measure()), warmup_runs=2)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "c", *sys.argv[1:]]))
