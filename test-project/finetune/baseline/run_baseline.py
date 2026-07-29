#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "scikit-learn",
#     "rich",
#     "requests",
# ]
# ///

# allow: SIZE_OK — cohesive evaluation pipeline, boilerplate-heavy (PEP 723, types)

# ─── How to run ───
# Requires: Ollama running on localhost:11434
#
# Run with uv:
#     uv run run_baseline.py
#
# Or with custom eval path:
#     uv run run_baseline.py --eval-path test-project/finetune/dataset/eval.jsonl
#
# Model can be overridden:
#     uv run run_baseline.py --model llama3.1
# ──────────────────

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import requests
from rich.console import Console
from rich.table import Table

# ─── Constants ────────────────────────────────────────────────

LABELED_CATEGORIES: Final[list[str]] = [
    "крайне негативный",
    "негативный",
    "нейтральный",
    "позитивный",
]

SYSTEM_PROMPT: Final[str] = (
    "Ты — классификатор тональности отзывов. Определи категорию отзыва.\n"
    "Категории: крайне негативный, негативный, нейтральный, позитивный.\n"
    "Отвечай только названием категории."
)

MODEL_NAME: Final[str] = "qwen3:14b"
OLLAMA_URL: Final[str] = "http://localhost:11434"

# ─── Data models ──────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Prediction:
    """Single evaluation prediction."""

    index: int
    user_content: str
    predicted: str
    actual: str
    correct: bool


@dataclass(frozen=True, slots=True)
class ClassMetrics:
    """Per-class precision/recall/f1."""

    precision: float
    recall: float
    f1: float
    support: int


# ─── Core logic ───────────────────────────────────────────────


def load_examples(path: Path) -> list[dict]:
    """Load JSONL dataset, returning list of parsed JSON objects."""
    examples: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            examples.append(json.loads(line))
    return examples


def extract_fields(example: dict) -> tuple[str, str, str]:
    """Extract system prompt, user content, and actual label from a message format example."""
    messages: list[dict[str, str]] = example["messages"]
    system = ""
    user = ""
    assistant = ""
    for msg in messages:
        match msg["role"]:
            case "system":
                system = msg["content"]
            case "user":
                user = msg["content"]
            case "assistant":
                assistant = msg["content"]
            case _:
                pass
    return system, user, assistant


