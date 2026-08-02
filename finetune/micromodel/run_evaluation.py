#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "scikit-learn",
#     "rich",
#     "requests",
#     "matplotlib",
#     "seaborn",
# ]
# ///
"""
Micro-Model Router Evaluation Script.

Evaluates the confidence-based micro-model router (with LLM fallback)
on the combined eval + edge_cases dataset. Tracks per-query routing
metadata and computes overall/system-level metrics.

Usage:
    uv run run_evaluation.py
    uv run run_evaluation.py --confidence-threshold 0.8
    uv run run_evaluation.py --output /tmp/micromodel_results.json
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

# Add project root to Python path for imports
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import requests
from rich.console import Console
from rich.table import Table
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

from finetune.micromodel.micromodel_router import (
    MicroModelConfig,
    RouterResult,
    route_with_fallback,
)
from finetune.confidence.constraint_check import LABELED_CATEGORIES

# ─── Constants ────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent
DATASET_DIR: Final[Path] = HERE.parent / "dataset"
EVAL_PATH: Final[Path] = DATASET_DIR / "eval.jsonl"
EDGE_CASES_PATH: Final[Path] = DATASET_DIR / "edge_cases.jsonl"
DEFAULT_OUTPUT_PATH: Final[Path] = HERE / "micromodel_results.json"

# Cost model (task spec)
# Micro-model: 0 cost units (CPU-only, <10ms)
# LLM (qwen3:14b): 1.0 cost unit (~1500ms)
COST_MICROMODEL: Final[float] = 0.0
COST_LLM: Final[float] = 1.0

# ─── Data models ──────────────────────────────────────────────


@dataclass
class EvalPrediction:
    """Prediction result with ground truth and routing metadata."""

    index: int
    user_content: str
    predicted: str
    actual: str
    correct: bool
    model_used: str
    confidence_status: str
    escalated: bool
    cheap_answer: str
    cheap_confidence: str
    latency_ms: int
    cost_units: int
    explanation: str


@dataclass
class EvalMetrics:
    """Aggregated evaluation metrics."""

    total_samples: int
    overall_accuracy: float
    micromodel_accuracy: float
    llm_accuracy: float
    fallback_rate: float
    avg_latency_ms: float
    cost_savings: float
    per_class_metrics: dict
    confusion_matrix: list[list[int]]
    classification_report: str


# ─── Helpers ──────────────────────────────────────────────────


def load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL dataset file."""
    examples: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            examples.append(json.loads(line))
    return examples


def extract_fields(example: dict) -> tuple[str, str]:
    """Extract user content and actual label from a message-format example.

    Returns:
        Tuple of (user_content, actual_label).
    """
    messages: list[dict[str, str]] = example["messages"]
    user = ""
    assistant = ""
    for msg in messages:
        match msg["role"]:
            case "user":
                user = msg["content"]
            case "assistant":
                assistant = msg["content"]
            case _:
                pass
    return user, assistant


def normalize(s: str) -> str:
    """Normalize a classification label for comparison."""
    return s.strip().lower().rstrip(".,!?;:")


def compute_cost_savings(
    predictions: list[EvalPrediction],
) -> float:
    """Compute cost savings vs using LLM for all queries.

    Uses the task-specified cost model:
        micro-model: 0 cost units
        LLM:         1.0 cost unit

    Cost savings = (total_if_all_LLM - actual_cost) / total_if_all_LLM
    """
    total = len(predictions)
    if total == 0:
        return 0.0

    actual_cost = 0.0
    for p in predictions:
        if p.escalated or "qwen" in p.model_used.lower():
            actual_cost += COST_LLM
        else:
            actual_cost += COST_MICROMODEL

    cost_if_all_llm = total * COST_LLM
    savings = (cost_if_all_llm - actual_cost) / cost_if_all_llm
    return round(savings, 4)


# ─── Evaluation logic ─────────────────────────────────────────


