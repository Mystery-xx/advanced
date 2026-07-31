#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
#     "rich",
#     "scikit-learn",
# ]
# ///

"""
Model Routing Evaluation Script.

This script evaluates confidence-based model routing on an evaluation dataset.
It routes requests between cheap and expensive models based on confidence scores,
then computes routing metrics (escalation rate, cost savings, latency stats).

Usage:
    uv run run_routing.py --eval-path finetune/dataset/eval.jsonl
    uv run run_routing.py --eval-path finetune/dataset/eval.jsonl --cheap-model llama3.1:8b --expensive-model qwen3:14b
    uv run run_routing.py --eval-path finetune/dataset/eval.jsonl --escalate-on LOW --output /tmp/results.json
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import requests
from rich.console import Console
from sklearn.metrics import classification_report, confusion_matrix

from finetune.routing.model_router import (
    RouterConfig,
    RouterResult,
    route_request,
    load_examples,
    extract_fields,
    COST_UNITS,
)
from finetune.confidence.constraint_check import LABELED_CATEGORIES

# ─── Constants ────────────────────────────────────────────────

DEFAULT_OUTPUT_PATH: Final[Path] = Path(__file__).resolve().parent / "routing_results.json"


# ─── Data models ──────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class RoutingPrediction:
    """Prediction result with ground truth for accuracy computation."""

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


# ─── Evaluation logic ─────────────────────────────────────────


def run_routing_evaluation(
    examples: list[dict],
    config: RouterConfig,
    console: Console,
) -> list[RoutingPrediction]:
    """
    Run routing evaluation on all examples.

    Args:
        examples: List of evaluation examples from JSONL
        config: RouterConfig with routing parameters
        console: Rich console for output

    Returns:
        List of RoutingPrediction objects for each example
    """
    predictions: list[RoutingPrediction] = []

    for i, example in enumerate(examples):
        _system, user_content, actual = extract_fields(example)

        try:
            result = route_request(user_content, config)
            # Normalize before comparison
            def _normalize(s: str) -> str:
                return s.strip().lower().rstrip(".,!?;:")

            correct = _normalize(result.answer) == _normalize(actual)

            status_icon = "✓" if correct else "✗"
            escalation_marker = " [yellow](escalated)[/]" if result.escalated else ""
            console.print(
                f"[{'green' if correct else 'red'}]#{i + 1:2d} {status_icon}[/] "
                f"Model: [bold]{result.model_used}[/]{escalation_marker} | "
                f"Answer: [bold]{result.answer}[/] | "
                f"Actual: [bold]{actual}[/] | "
                f"Confidence: [bold]{result.confidence_status}[/]"
            )

            prediction = RoutingPrediction(
                index=i,
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
        except EnvironmentError as e:
            console.print(f"[red]Error on example #{i + 1}: {e}[/]")
            prediction = RoutingPrediction(
                index=i,
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
                explanation=str(e),
            )

        predictions.append(prediction)

    return predictions


def compute_routing_metrics(predictions: list[RoutingPrediction]) -> dict:
    """
    Compute routing metrics from evaluation predictions.

    Returns dict with:
    - total_samples: Number of samples evaluated
    - accuracy: Overall accuracy
    - escalation_rate: Fraction of requests escalated
    - cheap_only_rate: Fraction handled by cheap model only
    - avg_latency_ms: Average latency across all requests
    - avg_cost_units: Average cost units spent
    - confidence_distribution: Count of HIGH/MEDIUM/LOW confidence results
    - accuracy_by_model: Accuracy for cheap vs expensive model
    - cost_savings_vs_expensive_only: Relative cost savings compared to using expensive for all
    - confusion_matrix: 4x4 confusion matrix
    - classification_report: sklearn classification report string
    """
    total = len(predictions)
    if total == 0:
        return {
            "total_samples": 0,
            "accuracy": 0.0,
            "escalation_rate": 0.0,
            "cheap_only_rate": 0.0,
            "avg_latency_ms": 0.0,
            "avg_cost_units": 0.0,
            "confidence_distribution": {},
            "accuracy_by_model": {},
            "cost_savings_vs_expensive_only": 0.0,
            "confusion_matrix": [],
            "classification_report": "",
        }

    # Basic counts
    correct_count = sum(1 for p in predictions if p.correct)
    escalated_count = sum(1 for p in predictions if p.escalated)
    cheap_only_count = total - escalated_count

    # Latency and cost
    total_latency = sum(p.latency_ms for p in predictions)
    total_cost = sum(p.cost_units for p in predictions)

    # Confidence distribution
    confidence_counts: dict[str, int] = {}
    for p in predictions:
        conf = p.confidence_status
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

    # Accuracy by model used
    cheap_predictions = [p for p in predictions if p.model_used.endswith("8b") or "llama" in p.model_used.lower()]
    expensive_predictions = [p for p in predictions if p.model_used.endswith("14b") or "qwen" in p.model_used.lower()]

    accuracy_by_model: dict[str, float] = {}
    if cheap_predictions:
        cheap_correct = sum(1 for p in cheap_predictions if p.correct)
        accuracy_by_model["cheap"] = round(cheap_correct / len(cheap_predictions), 4)
    if expensive_predictions:
        expensive_correct = sum(1 for p in expensive_predictions if p.correct)
        accuracy_by_model["expensive"] = round(expensive_correct / len(expensive_predictions), 4)

    # Cost savings: compare to using expensive model for everything
    cost_if_all_expensive = total * COST_UNITS["expensive"]
    cost_savings = cost_if_all_expensive - total_cost
    cost_savings_percent = round((cost_savings / cost_if_all_expensive) * 100, 2) if cost_if_all_expensive > 0 else 0.0

    # Confusion matrix and classification report
    labels = [c.strip().lower().rstrip(".,!?;:") for c in LABELED_CATEGORIES]
    y_true = [p.actual.strip().lower().rstrip(".,!?;:") for p in predictions]
    y_pred = [p.predicted.strip().lower().rstrip(".,!?;:") for p in predictions]

    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()
    cr = classification_report(y_true, y_pred, target_names=labels, zero_division=0)

    return {
        "total_samples": total,
        "accuracy": round(correct_count / total, 4),
        "escalation_rate": round(escalated_count / total, 4),
        "cheap_only_rate": round(cheap_only_count / total, 4),
        "avg_latency_ms": round(total_latency / total, 2),
        "avg_cost_units": round(total_cost / total, 2),
        "confidence_distribution": confidence_counts,
        "accuracy_by_model": accuracy_by_model,
        "cost_savings_vs_expensive_only": cost_savings_percent,
        "confusion_matrix": cm,
        "classification_report": cr,
    }


def print_routing_summary(console: Console, metrics: dict) -> None:
    """Print formatted routing summary with all metrics."""
    console.print()
    console.rule("Routing Summary")

    # Core metrics
    console.print(f"[bold]Total samples:[/]     {metrics['total_samples']}")
    console.print(f"[bold]Accuracy:[/]          {metrics['accuracy']:.2%}")
    console.print(f"[bold]Escalation rate:[/]   {metrics['escalation_rate']:.2%}")
    console.print(f"[bold]Cheap-only rate:[/]   {metrics['cheap_only_rate']:.2%}")
    console.print()

    # Performance metrics
    console.print(f"[bold]Avg latency:[/]       {metrics['avg_latency_ms']:.1f} ms")
    console.print(f"[bold]Avg cost units:[/]    {metrics['avg_cost_units']:.2f}")
    console.print(f"[bold]Cost savings:[/]      {metrics['cost_savings_vs_expensive_only']:.1f}% vs expensive-only")
    console.print()

    # Confidence distribution
    console.print("[bold]Confidence Distribution:[/]")
    conf_dist = metrics["confidence_distribution"]
    for level in ["HIGH", "MEDIUM", "LOW", "ERROR"]:
        count = conf_dist.get(level, 0)
        console.print(f"  {level:6s}: {count}")
    console.print()

    # Accuracy by model
    console.print("[bold]Accuracy by Model:[/]")
    acc_by_model = metrics["accuracy_by_model"]
    console.print(f"  Cheap model:     {acc_by_model.get('cheap', 'N/A')}")
    console.print(f"  Expensive model: {acc_by_model.get('expensive', 'N/A')}")


def save_routing_results(
    output_path: Path,
    metrics: dict,
    predictions: list[RoutingPrediction],
    dataset_path: str,
    config: RouterConfig,
) -> None:
    """Save routing results to JSON file with nested statistics objects."""

    def _dataclass_to_dict(obj: object) -> object:
        """Convert dataclass instances to plain dicts for JSON."""
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

    total = len(predictions)
    escalated_count = sum(1 for p in predictions if p.escalated)
    cheap_count = total - escalated_count
    escalation_rate = round(escalated_count / total, 4) if total > 0 else 0.0
    cheap_pct = round(cheap_count / total * 100, 2) if total > 0 else 0.0
    expensive_pct = round(escalated_count / total * 100, 2) if total > 0 else 0.0

    latencies = [p.latency_ms for p in predictions]
    avg_latency = round(sum(latencies) / total, 2) if total > 0 else 0.0
    min_latency = min(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0

    costs = [p.cost_units for p in predictions]
    total_cost = sum(costs)
    avg_cost = round(total_cost / total, 2) if total > 0 else 0.0
    cost_if_all_expensive = total * COST_UNITS["expensive"]
    cost_savings = round(
        ((cost_if_all_expensive - total_cost) / cost_if_all_expensive) * 100, 2
    ) if cost_if_all_expensive > 0 else 0.0

    results_dict = {
        "config": {
            "cheap_model": config.cheap_model,
            "expensive_model": config.expensive_model,
            "escalate_on": config.escalate_on,
            "use_self_check": config.use_self_check,
            "ollama_url": config.ollama_url,
        },
        "dataset_path": dataset_path,
        "routing_statistics": {
            "total_examples": total,
            "cheap_model_count": cheap_count,
            "expensive_model_count": escalated_count,
            "escalation_rate": escalation_rate,
            "cheap_percentage": cheap_pct,
            "expensive_percentage": expensive_pct,
        },
        "latency_statistics": {
            "avg_latency_ms": avg_latency,
            "min_latency_ms": min_latency,
            "max_latency_ms": max_latency,
        },
        "cost_statistics": {
            "total_cost_units": total_cost,
            "avg_cost_per_request": avg_cost,
            "cost_savings_vs_all_expensive": cost_savings,
        },
        "confidence_distribution": metrics.get("confidence_distribution", {}),
        "accuracy": metrics.get("accuracy", 0.0),
        "cheap_only_rate": metrics.get("cheap_only_rate", 0.0),
        "avg_cost_units": metrics.get("avg_cost_units", 0.0),
        "accuracy_by_model": metrics.get("accuracy_by_model", {}),
        "confusion_matrix": metrics.get("confusion_matrix", []),
        "classification_report": metrics.get("classification_report", ""),
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
    serializable = _dataclass_to_dict(results_dict)
    output_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")


def check_ollama(config: RouterConfig) -> None:
    """Verify Ollama is running and both models are available."""
    try:
        resp = requests.get(f"{config.ollama_url}/api/tags", timeout=10)
        resp.raise_for_status()
    except requests.ConnectionError:
        raise EnvironmentError(
            f"Cannot connect to Ollama at {config.ollama_url}. "
            "Start it with: ollama serve"
        )
    except requests.HTTPError:
        raise EnvironmentError(
            f"Ollama at {config.ollama_url} returned an error. "
            "Is it running? (ollama serve)"
        )

    available = [m["name"] for m in resp.json().get("models", [])]
    for model in [config.cheap_model, config.expensive_model]:
        if model not in available:
            raise EnvironmentError(
                f"Model '{model}' not found in Ollama. "
                f"Available: {available}. "
                f"Pull it with: ollama pull {model}"
            )


def parse_args(args: list[str]) -> tuple[Path, RouterConfig, Path]:
    """
    Parse command-line arguments.

    Returns:
        Tuple of (eval_path, config, output_path)
    """
    eval_path: Path | None = None
    cheap_model: str = "llama3.1:8b"
    expensive_model: str = "qwen3:14b"
    escalate_on: list[str] = ["MEDIUM", "LOW"]
    use_self_check: bool = True
    ollama_url: str = "http://localhost:11434"
    output_path: Path | None = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--eval-path" and i + 1 < len(args):
            eval_path = Path(args[i + 1])
            i += 2
        elif arg == "--cheap-model" and i + 1 < len(args):
            cheap_model = args[i + 1]
            i += 2
        elif arg == "--expensive-model" and i + 1 < len(args):
            expensive_model = args[i + 1]
            i += 2
        elif arg == "--escalate-on" and i + 1 < len(args):
            # Parse comma-separated list
            escalate_on = [s.strip() for s in args[i + 1].split(",")]
            i += 2
        elif arg == "--ollama-url" and i + 1 < len(args):
            ollama_url = args[i + 1]
            i += 2
        elif arg == "--no-self-check":
            use_self_check = False
            i += 1
        elif arg == "--output" and i + 1 < len(args):
            output_path = Path(args[i + 1])
            i += 2
        else:
            i += 1

    config = RouterConfig(
        cheap_model=cheap_model,
        expensive_model=expensive_model,
        escalate_on=escalate_on,
        use_self_check=use_self_check,
        ollama_url=ollama_url,
    )

    return (
        eval_path or Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl",
        config,
        output_path or DEFAULT_OUTPUT_PATH,
    )


def main() -> int:
    """Run model routing evaluation on eval dataset."""
    args = sys.argv[1:]
    eval_path, config, output_path = parse_args(args)
    console = Console()

    console.rule("Model Routing Evaluation")
    console.print(f"Ollama URL:      {config.ollama_url}")
    console.print(f"Cheap model:     [bold]{config.cheap_model}[/]")
    console.print(f"Expensive model: [bold]{config.expensive_model}[/]")
    console.print(f"Escalate on:     {', '.join(config.escalate_on)}")
    console.print(f"Use self-check:  {config.use_self_check}")
    console.print(f"Eval dataset:    {eval_path}")
    console.print(f"Output:          {output_path}")

    # Load
    if not eval_path.exists():
        console.print(f"[red]Error: eval file not found: {eval_path}[/]")
        return 1

    examples = load_examples(eval_path)
    console.print(f"Loaded {len(examples)} examples")

    # Check Ollama
    try:
        check_ollama(config)
        console.print(f"[green]✓[/] Ollama running, models available")
    except EnvironmentError as e:
        console.print(f"[red]Error: {e}[/]")
        return 1

    # Run
    console.print(f"\n[bold]Running routing evaluation...[/]")
    start = time.perf_counter()
    predictions = run_routing_evaluation(examples, config, console)
    elapsed = time.perf_counter() - start
    console.print(f"\nCompleted in {elapsed:.1f}s ({elapsed / len(predictions):.2f}s per sample)")

    # Metrics
    metrics = compute_routing_metrics(predictions)
    print_routing_summary(console, metrics)

    # Classification report
    console.print()
    console.print("[bold]Classification Report:[/]")
    console.print(metrics["classification_report"])

    # Print misclassifications
    wrong = [p for p in predictions if not p.correct]
    if wrong:
        console.rule(f"Misclassifications ({len(wrong)})")
        for p in wrong:
            escalation_note = " [yellow](escalated)[/]" if p.escalated else ""
            console.print(
                f"  [red]#{p.index + 1} ✗[/] "
                f"Predicted: [bold]{p.predicted}[/] | "
                f"Actual: [bold]{p.actual}[/] | "
                f"Model: [bold]{p.model_used}[/]{escalation_note} | "
                f"Confidence: [bold]{p.confidence_status}[/]"
            )
            snippet = p.user_content[:80] + "…" if len(p.user_content) > 80 else p.user_content
            console.print(f"    Input: \"{snippet}\"")

    # Save
    save_routing_results(output_path, metrics, predictions, str(eval_path), config)
    console.print(f"\n[green]✓[/] Results saved to [bold]{output_path}[/]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())