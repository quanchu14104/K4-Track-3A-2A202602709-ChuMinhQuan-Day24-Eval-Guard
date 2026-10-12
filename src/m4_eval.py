from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import math
import os, sys, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (OPENAI_API_KEY, OPENAI_ENDPOINT_URL, RAGAS_EVALUATOR_MODEL,
                    RAGAS_EVALUATOR_EMBEDDING_MODEL, TEST_SET_PATH)


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run all four RAGAS metrics using explicitly configured evaluator models."""
    sizes = {len(questions), len(answers), len(contexts), len(ground_truths)}
    if len(sizes) != 1 or not questions:
        raise ValueError("RAGAS inputs must be non-empty lists of equal length.")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required for live RAGAS evaluation.")

    from datasets import Dataset
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_openai import ChatOpenAI
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    client_options = {"api_key": OPENAI_API_KEY}
    if OPENAI_ENDPOINT_URL:
        client_options["base_url"] = OPENAI_ENDPOINT_URL
    evaluator_llm = ChatOpenAI(model=RAGAS_EVALUATOR_MODEL, **client_options)
    evaluator_embeddings = HuggingFaceEmbeddings(
        model_name=RAGAS_EVALUATOR_EMBEDDING_MODEL,
        model_kwargs={"local_files_only": True},
        encode_kwargs={"normalize_embeddings": True},
    )
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        raise_exceptions=True,
    )
    df = result.to_pandas()
    metrics = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    if len(df) != len(questions):
        raise ValueError("RAGAS returned a different number of rows than the input.")
    per_question = []
    for _, row in df.iterrows():
        scores = {}
        for metric in metrics:
            value = float(row[metric])
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"RAGAS returned invalid {metric} score: {value!r}.")
            scores[metric] = value
        per_question.append(EvalResult(
            question=str(row["question"]),
            answer=str(row["answer"]),
            contexts=list(row["contexts"]),
            ground_truth=str(row["ground_truth"]),
            **scores,
        ))
    return {
        **{
            metric: sum(getattr(row, metric) for row in per_question) / len(per_question)
            for metric in metrics
        },
        "per_question": per_question,
        "metadata": {
            "evaluator_models": sorted({
                RAGAS_EVALUATOR_MODEL, RAGAS_EVALUATOR_EMBEDDING_MODEL
            })
        },
    }


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    diagnostic_tree = {
        "faithfulness": ("LLM hallucinating", "Tighten prompt, lower temperature"),
        "context_recall": ("Missing relevant chunks", "Improve chunking or add BM25"),
        "context_precision": ("Too many irrelevant chunks", "Add reranking or metadata filter"),
        "answer_relevancy": ("Answer doesn't match question", "Improve prompt template"),
    }
    items = []
    for res in eval_results:
        metric_scores = {
            "faithfulness": res.faithfulness,
            "context_recall": res.context_recall,
            "context_precision": res.context_precision,
            "answer_relevancy": res.answer_relevancy,
        }
        avg_score = sum(metric_scores.values()) / 4.0
        worst_metric = min(metric_scores, key=metric_scores.get)
        diag, fix = diagnostic_tree.get(
            worst_metric, ("Unknown error", "Review pipeline components")
        )
        items.append({
            "question": res.question,
            "answer": res.answer,
            "ground_truth": res.ground_truth,
            "worst_metric": worst_metric,
            "score": float(metric_scores[worst_metric]),
            "avg_score": float(avg_score),
            "diagnosis": diag,
            "suggested_fix": fix,
        })

    items.sort(key=lambda x: x["avg_score"])
    return items[:bottom_n]


def save_report(results: dict, failures: list[dict], path: str = "reports/ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