def run_evaluation(
    examples: list[dict],
    config: MicroModelConfig,
    console: Console,
    start_index: int = 0,
) -> list[EvalPrediction]:
    """Run micro-model router evaluation on all examples.

    Args:
        examples: List of evaluation examples (message-format dicts).
        config: MicroModelConfig for the router.
        console: Rich console for live output.
        start_index: Global index offset (used when combining datasets).

    Returns:
        List of EvalPrediction objects.
    """
    predictions: list[EvalPrediction] = []

    for i, example in enumerate(examples):
        global_idx = start_index + i
        user_content, actual = extract_fields(example)

        try:
            result: RouterResult = route_with_fallback(user_content, config)
        except Exception as exc:
            # If route_with_fallback itself raises (shouldn't, but be safe)
            console.print(f"[red]#{global_idx + 1:2d} ERROR — {exc}[/]")
            predictions.append(
                EvalPrediction(
                    index=global_idx,
                    user_content=user_content,
                    predicted="ERROR",
                    actual=actual,
                    correct=False,
                    model_used="",
                    confidence_status="ERROR",
                    escalated=False,
                    cheap_answer="",
                    cheap_confidence="ERROR",
                    latency_ms=0,
                    cost_units=0,
                    explanation=str(exc),
                )
            )
            continue

        # Handle error status from the router itself
        if result.answer == "ERROR":
            correct = False
        else:
            correct = normalize(result.answer) == normalize(actual)

        status_icon = "✓" if correct else "✗"
        escalation_marker = " [yellow](escalated)[/]" if result.escalated else ""

        # Determine if LLM was actually used
        is_llm = result.escalated or ("qwen" in result.model_used.lower())

        console.print(
            f"[{'green' if correct else 'red'}]#{global_idx + 1:2d} {status_icon}[/]"
            f" Model: [bold]{result.model_used}[/]{escalation_marker} |"
            f" Answer: [bold]{result.answer}[/] |"
            f" Actual: [bold]{actual}[/] |"
            f" Confidence: [bold]{result.confidence_status}[/] |"
            f" Latency: {result.latency_ms}ms |"
            f" Cost: {result.cost_units}"
        )

        predictions.append(
            EvalPrediction(
                index=global_idx,
                user_content=user_content,
                predicted=result.answer,
                actual=actual,
                correct=correct,
                model_used=result.model_used,
                confidence_status=result.confidence_status,
                escalated=result.escalated,
                cheap_answer=result.cheap_answer,
                cheap_confidence=result.cheap_confidence,
                latency_ms=result.latency_ms,
                cost_units=result.cost_units,
                explanation=result.explanation,
            )
        )

    return predictions


# ─── Metrics computation ──────────────────────────────────────


def compute_metrics(predictions: list[EvalPrediction]) -> EvalMetrics:
    """Compute all evaluation metrics from predictions."""
    total = len(predictions)
    if total == 0:
        return EvalMetrics(
            total_samples=0,
            overall_accuracy=0.0,
            micromodel_accuracy=0.0,
            llm_accuracy=0.0,
            fallback_rate=0.0,
            avg_latency_ms=0.0,
            cost_savings=0.0,
            per_class_metrics={},
            confusion_matrix=[],
            classification_report="",
        )

    # Overall accuracy
    correct_count = sum(1 for p in predictions if p.correct)
    overall_accuracy = round(correct_count / total, 4)

    # Split by model used
    micromodel_preds = [p for p in predictions if not p.escalated and p.model_used == "micromodel"]
    llm_preds = [p for p in predictions if p.escalated or "qwen" in p.model_used.lower()]

    micromodel_accuracy = round(
        sum(1 for p in micromodel_preds if p.correct) / len(micromodel_preds), 4
    ) if micromodel_preds else 0.0

    llm_accuracy = round(
        sum(1 for p in llm_preds if p.correct) / len(llm_preds), 4
    ) if llm_preds else 0.0

    # Fallback rate: fraction that went to LLM
    fallback_count = len(llm_preds)
    fallback_rate = round(fallback_count / total, 4)

    # Average latency
    total_latency = sum(p.latency_ms for p in predictions)
    avg_latency_ms = round(total_latency / total, 1)

    # Cost savings
    cost_savings = compute_cost_savings(predictions)

    # Per-class metrics via sklearn
    known_labels = list(LABELED_CATEGORIES)

    # Map predictions to known labels (unknown -> "unknown")
    y_true = [normalize(p.actual) for p in predictions]
    y_pred = [
        normalize(p.predicted) if normalize(p.predicted) in known_labels else "unknown"
        for p in predictions
    ]

    # Per-class precision/recall/f1
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=known_labels, zero_division=0
    )

    per_class: dict[str, dict] = {}
    for i, label in enumerate(known_labels):
        per_class[label] = {
            "precision": round(float(precision[i]), 4),
            "recall": round(float(recall[i]), 4),
            "f1": round(float(f1[i]), 4),
            "support": int(support[i]),
        }

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=known_labels)
    cm_list = cm.tolist()

    # Classification report text
    cr_text = classification_report(
        y_true, y_pred, labels=known_labels, target_names=known_labels, zero_division=0
    )

    return EvalMetrics(
        total_samples=total,
        overall_accuracy=overall_accuracy,
        micromodel_accuracy=micromodel_accuracy,
        llm_accuracy=llm_accuracy,
        fallback_rate=fallback_rate,
        avg_latency_ms=avg_latency_ms,
        cost_savings=cost_savings,
        per_class_metrics=per_class,
        confusion_matrix=cm_list,
        classification_report=cr_text,
    )