def classify(user_content: str, system_prompt: str, model: str) -> str:
    """Send single classification request to Ollama and return model's response."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.0,
        "stream": False,
    }
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("message", {}).get("content", "").strip()


def run_evaluation(
    examples: list[dict],
    model: str,
) -> list[Prediction]:
    """Run zero-shot classification on all examples. Returns list of predictions."""
    console = Console()
    predictions: list[Prediction] = []

    for i, example in enumerate(examples):
        _system, user_content, actual = extract_fields(example)
        predicted = classify(user_content, SYSTEM_PROMPT, model).strip()
        correct = predicted == actual

        console.print(
            f"[{'green' if correct else 'red'}]#{i + 1:2d}[/] "
            f"pred=[bold]{predicted}[/] | "
            f"gold=[bold]{actual}[/] | "
            f"{'✓' if correct else '✗'}"
        )

        predictions.append(
            Prediction(
                index=i,
                user_content=user_content,
                predicted=predicted,
                actual=actual,
                correct=correct,
            )
        )

    return predictions


def compute_metrics(predictions: list[Prediction]) -> dict:
    """Compute classification metrics from predictions.

    Returns dict with all metrics ready for JSON serialization.
    """
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        precision_score,
        recall_score,
        confusion_matrix,
        classification_report,
    )

    y_true = [p.actual for p in predictions]
    y_pred = [p.predicted for p in predictions]

    # Handle OOV predictions — treat as mismatches only, metrics use known labels
    known_labels = LABELED_CATEGORIES
    mask = [y in known_labels for y in y_pred]
    y_pred_clean = [
        p if m else "unknown" for p, m in zip(y_pred, mask)
    ]

    acc = accuracy_score(y_true, y_pred_clean)

    # Per-class metrics
    per_class: dict[str, ClassMetrics] = {}
    for label in known_labels:
        labels = [label, "unknown"]
        p = precision_score(y_true, y_pred_clean, labels=labels, zero_division=0, average=None)[0]
        r = recall_score(y_true, y_pred_clean, labels=labels, zero_division=0, average=None)[0]
        f = f1_score(y_true, y_pred_clean, labels=labels, zero_division=0, average=None)[0]
        support = sum(1 for y in y_true if y == label)
        per_class[label] = ClassMetrics(
            precision=round(p, 4),
            recall=round(r, 4),
            f1=round(f, 4),
            support=support,
        )

    macro_f1 = f1_score(y_true, y_pred_clean, labels=known_labels, average="macro", zero_division=0)
    macro_p = precision_score(y_true, y_pred_clean, labels=known_labels, average="macro", zero_division=0)
    macro_r = recall_score(y_true, y_pred_clean, labels=known_labels, average="macro", zero_division=0)
    macro_support = len(predictions)
    macro_avg = ClassMetrics(
        precision=round(macro_p, 4),
        recall=round(macro_r, 4),
        f1=round(macro_f1, 4),
        support=macro_support,
    )

    weight_f1 = f1_score(y_true, y_pred_clean, labels=known_labels, average="weighted", zero_division=0)
    weight_p = precision_score(y_true, y_pred_clean, labels=known_labels, average="weighted", zero_division=0)
    weight_r = recall_score(y_true, y_pred_clean, labels=known_labels, average="weighted", zero_division=0)
    weighted_avg = ClassMetrics(
        precision=round(weight_p, 4),
        recall=round(weight_r, 4),
        f1=round(weight_f1, 4),
        support=macro_support,
    )

    cm = confusion_matrix(y_true, y_pred_clean, labels=known_labels)
    cm_list = cm.tolist()

    report_text = classification_report(
        y_true, y_pred_clean, labels=known_labels, zero_division=0
    )

    return {
        "accuracy": round(acc, 4),
        "per_class": per_class,
        "macro_avg": macro_avg,
        "weighted_avg": weighted_avg,
        "confusion_matrix": cm_list,
        "classification_report": report_text,
    }


def print_confusion_matrix(cm: list[list[int]], labels: list[str], console: Console) -> None:
    """Print confusion matrix as a rich table."""
    table = Table(title="Confusion Matrix", show_header=True, header_style="bold magenta")
    table.add_column("Actual ↘ Pred ↙", style="dim")
    for label in labels:
        table.add_column(label, justify="right")

    for i, label in enumerate(labels):
        row = [label]
        for val in cm[i]:
            row.append(str(val))
        table.add_row(*row)

    console.print(table)


def _dataclass_to_dict(obj: object) -> object:
    """Convert dataclass instances (including slotted) to plain dicts for JSON."""
    if hasattr(obj, "__dataclass_fields__"):
        import dataclasses as dc

        return {
            f.name: _dataclass_to_dict(getattr(obj, f.name))
            for f in dc.fields(obj)
        }
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_dataclass_to_dict(v) for v in obj]
    return obj


def save_results(
    output_path: Path,
    metrics: dict,
    predictions: list[Prediction],
    dataset_path: str,
    model: str,
) -> None:
    """Save results to JSON file."""
    results: dict = {
        "model": model,
        "provider": "ollama",
        "ollama_url": OLLAMA_URL,
        "dataset_path": dataset_path,
        "total_samples": len(predictions),
        **metrics,
        "predictions": [
            {
                "index": p.index,
                "user_content": p.user_content,
                "predicted": p.predicted,
                "actual": p.actual,
                "correct": p.correct,
            }
            for p in predictions
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    serializable = _dataclass_to_dict(results)
    output_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")


def print_summary(console: Console, metrics: dict) -> None:
    """Print formatted summary."""
    console.print()
    console.rule("Summary")
    console.print(f"Accuracy:       [bold]{metrics['accuracy']:.4f}[/]")
    console.print(f"Macro F1:       [bold]{metrics['macro_avg'].f1:.4f}[/] "
                  f"(P={metrics['macro_avg'].precision:.4f}, R={metrics['macro_avg'].recall:.4f})")
    console.print(f"Weighted F1:    [bold]{metrics['weighted_avg'].f1:.4f}[/] "
                  f"(P={metrics['weighted_avg'].precision:.4f}, R={metrics['weighted_avg'].recall:.4f})")
    console.print()
    console.print("[bold]Per-class:[/]")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Class")
    table.add_column("Precision", justify="right")
    table.add_column("Recall", justify="right")
    table.add_column("F1", justify="right")
    table.add_column("Support", justify="right")

    for label in LABELED_CATEGORIES:
        m = metrics["per_class"][label]
        table.add_row(label, f"{m.precision:.4f}", f"{m.recall:.4f}", f"{m.f1:.4f}", str(m.support))

    console.print(table)


# ─── Entry point ──────────────────────────────────────────────


def parse_args(args: list[str]) -> tuple[Path, str]:
    """Parse --eval-path and --model arguments."""
    eval_path: Path | None = None
    model: str | None = None
    for i, arg in enumerate(args):
        if arg == "--eval-path" and i + 1 < len(args):
            eval_path = Path(args[i + 1])
        elif arg == "--model" and i + 1 < len(args):
            model = args[i + 1]
    return (
        eval_path or Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl",
        model or MODEL_NAME,
    )


def check_ollama(model: str) -> None:
    """Verify Ollama is running and model is available."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        resp.raise_for_status()
    except requests.ConnectionError:
        raise EnvironmentError(
            f"Cannot connect to Ollama at {OLLAMA_URL}. "
            "Start it with: ollama serve"
        )
    except requests.HTTPError:
        raise EnvironmentError(
            f"Ollama at {OLLAMA_URL} returned an error. "
            "Is it running? (ollama serve)"
        )

    available = [m["name"] for m in resp.json().get("models", [])]
    if model not in available:
        raise EnvironmentError(
            f"Model '{model}' not found in Ollama. "
            f"Available: {available}. "
            f"Pull it with: ollama pull {model}"
        )


