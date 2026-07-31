#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
#     "rich",
#     "scikit-learn",
#     "aiohttp",
# ]
# ///

"""
Confidence Evaluator - Integration wrapper over baseline with 3 confidence approaches.

This module provides evaluate_with_confidence() function that runs baseline classification
plus three confidence evaluation approaches:
1. Self-check: Model explains its own answer
2. Redundancy: 3 parallel requests with majority vote
3. Constraint: Validate answer against allowed categories

Usage:
    uv run confidence_evaluator.py --eval-path finetune/dataset/eval.jsonl --confidence
    uv run confidence_evaluator.py --eval-path finetune/dataset/eval.jsonl  # without confidence
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
from rich.table import Table

# Import confidence evaluators from tasks 1-3
# Use relative imports for same-package modules
from self_check import self_check
from redundancy_check import redundancy_check
from constraint_check import constraint_check, LABELED_CATEGORIES

# ─── Constants ────────────────────────────────────────────────

SYSTEM_PROMPT: Final[str] = (
    "Ты — классификатор тональности отзывов. Определи категорию отзыва.\n"
    "Категории: крайне негативный, негативный, нейтральный, позитивный.\n"
    "Отвечай только названием категории."
)

MODEL_NAME: Final[str] = "qwen3:14b"
OLLAMA_URL: Final[str] = "http://localhost:11434"

# ─── Data models ──────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ConfidencePrediction:
    """Single evaluation prediction with confidence data."""

    index: int
    user_content: str
    predicted: str
    actual: str
    correct: bool
    confidence_status: str  # "HIGH", "MEDIUM", "LOW"
    explanation: str  # From self_check
    redundancy_votes: dict  # From redundancy_check
    constraint_passed: bool  # From constraint_check
    latency_ms: int  # Total latency for this prediction


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


def evaluate_with_confidence(
    user_content: str,
    model: str = "qwen3:14b",
    use_confidence: bool = True,
) -> dict:
    """
    Run baseline classification plus three confidence evaluation approaches.

    This function:
    1. Runs baseline classification (classify user content)
    2. Runs self-check (model explains its answer)
    3. Runs redundancy check (3 parallel requests, majority vote)
    4. Runs constraint check (validate answer against allowed categories)
    5. Combines all results into a single dict

    Args:
        user_content: The review text to classify
        model: Ollama model name (default: "qwen3:14b")
        use_confidence: Whether to run confidence evaluators (default: True)

    Returns:
        Dictionary with keys:
        - answer (str): Baseline classification result
        - confidence_status (str): "HIGH", "MEDIUM", or "LOW"
        - explanation (str): Model's explanation from self_check
        - redundancy_votes (dict): Vote counts from redundancy_check
        - constraint_passed (bool): Whether answer passed constraint check
        - latency_ms (int): Total latency in milliseconds

    Example:
        >>> result = evaluate_with_confidence(
        ...     "Отличная тачка для дачи",
        ...     model="qwen3:14b",
        ...     use_confidence=True
        ... )
        >>> print(result["answer"])
        "позитивный"
        >>> print(result["confidence_status"])
        "HIGH"
    """
    start_time = time.perf_counter()

    # Step 1: Baseline classification
    try:
        answer = classify(user_content, SYSTEM_PROMPT, model)
    except requests.ConnectionError:
        raise EnvironmentError(
            f"Cannot connect to Ollama at {OLLAMA_URL}. "
            "Start it with: ollama serve"
        )
    except requests.HTTPError as e:
        raise EnvironmentError(
            f"Ollama API error: {e}. "
            "Is Ollama running? (ollama serve)"
        )

    # If confidence evaluation is disabled, return baseline result only
    if not use_confidence:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "answer": answer,
            "confidence_status": "UNKNOWN",
            "explanation": "",
            "redundancy_votes": {},
            "constraint_passed": True,
            "latency_ms": latency_ms,
        }

    # Step 2: Self-check (model explains its answer)
    try:
        self_check_result = self_check(user_content, answer, model)
        explanation = self_check_result["explanation"]
        self_check_latency = self_check_result["latency_ms"]
    except Exception as e:
        explanation = f"Error in self-check: {str(e)}"
        self_check_latency = 0

    # Step 3: Redundancy check (3 parallel requests, majority vote)
    try:
        redundancy_result = redundancy_check(user_content, model, n_requests=3)
        redundancy_votes = redundancy_result["votes"]
        redundancy_consensus = redundancy_result["consensus"]
        redundancy_status = redundancy_result["status"]
        redundancy_latency = redundancy_result["latency_ms"]
    except Exception as e:
        redundancy_votes = {}
        redundancy_consensus = None
        redundancy_status = "ERROR"
        redundancy_latency = 0

    # Step 4: Constraint check (validate answer against allowed categories)
    constraint_result = constraint_check(answer, LABELED_CATEGORIES)
    constraint_passed = constraint_result["passed"]

    # Step 5: Compute overall confidence status
    # HIGH: constraint passed + redundancy consensus + consensus matches baseline
    # MEDIUM: constraint passed but no consensus OR consensus differs from baseline
    # LOW: constraint failed
    if not constraint_passed:
        confidence_status = "LOW"
    elif redundancy_status == "OK" and redundancy_consensus == answer:
        confidence_status = "HIGH"
    else:
        confidence_status = "MEDIUM"

    # Total latency
    latency_ms = int((time.perf_counter() - start_time) * 1000)

    return {
        "answer": answer,
        "confidence_status": confidence_status,
        "explanation": explanation,
        "redundancy_votes": redundancy_votes,
        "constraint_passed": constraint_passed,
        "latency_ms": latency_ms,
    }


def run_evaluation_with_confidence(
    examples: list[dict],
    model: str,
    use_confidence: bool = True,
) -> list[ConfidencePrediction]:
    """Run evaluation with confidence on all examples. Returns list of predictions."""
    console = Console()
    predictions: list[ConfidencePrediction] = []

    for i, example in enumerate(examples):
        _system, user_content, actual = extract_fields(example)

        try:
            result = evaluate_with_confidence(user_content, model, use_confidence)
            predicted = result["answer"]
            # Normalize before comparison (strip, lowercase, remove trailing punctuation)
            def _normalize(s: str) -> str:
                return s.strip().lower().rstrip(".,!?;:")
            correct = _normalize(predicted) == _normalize(actual)
            confidence_status = result["confidence_status"]
            explanation = result["explanation"]
            redundancy_votes = result["redundancy_votes"]
            constraint_passed = result["constraint_passed"]
            latency_ms = result["latency_ms"]
        except EnvironmentError as e:
            console.print(f"[red]Error on example #{i + 1}: {e}[/]")
            # Create a failed prediction
            predicted = "ERROR"
            correct = False
            confidence_status = "ERROR"
            explanation = str(e)
            redundancy_votes = {}
            constraint_passed = False
            latency_ms = 0

        console.print(f"[{'green' if correct else 'red'}]#{i + 1:2d} "
                      f"[{'✓' if correct else '✗'}][/] "
                      f"Predicted: [bold]{predicted}[/] | "
                      f"Actual: [bold]{actual}[/] | "
                      f"Confidence: [bold]{confidence_status}[/]")

        predictions.append(
            ConfidencePrediction(
                index=i,
                user_content=user_content,
                predicted=predicted,
                actual=actual,
                correct=correct,
                confidence_status=confidence_status,
                explanation=explanation,
                redundancy_votes=redundancy_votes,
                constraint_passed=constraint_passed,
                latency_ms=latency_ms,
            )
        )

    return predictions


def compute_metrics(predictions: list[ConfidencePrediction]) -> dict:
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

    # Normalize for consistent metric computation (same as prediction-level check)
    def _normalize(s: str) -> str:
        return s.strip().lower().rstrip(".,!?;:")
    y_true = [_normalize(p.actual) for p in predictions]
    y_pred = [_normalize(p.predicted) for p in predictions]

    # Handle OOV predictions — treat as mismatches only, metrics use known labels
    known_labels = [_normalize(c) for c in LABELED_CATEGORIES]
    mask = [y in known_labels for y in y_pred]
    y_pred_clean = [
        p if m else "unknown" for p, m in zip(y_pred, mask)
    ]

    acc = accuracy_score(y_true, y_pred_clean)

    # Per-class metrics
    per_class: dict[str, dict] = {}
    for label in known_labels:
        labels = [label, "unknown"]
        p = precision_score(y_true, y_pred_clean, labels=labels, zero_division=0, average=None)[0]
        r = recall_score(y_true, y_pred_clean, labels=labels, zero_division=0, average=None)[0]
        f = f1_score(y_true, y_pred_clean, labels=labels, zero_division=0, average=None)[0]
        support = sum(1 for y in y_true if y == label)
        per_class[label] = {
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f, 4),
            "support": support,
        }

    macro_f1 = f1_score(y_true, y_pred_clean, labels=known_labels, average="macro", zero_division=0)
    macro_p = precision_score(y_true, y_pred_clean, labels=known_labels, average="macro", zero_division=0)
    macro_r = recall_score(y_true, y_pred_clean, labels=known_labels, average="macro", zero_division=0)
    macro_support = len(predictions)

    weight_f1 = f1_score(y_true, y_pred_clean, labels=known_labels, average="weighted", zero_division=0)
    weight_p = precision_score(y_true, y_pred_clean, labels=known_labels, average="weighted", zero_division=0)
    weight_r = recall_score(y_true, y_pred_clean, labels=known_labels, average="weighted", zero_division=0)

    cm = confusion_matrix(y_true, y_pred_clean, labels=known_labels)
    cm_list = cm.tolist()

    report_text = classification_report(
        y_true, y_pred_clean, labels=known_labels, zero_division=0
    )

    # Confidence statistics
    confidence_counts = {}
    for p in predictions:
        conf = p.confidence_status
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

    # Accuracy by confidence level
    accuracy_by_confidence = {}
    for conf_level in ["HIGH", "MEDIUM", "LOW", "ERROR"]:
        conf_preds = [p for p in predictions if p.confidence_status == conf_level]
        if conf_preds:
            correct_count = sum(1 for p in conf_preds if p.correct)
            accuracy_by_confidence[conf_level] = round(correct_count / len(conf_preds), 4)
        else:
            accuracy_by_confidence[conf_level] = None

    return {
        "accuracy": round(acc, 4),
        "per_class": per_class,
        "macro_avg": {
            "precision": round(macro_p, 4),
            "recall": round(macro_r, 4),
            "f1": round(macro_f1, 4),
            "support": macro_support,
        },
        "weighted_avg": {
            "precision": round(weight_p, 4),
            "recall": round(weight_r, 4),
            "f1": round(weight_f1, 4),
            "support": macro_support,
        },
        "confusion_matrix": cm_list,
        "classification_report": report_text,
        "confidence_statistics": {
            "counts": confidence_counts,
            "accuracy_by_confidence": accuracy_by_confidence,
        },
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


def print_summary(console: Console, metrics: dict) -> None:
    """Print formatted summary with confidence statistics."""
    console.print()
    console.rule("Summary")
    console.print(f"Accuracy:       [bold]{metrics['accuracy']:.4f}[/]")
    console.print(f"Macro F1:       [bold]{metrics['macro_avg']['f1']:.4f}[/] "
                  f"(P={metrics['macro_avg']['precision']:.4f}, R={metrics['macro_avg']['recall']:.4f})")
    console.print(f"Weighted F1:    [bold]{metrics['weighted_avg']['f1']:.4f}[/] "
                  f"(P={metrics['weighted_avg']['precision']:.4f}, R={metrics['weighted_avg']['recall']:.4f})")
    console.print()

    # Confidence statistics
    console.print("[bold]Confidence Statistics:[/]")
    conf_stats = metrics["confidence_statistics"]
    console.print(f"  HIGH:   {conf_stats['counts'].get('HIGH', 0)} samples, "
                  f"accuracy: {conf_stats['accuracy_by_confidence'].get('HIGH', 'N/A')}")
    console.print(f"  MEDIUM: {conf_stats['counts'].get('MEDIUM', 0)} samples, "
                  f"accuracy: {conf_stats['accuracy_by_confidence'].get('MEDIUM', 'N/A')}")
    console.print(f"  LOW:    {conf_stats['counts'].get('LOW', 0)} samples, "
                  f"accuracy: {conf_stats['accuracy_by_confidence'].get('LOW', 'N/A')}")
    console.print()

    console.print("[bold]Per-class:[/]")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Class")
    table.add_column("Precision", justify="right")
    table.add_column("Recall", justify="right")
    table.add_column("F1", justify="right")
    table.add_column("Support", justify="right")

    for label in LABELED_CATEGORIES:
        m = metrics["per_class"][label.strip().lower().rstrip(".,!?;:")]
        table.add_row(label, f"{m['precision']:.4f}", f"{m['recall']:.4f}", f"{m['f1']:.4f}", str(m["support"]))

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
    predictions: list[ConfidencePrediction],
    dataset_path: str,
    model: str,
    use_confidence: bool,
) -> None:
    """Save results to JSON file."""
    results: dict = {
        "model": model,
        "provider": "ollama",
        "ollama_url": OLLAMA_URL,
        "dataset_path": dataset_path,
        "confidence_enabled": use_confidence,
        "total_samples": len(predictions),
        **metrics,
        "predictions": [
            {
                "index": p.index,
                "user_content": p.user_content,
                "predicted": p.predicted,
                "actual": p.actual,
                "correct": p.correct,
                "confidence_status": p.confidence_status,
                "explanation": p.explanation,
                "redundancy_votes": p.redundancy_votes,
                "constraint_passed": p.constraint_passed,
                "latency_ms": p.latency_ms,
            }
            for p in predictions
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    serializable = _dataclass_to_dict(results)
    output_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")


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


def parse_args(args: list[str]) -> tuple[Path, str, bool]:
    """Parse --eval-path, --model, and --confidence arguments."""
    eval_path: Path | None = None
    model: str | None = None
    use_confidence: bool = True  # Default: enabled

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--eval-path" and i + 1 < len(args):
            eval_path = Path(args[i + 1])
            i += 2
        elif arg == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 2
        elif arg == "--confidence":
            # Check if next arg is a boolean
            if i + 1 < len(args) and args[i + 1].lower() in ("true", "false"):
                use_confidence = args[i + 1].lower() == "true"
                i += 2
            else:
                # Flag without value means enable
                use_confidence = True
                i += 1
        elif arg == "--no-confidence":
            use_confidence = False
            i += 1
        else:
            i += 1

    return (
        eval_path or Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl",
        model or MODEL_NAME,
        use_confidence,
    )


def main() -> int:
    """Run confidence evaluation on a local Ollama model."""
    args = sys.argv[1:]
    eval_path, model, use_confidence = parse_args(args)
    output_path = Path(__file__).resolve().parent / "confidence_results.json"
    console = Console()

    mode_str = "with confidence" if use_confidence else "baseline only"
    console.rule(f"Confidence Evaluation — {model} (Ollama) {mode_str}")
    console.print(f"Ollama URL:   {OLLAMA_URL}")
    console.print(f"Eval dataset: {eval_path}")
    console.print(f"Output:       {output_path}")
    console.print(f"Confidence:   {'enabled' if use_confidence else 'disabled'}")

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
    console.print(f"\n[bold]Running inference {mode_str}...[/]")
    start = time.perf_counter()
    predictions = run_evaluation_with_confidence(examples, model, use_confidence)
    elapsed = time.perf_counter() - start
    console.print(f"\nCompleted in {elapsed:.1f}s ({elapsed / len(predictions):.2f}s per sample)")

    # Metrics
    metrics = compute_metrics(predictions)
    km_labels = [c.strip().lower().rstrip(".,!?;:") for c in LABELED_CATEGORIES]
    print_confusion_matrix(metrics["confusion_matrix"], km_labels, console)
    print_summary(console, metrics)

    # Classification report
    console.print()
    console.print(metrics["classification_report"])

    # misclassifications with confidence
    wrong = [p for p in predictions if not p.correct]
    if wrong:
        console.rule(f"Misclassifications ({len(wrong)})")
        for p in wrong:
            console.print(
                f"  [red]#{p.index + 1} ✗[/] "
                f"Predicted: [bold]{p.predicted}[/] | "
                f"Actual: [bold]{p.actual}[/] | "
                f"Confidence: [bold]{p.confidence_status}[/]"
            )
            snippet = p.user_content[:80] + "…" if len(p.user_content) > 80 else p.user_content
            console.print(f"    Input: \"{snippet}\"")

    # Save
    save_results(output_path, metrics, predictions, str(eval_path), model, use_confidence)
    console.print(f"\n[green]✓[/] Results saved to [bold]{output_path}[/]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())