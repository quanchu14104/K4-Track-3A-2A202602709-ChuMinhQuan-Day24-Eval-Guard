import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src import m5_enrichment


def test_combined_enrichment_requests_and_validates_json(monkeypatch):
    payload = {
        "summary": "Quy định nghỉ phép năm.",
        "questions": ["Có bao nhiêu ngày phép?"],
        "context": "Quy định trong sổ tay nhân viên.",
        "metadata": {"topic": "nghỉ phép"},
    }
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))],
    )
    monkeypatch.setattr(m5_enrichment, "_is_openai_ready", lambda: True)
    monkeypatch.setattr(m5_enrichment, "create_openai_client", lambda: client)

    assert m5_enrichment._enrich_single_call("Nguồn nói 12 ngày.", "Sổ tay") == payload
    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["response_format"] == {"type": "json_object"}
    assert kwargs["extra_body"] == {"reasoning": {"effort": "low"}}
    assert kwargs["temperature"] == 0
    assert kwargs["max_tokens"] >= 1000


@pytest.mark.parametrize("payload", [
    {"summary": "", "questions": [], "context": "source", "metadata": {}},
    {"summary": "summary", "questions": [""], "context": "source", "metadata": {}},
    {"summary": "summary", "questions": [], "context": "", "metadata": {}},
    {"summary": "summary", "questions": [], "context": "source", "metadata": []},
])
def test_combined_enrichment_marks_incomplete_json_as_local_fallback(monkeypatch, payload):
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))],
    )
    monkeypatch.setattr(m5_enrichment, "_is_openai_ready", lambda: True)
    monkeypatch.setattr(m5_enrichment, "create_openai_client", lambda: client)

    result = m5_enrichment._enrich_single_call("source", "document")
    assert result["_local_fallback"] is True
    assert result["summary"]
    assert result["questions"]
    assert result["context"]
    assert result["metadata"]["category"] == "unknown"


def test_enrichment_result_records_local_fallback_method(monkeypatch):
    monkeypatch.setattr(m5_enrichment, "_enrich_single_call", lambda text, source: {
        "summary": "Summary",
        "questions": ["Question?"],
        "context": "Source context.",
        "metadata": {"category": "unknown"},
        "_local_fallback": True,
    })

    result = m5_enrichment.enrich_chunks([{"text": "source text", "metadata": {}}])[0]

    assert result.method == "combined+local_fallback"


def test_local_enrichment_mode_avoids_remote_llm(monkeypatch):
    monkeypatch.setattr(m5_enrichment, "_is_openai_ready", Mock(
        side_effect=AssertionError("Local mode must not check remote credentials")))

    result = m5_enrichment.enrich_chunks(
        [{"text": "A real sentence with enough words. A second useful sentence.",
          "metadata": {"source": "policy"}}],
        methods=["local"],
    )[0]

    assert result.method == "local_fallback"
    assert result.original_text.startswith("A real sentence")
    assert result.enriched_text.startswith("Trích từ policy.")
    assert result.summary


def test_combined_enrichment_retries_invalid_structured_output(monkeypatch):
    payload = {
        "summary": "Summary",
        "questions": ["Question?"],
        "context": "Document context.",
        "metadata": {},
    }
    client = Mock()
    client.chat.completions.create.side_effect = [
        SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content='{"summary":""}'))]),
        SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content=json.dumps(payload)))]),
    ]
    monkeypatch.setattr(m5_enrichment, "_is_openai_ready", lambda: True)
    monkeypatch.setattr(m5_enrichment, "create_openai_client", lambda: client)

    assert m5_enrichment._enrich_single_call("source", "document") == payload
    assert client.chat.completions.create.call_count == 2
