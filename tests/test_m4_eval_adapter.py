from types import ModuleType, SimpleNamespace

import pytest

from src import m4_eval


class FakeDataFrame:
    def __init__(self, rows):
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def iterrows(self):
        return iter(enumerate(self.rows))


def install_fake_ragas(monkeypatch, rows):
    captured = {}
    dataset_module = ModuleType("datasets")
    dataset_module.Dataset = SimpleNamespace(from_dict=lambda values: values)

    class FakeModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            captured[type(self).__name__] = kwargs

    langchain_module = ModuleType("langchain_openai")
    class FakeChatModel(FakeModel):
        pass

    class FakeEmbeddings(FakeModel):
        pass

    langchain_module.ChatOpenAI = FakeChatModel
    community_embeddings_module = ModuleType("langchain_community.embeddings")
    community_embeddings_module.HuggingFaceEmbeddings = FakeEmbeddings

    result = SimpleNamespace(to_pandas=lambda: FakeDataFrame(rows))
    ragas_module = ModuleType("ragas")
    def evaluate(dataset, **kwargs):
        captured["evaluation"] = kwargs
        return result

    ragas_module.evaluate = evaluate
    metrics_module = ModuleType("ragas.metrics")
    for name in ("faithfulness", "answer_relevancy", "context_precision", "context_recall"):
        setattr(metrics_module, name, name)

    monkeypatch.setitem(__import__("sys").modules, "datasets", dataset_module)
    monkeypatch.setitem(__import__("sys").modules, "langchain_openai", langchain_module)
    monkeypatch.setitem(
        __import__("sys").modules, "langchain_community.embeddings",
        community_embeddings_module,
    )
    monkeypatch.setitem(__import__("sys").modules, "ragas", ragas_module)
    monkeypatch.setitem(__import__("sys").modules, "ragas.metrics", metrics_module)
    return captured


def make_row(**updates):
    row = {
        "question": "Question",
        "answer": "Answer",
        "contexts": ["Context"],
        "ground_truth": "Reference",
        "faithfulness": 0.8,
        "answer_relevancy": 0.7,
        "context_precision": 0.6,
        "context_recall": 0.5,
    }
    row.update(updates)
    return row


def test_ragas_adapter_uses_explicit_models_and_reports_provenance(monkeypatch):
    captured = install_fake_ragas(monkeypatch, [make_row()])
    monkeypatch.setattr(m4_eval, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(m4_eval, "OPENAI_ENDPOINT_URL", "https://example.invalid/v1")
    monkeypatch.setattr(m4_eval, "RAGAS_EVALUATOR_MODEL", "evaluator-llm")
    monkeypatch.setattr(m4_eval, "RAGAS_EVALUATOR_EMBEDDING_MODEL", "evaluator-embedding")

    report = m4_eval.evaluate_ragas(["Question"], ["Answer"], [["Context"]], ["Reference"])

    assert report["metadata"]["evaluator_models"] == [
        "evaluator-embedding", "evaluator-llm"
    ]
    assert captured["FakeChatModel"]["model"] == "evaluator-llm"
    assert captured["FakeEmbeddings"]["model_name"] == "evaluator-embedding"
    assert captured["FakeEmbeddings"]["model_kwargs"] == {"local_files_only": True}
    assert captured["FakeEmbeddings"]["encode_kwargs"] == {"normalize_embeddings": True}
    assert captured["FakeChatModel"]["base_url"] == "https://example.invalid/v1"
    assert captured["evaluation"]["raise_exceptions"] is True
    assert len(report["per_question"]) == 1
    assert report["per_question"][0].faithfulness == 0.8
    assert report["per_question"][0].context_recall == 0.5


@pytest.mark.parametrize("score", [float("nan"), float("inf"), -0.1, 1.1])
def test_ragas_adapter_rejects_invalid_scores(monkeypatch, score):
    install_fake_ragas(monkeypatch, [make_row(faithfulness=score)])
    monkeypatch.setattr(m4_eval, "OPENAI_API_KEY", "test-key")

    with pytest.raises(ValueError, match="faithfulness"):
        m4_eval.evaluate_ragas(["Question"], ["Answer"], [["Context"]], ["Reference"])


def test_ragas_adapter_requires_equal_nonempty_inputs():
    with pytest.raises(ValueError, match="equal length"):
        m4_eval.evaluate_ragas(["Question"], [], [["Context"]], ["Reference"])
    with pytest.raises(ValueError, match="equal length"):
        m4_eval.evaluate_ragas([], [], [], [])


def test_ragas_adapter_requires_api_credentials(monkeypatch):
    monkeypatch.setattr(m4_eval, "OPENAI_API_KEY", "")

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        m4_eval.evaluate_ragas(["Question"], ["Answer"], [["Context"]], ["Reference"])