# ─── Output helpers ───────────────────────────────────────────


def print_confusion_matrix(cm: list[list[int]], labels: list[str], console: Console) -> None:
    """Print confusion matrix as a rich table."""
    table = Table(title="Confusion Matrix", show_header=True, header_style="bold magenta")
    table.add_column("Actual ↘ Pred →", style="dim")
    for label in labels:
        table.add_column(label, justify="right")

    for i, label in enumerate(labels):
        row = [label]
        for val in cm[i]:
            row.append(str(val))
        table.add_row(*row)

    console.print(table)


def print_metrics_summary(console: Console, metrics: EvalMetrics) -> None:
    """Print a summary table of all metrics."""
    console.print()
    console.rule("Evaluation Summary")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Total samples", str(metrics.total_samples))
    table.add_row("Overall accuracy", f"{metrics.overall_accuracy:.2%}")
    table.add_row("Micro-model accuracy", f"{metrics.micromodel_accuracy:.2%}")
    table.add_row("LLM accuracy", f"{metrics.llm_accuracy:.2%}")
    table.add_row("Fallback rate", f"{metrics.fallback_rate:.2%}")
    table.add_row("Avg latency", f"{metrics.avg_latency_ms:.1f} ms")
    table.add_row("Cost savings", f"{metrics.cost_savings:.2%}")

    console.print(table)

    # Per-class metrics
    console.print()
    console.print("[bold]Per-class Metrics:[/]")
    pc_table = Table(show_header=True, header_style="bold green")
    pc_table.add_column("Class")
    pc_table.add_column("Precision", justify="right")
    pc_table.add_column("Recall", justify="right")
    pc_table.add_column("F1", justify="right")
    pc_table.add_column("Support", justify="right")

    for label in LABELED_CATEGORIES:
        m = metrics.per_class_metrics.get(label, {})
        pc_table.add_row(
            label,
            f"{m.get('precision', 0):.4f}",
            f"{m.get('recall', 0):.4f}",
            f"{m.get('f1', 0):.4f}",
            str(m.get('support', 0)),
        )
    console.print(pc_table)


