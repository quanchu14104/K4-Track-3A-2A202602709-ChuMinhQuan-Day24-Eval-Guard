from types import ModuleType, SimpleNamespace

import pytest

from src.m2_search import DenseSearch
from src.m3_rerank import CrossEncoderReranker


class FakeVector:
    def tolist(self):
        return [0.1, 0.2]


class FakeEncoder:
    def encode(self, _text, **_kwargs):
        return FakeVector()


def test_dense_search_uses_configured_qdrant_and_legacy_search_api(monkeypatch):
    captured = {}

    class FakeQdrantClient:
        def __init__(self, **kwargs):
            captured["client_options"] = kwargs

        def get_collections(self):
            captured["health_checked"] = True

        def search(self, **kwargs):
            captured["search_options"] = kwargs
            return [SimpleNamespace(payload={"text": "source text"}, score=0.75)]

    qdrant_module = ModuleType("qdrant_client")
    qdrant_module.QdrantClient = FakeQdrantClient
    monkeypatch.setitem(__import__("sys").modules, "qdrant_client", qdrant_module)

    search = DenseSearch()
    search._encoder = FakeEncoder()
    rows = search.search("question", top_k=2)

    assert captured["health_checked"] is True
    assert captured["search_options"]["query_vector"] == [0.1, 0.2]
    assert captured["search_options"]["limit"] == 2
    assert len(rows) == 1
    assert rows[0].text == "source text"
    assert rows[0].score == 0.75


def test_dense_search_surfaces_qdrant_connection_failure(monkeypatch):
    class UnavailableQdrant:
        def __init__(self, **_kwargs):
            pass

        def get_collections(self):
            raise ConnectionError("Qdrant unavailable")

    qdrant_module = ModuleType("qdrant_client")
    qdrant_module.QdrantClient = UnavailableQdrant
    monkeypatch.setitem(__import__("sys").modules, "qdrant_client", qdrant_module)

    with pytest.raises(ConnectionError, match="Qdrant unavailable"):
        DenseSearch()


def test_cross_encoder_reranks_with_requested_local_model(monkeypatch):
    captured = {}

    class FakeCrossEncoder:
        def __init__(self, model_name, **kwargs):
            captured["model_name"] = model_name
            captured["options"] = kwargs

        def predict(self, pairs):
            captured["pairs"] = pairs
            return [0.1, 0.9]

    sentence_transformers = ModuleType("sentence_transformers")
    sentence_transformers.CrossEncoder = FakeCrossEncoder
    monkeypatch.setitem(__import__("sys").modules, "sentence_transformers", sentence_transformers)

    reranker = CrossEncoderReranker("test-reranker")
    rows = reranker.rerank("question", [
        {"text": "less relevant", "score": 0.8, "metadata": {"source": "a"}},
        {"text": "more relevant", "score": 0.7, "metadata": {"source": "b"}},
    ])

    assert captured["model_name"] == "test-reranker"
    assert captured["options"]["local_files_only"] is True
    assert captured["pairs"] == [("question", "less relevant"), ("question", "more relevant")]
    assert [row.text for row in rows] == ["more relevant", "less relevant"]