def main() -> int:
    """Run baseline evaluation of a local Ollama model on the sentiment classification dataset."""
    args = sys.argv[1:]
    eval_path, model = parse_args(args)
    output_path = Path(__file__).resolve().parent / "baseline_results.json"
    console = Console()

    console.rule(f"Baseline Evaluation — {model} (Ollama)")
    console.print(f"Ollama URL:   {OLLAMA_URL}")
    console.print(f"Eval dataset: {eval_path}")
    console.print(f"Output:       {output_path}")

    # Load
    if not eval_path.exists():
        console.print(f"[red]Error: eval file not found: {eval_path}[/]")
        return 1

    examples = load_examples(eval_path)
    console.print(f"Loaded {len(examples)} examples")

    # Check Ollama
    try:
        check_ollama(model)
        console.print(f"[green]✓[/] Ollama running, model '{model}' available")
    except EnvironmentError as e:
        console.print(f"[red]Error: {e}[/]")
        return 1

    # Run
    console.print("\n[bold]Running inference...[/]")
    start = time.perf_counter()
    predictions = run_evaluation(examples, model)
    elapsed = time.perf_counter() - start
    console.print(f"\nCompleted in {elapsed:.1f}s ({elapsed / len(predictions):.2f}s per sample)")

    # Metrics
    metrics = compute_metrics(predictions)
    print_confusion_matrix(metrics["confusion_matrix"], LABELED_CATEGORIES, console)
    print_summary(console, metrics)

    # Classification report
    console.print()
    console.print(metrics["classification_report"])

    # Print misclassifications
    wrong = [p for p in predictions if not p.correct]
    if wrong:
        console.rule(f"Misclassifications ({len(wrong)})")
        for p in wrong:
            console.print(
                f"  [red]#{p.index + 1}[/] pred=[bold]{p.predicted}[/] "
                f"gold=[bold]{p.actual}[/] "
                f'— "{p.user_content[:80]}…"'
                if len(p.user_content) > 80
                else f'— "{p.user_content}"'
            )

    # Save
    save_results(output_path, metrics, predictions, str(eval_path), model)
    console.print(f"\n[green]✓[/] Results saved to [bold]{output_path}[/]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