def save_results(
    output_path: Path,
    metrics: EvalMetrics,
    predictions: list[EvalPrediction],
    eval_path: str,
    edge_path: str,
    config: MicroModelConfig,
) -> None:
    """Save full evaluation results to a JSON file."""
    results: dict = {
        "total_samples": metrics.total_samples,
        "overall_accuracy": metrics.overall_accuracy,
        "micromodel_accuracy": metrics.micromodel_accuracy,
        "llm_accuracy": metrics.llm_accuracy,
        "fallback_rate": metrics.fallback_rate,
        "avg_latency_ms": metrics.avg_latency_ms,
        "cost_savings": metrics.cost_savings,
        "per_class_metrics": metrics.per_class_metrics,
        "confusion_matrix": metrics.confusion_matrix,
        "classification_report": metrics.classification_report,
        "config": {
            "confidence_threshold": config.confidence_threshold,
            "llm_model": config.llm_model,
            "ollama_url": config.ollama_url,
        },
        "datasets": {
            "eval": eval_path,
            "edge_cases": edge_path,
        },
        "predictions": [
            {
                "index": p.index,
                "user_content": p.user_content,
                "predicted": p.predicted,
                "actual": p.actual,
                "correct": p.correct,
                "model_used": p.model_used,
                "confidence_status": p.confidence_status,
                "escalated": p.escalated,
                "cheap_answer": p.cheap_answer,
                "cheap_confidence": p.cheap_confidence,
                "latency_ms": p.latency_ms,
                "cost_units": p.cost_units,
                "explanation": p.explanation,
            }
            for p in predictions
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def plot_confusion_matrix(
    cm: list[list[int]],
    labels: list[str],
    output_path: Path,
) -> None:
    """Generate and save a confusion matrix heatmap using matplotlib/seaborn."""
    import seaborn as sns

    matplotlib.use("Agg")
    plt.rcParams.update({"figure.autolayout": True})

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        np.array(cm),
        annot=True,
        fmt="d",
        xticklabels=labels,
        yticklabels=labels,
        cmap="Blues",
        cbar=True,
        square=True,
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix — Micro-Model Router Evaluation")

    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def print_wrong_predictions(
    predictions: list[EvalPrediction],
    console: Console,
) -> None:
    """Print all misclassifications with details."""
    wrong = [p for p in predictions if not p.correct]
    if not wrong:
        return

    console.print()
    console.rule(f"Misclassifications ({len(wrong)})")
    for p in wrong:
        escalation_note = " [yellow](escalated)[/]" if p.escalated else ""
        console.print(
            f"  [red]#{p.index + 1} ✗[/]"
            f" Predicted: [bold]{p.predicted}[/] |"
            f" Actual: [bold]{p.actual}[/] |"
            f" Model: [bold]{p.model_used}[/]{escalation_note} |"
            f" Confidence: [bold]{p.confidence_status}[/]"
        )
        snippet = p.user_content[:100] + "…" if len(p.user_content) > 100 else p.user_content
        console.print(f'    Input: "{snippet}"')


def check_ollama(url: str) -> None:
    """Verify Ollama is running and the default model is available."""
    try:
        resp = requests.get(f"{url}/api/tags", timeout=10)
        resp.raise_for_status()
    except requests.ConnectionError:
        raise EnvironmentError(
            f"Cannot connect to Ollama at {url}. "
            "Start it with: ollama serve"
        )
    except requests.HTTPError:
        raise EnvironmentError(
            f"Ollama at {url} returned an error. Is it running? (ollama serve)"
        )

    # Not strictly required to have the model pre-loaded (Ollama pulls on demand),
    # but we check as a courtesy.
    available = [m["name"] for m in resp.json().get("models", [])]
    console = Console()
    if len(available) == 0:
        console.print("[yellow]⚠ No models found in Ollama. LLM fallback will fail.[/]")
    else:
        console.print(f"[green]✓[/] Ollama running. Available models: {', '.join(available[:5])}")


# ─── Entry point ──────────────────────────────────────────────


def parse_args(args: list[str]) -> tuple[float, Path]:
    """Parse command-line arguments."""
    threshold: float = 0.75
    output_path: Path = DEFAULT_OUTPUT_PATH

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--confidence-threshold" and i + 1 < len(args):
            threshold = float(args[i + 1])
            i += 2
        elif arg == "--output" and i + 1 < len(args):
            output_path = Path(args[i + 1])
            i += 2
        else:
            i += 1

    return threshold, output_path


def main() -> int:
    """Run micro-model router evaluation on eval + edge_cases datasets."""
    args = sys.argv[1:]
    confidence_threshold, output_path = parse_args(args)
    console = Console()

    config = MicroModelConfig(confidence_threshold=confidence_threshold)

    console.rule("Micro-Model Router Evaluation")
    console.print(f"Confidence threshold: {config.confidence_threshold}")
    console.print(f"LLM model:           {config.llm_model}")
    console.print(f"Ollama URL:          {config.ollama_url}")
    console.print(f"Eval dataset:        {EVAL_PATH}")
    console.print(f"Edge cases dataset:  {EDGE_CASES_PATH}")
    console.print(f"Output:              {output_path}")

    # ── Check Ollama ──────────────────────────────────────────
    try:
        check_ollama(config.ollama_url)
    except EnvironmentError as e:
        console.print(f"[red]Error: {e}[/]")
        console.print("[yellow]Continuing anyway — micro-model (CPU) will work, "
                       "but LLM fallback will fail for low-confidence queries.[/]")

    # ── Load datasets ─────────────────────────────────────────
    if not EVAL_PATH.exists():
        console.print(f"[red]Error: eval file not found: {EVAL_PATH}[/]")
        return 1
    if not EDGE_CASES_PATH.exists():
        console.print(f"[red]Error: edge cases file not found: {EDGE_CASES_PATH}[/]")
        return 1

    eval_examples = load_jsonl(EVAL_PATH)
    edge_examples = load_jsonl(EDGE_CASES_PATH)

    all_examples = eval_examples + edge_examples
    total = len(all_examples)
    console.print(f"\nLoaded {len(eval_examples)} eval + {len(edge_examples)} edge cases = {total} total")

    # ── Run evaluation ────────────────────────────────────────
    console.print(f"\n[bold]Running evaluation (threshold={config.confidence_threshold})...[/]")
    start_time = time.perf_counter()

    predictions = run_evaluation(eval_examples, config, console, start_index=0)
    predictions += run_evaluation(edge_examples, config, console, start_index=len(eval_examples))

    elapsed = time.perf_counter() - start_time
    console.print(f"\nCompleted in {elapsed:.1f}s ({elapsed / total:.2f}s per sample)")

    # ── Compute metrics ───────────────────────────────────────
    metrics = compute_metrics(predictions)
    print_confusion_matrix(metrics.confusion_matrix, list(LABELED_CATEGORIES), console)
    print_metrics_summary(console, metrics)

    # ── Classification report ──────────────────────────────────
    console.print()
    console.print("[bold]Classification Report:[/]")
    console.print(metrics.classification_report)

    # ── Misclassifications ────────────────────────────────────
    print_wrong_predictions(predictions, console)

    # ── Save results ──────────────────────────────────────────
    save_results(
        output_path,
        metrics,
        predictions,
        str(EVAL_PATH),
        str(EDGE_CASES_PATH),
        config,
    )
    console.print(f"\n[green]✓[/] Results saved to [bold]{output_path}[/]")

    # ── Confusion matrix plot ─────────────────────────────────
    cm_plot_path = output_path.with_suffix(".png")
    try:
        plot_confusion_matrix(metrics.confusion_matrix, list(LABELED_CATEGORIES), cm_plot_path)
        console.print(f"[green]✓[/] Confusion matrix plot saved to [bold]{cm_plot_path}[/]")
    except Exception as exc:
        console.print(f"[yellow]⚠ Could not generate confusion matrix plot: {exc}[/]")

    # ── Target check ──────────────────────────────────────────
    console.print()
    console.rule("Target Metrics Check")
    targets = [
        ("Fallback rate < 40%", metrics.fallback_rate < 0.4, f"{metrics.fallback_rate:.1%}"),
        ("Overall accuracy > 75%", metrics.overall_accuracy > 0.75, f"{metrics.overall_accuracy:.1%}"),
        ("Avg latency < 50ms", metrics.avg_latency_ms < 50, f"{metrics.avg_latency_ms:.1f}ms"),
        ("Cost savings > 50%", metrics.cost_savings > 0.5, f"{metrics.cost_savings:.1%}"),
    ]
    for name, passed, value in targets:
        icon = "[green]✓ PASS[/]" if passed else "[red]✗ FAIL[/]"
        console.print(f"  {icon} | {name}: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
