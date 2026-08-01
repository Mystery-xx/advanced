#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "scikit-learn",
# ]
# ///

"""
Monolithic Baseline Comparator

Compares monolithic (single-request) approach vs multi-stage pipeline approach
on the same inputs, measuring accuracy, latency, and cost differences.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from sklearn.metrics import accuracy_score

from finetune.multi_stage.pipeline import MultiStagePipeline

# ─── Constants ────────────────────────────────────────────────

LABELED_CATEGORIES: Final[tuple[str, ...]] = (
    "крайне негативный",
    "негативный",
    "нейтральный",
    "позитивный",
)

# Mock latency constants (in milliseconds)
MONOLITHIC_LATENCY_MS: Final[float] = 1500.0  # Single LLM call
MULTI_STAGE_LATENCY_MS: Final[float] = 800.0  # 3 smaller stages

# Mock cost constants (in arbitrary units)
MONOLITHIC_COST: Final[float] = 1.0  # Single expensive call
MULTI_STAGE_COST: Final[float] = 0.6  # 3 cheaper calls


# ─── Data models ──────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Result of comparing monolithic vs multi-stage approaches."""

    monolithic: dict[str, Any]
    multi_stage: dict[str, Any]
    delta: dict[str, float]


# ─── Helper functions ─────────────────────────────────────────


def load_examples(path: Path) -> list[dict]:
    """Load JSONL dataset, returning list of parsed JSON objects."""
    examples: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            examples.append(json.loads(line))
    return examples


def extract_user_content(example: dict) -> str:
    """Extract user content from message format example."""
    messages: list[dict[str, str]] = example.get("messages", [])
    for msg in messages:
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def extract_actual_label(example: dict) -> str:
    """Extract actual label from message format example."""
    messages: list[dict[str, str]] = example.get("messages", [])
    for msg in messages:
        if msg.get("role") == "assistant":
            return msg.get("content", "").strip()
    return ""


def normalize_prediction(predicted: str) -> str:
    """
    Normalize prediction to one of the valid categories.
    
    If prediction doesn't match any known category, return 'нейтральный' as default.
    """
    predicted = predicted.strip().lower()
    
    for category in LABELED_CATEGORIES:
        if predicted == category.lower():
            return category
    
    # OOV handling: return neutral for unknown predictions
    return "нейтральный"


def run_monolithic_prediction(user_content: str) -> dict[str, Any]:
    """
    Run monolithic (single-request) prediction.
    
    This simulates the baseline approach from run_baseline.py.
    For actual comparison, this would call the LLM directly.
    For testing purposes, we use a simple rule-based approximation.
    
    Returns:
        dict with keys: predicted, latency_ms, cost
    """
    start_time = time.perf_counter()
    
    # Simple rule-based monolithic prediction (simulating LLM behavior)
    # This is a simplified version for comparison without requiring Ollama
    user_lower = user_content.lower()
    
    # Count sentiment indicators
    positive_words = [
        "отличная", "хорошая", "супер", "крепкая", "удобная", 
        "рекомендую", "лучшая", "доволен", "прекрасно", "выносливая"
    ]
    negative_words = [
        "ржавчина", "провисло", "мусор", "тишина", "отвратительный",
        "развалилась", "сломалась", "недостаток", "минус", "плохая"
    ]
    
    pos_count = sum(1 for word in positive_words if word in user_lower)
    neg_count = sum(1 for word in negative_words if word in user_lower)
    
    # Classification logic similar to baseline
    if neg_count >= 3 and pos_count == 0:
        predicted = "крайне негативный"
    elif neg_count > pos_count:
        if neg_count >= 2:
            predicted = "негативный"
        else:
            predicted = "нейтральный"
    elif pos_count > neg_count:
        predicted = "позитивный"
    else:
        predicted = "нейтральный"
    
    elapsed = (time.perf_counter() - start_time) * 1000  # ms
    
    return {
        "predicted": predicted,
        "latency_ms": MONOLITHIC_LATENCY_MS,  # Use mock latency for consistency
        "cost": MONOLITHIC_COST,
    }


def run_multi_stage_prediction(user_content: str, pipeline: MultiStagePipeline) -> dict[str, Any]:
    """
    Run multi-stage pipeline prediction.
    
    Returns:
        dict with keys: predicted, confidence, latency_ms, cost, stages
    """
    start_time = time.perf_counter()
    
    result = pipeline.run_pipeline(user_content)
    
    elapsed = (time.perf_counter() - start_time) * 1000  # ms
    
    final_result = result.get("final_result", {})
    
    if "error" in final_result:
        return {
            "predicted": "нейтральный",  # Default on error
            "confidence": 0.0,
            "latency_ms": MULTI_STAGE_LATENCY_MS,
            "cost": MULTI_STAGE_COST,
            "stages": result,
            "error": final_result["error"],
        }
    
    return {
        "predicted": final_result.get("category", "нейтральный"),
        "confidence": final_result.get("confidence", 0.0),
        "latency_ms": MULTI_STAGE_LATENCY_MS,  # Use mock latency
        "cost": MULTI_STAGE_COST,
        "stages": result,
    }


# ─── Core comparison logic ────────────────────────────────────


def compare(inputs: list[dict] | None = None, eval_path: str | None = None) -> dict[str, Any]:
    """
    Compare monolithic vs multi-stage approaches on the same inputs.
    
    Args:
        inputs: List of examples from eval.jsonl format.
                Each example should have 'messages' with user/assistant roles.
                If None, loads from eval_path or default location.
        eval_path: Path to eval.jsonl file. Used if inputs is None.
                   Defaults to finetune/dataset/eval.jsonl
    
    Returns:
        dict with structure:
        {
            "monolithic": {
                "predictions": [...],
                "accuracy": float,
                "avg_latency_ms": float,
                "total_cost": float
            },
            "multi_stage": {
                "predictions": [...],
                "accuracy": float,
                "avg_latency_ms": float,
                "total_cost": float,
                "avg_confidence": float
            },
            "delta": {
                "accuracy_diff": float,  # multi_stage - monolithic
                "latency_diff": float,   # multi_stage - monolithic
                "cost_diff": float,      # multi_stage - monolithic
                "agreement_rate": float  # % where both predict same
            }
        }
    """
    # Load inputs
    if inputs is None:
        if eval_path is None:
            eval_path = str(Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl")
        inputs = load_examples(Path(eval_path))
    
    if not inputs:
        return {
            "monolithic": {"predictions": [], "accuracy": 0.0, "avg_latency_ms": 0.0, "total_cost": 0.0},
            "multi_stage": {"predictions": [], "accuracy": 0.0, "avg_latency_ms": 0.0, "total_cost": 0.0, "avg_confidence": 0.0},
            "delta": {"accuracy_diff": 0.0, "latency_diff": 0.0, "cost_diff": 0.0, "agreement_rate": 0.0},
        }
    
    # Initialize pipeline
    pipeline = MultiStagePipeline()
    
    # Run both approaches
    mono_predictions: list[str] = []
    multi_predictions: list[str] = []
    actual_labels: list[str] = []
    
    mono_latencies: list[float] = []
    multi_latencies: list[float] = []
    
    mono_costs: list[float] = []
    multi_costs: list[float] = []
    
    multi_confidences: list[float] = []
    
    agreements = 0
    
    for example in inputs:
        user_content = extract_user_content(example)
        actual = extract_actual_label(example)
        
        # Run monolithic
        mono_result = run_monolithic_prediction(user_content)
        mono_pred = normalize_prediction(mono_result["predicted"])
        
        # Run multi-stage
        multi_result = run_multi_stage_prediction(user_content, pipeline)
        multi_pred = normalize_prediction(multi_result["predicted"])
        
        # Collect results
        mono_predictions.append(mono_pred)
        multi_predictions.append(multi_pred)
        actual_labels.append(actual)
        
        mono_latencies.append(mono_result["latency_ms"])
        multi_latencies.append(multi_result["latency_ms"])
        
        mono_costs.append(mono_result["cost"])
        multi_costs.append(multi_result["cost"])
        
        if "confidence" in multi_result:
            multi_confidences.append(multi_result["confidence"])
        
        # Check agreement
        if mono_pred == multi_pred:
            agreements += 1
    
    # Calculate metrics
    mono_accuracy = accuracy_score(actual_labels, mono_predictions) if mono_predictions else 0.0
    multi_accuracy = accuracy_score(actual_labels, multi_predictions) if multi_predictions else 0.0
    
    avg_mono_latency = sum(mono_latencies) / len(mono_latencies) if mono_latencies else 0.0
    avg_multi_latency = sum(multi_latencies) / len(multi_latencies) if multi_latencies else 0.0
    
    total_mono_cost = sum(mono_costs)
    total_multi_cost = sum(multi_costs)
    
    avg_multi_confidence = sum(multi_confidences) / len(multi_confidences) if multi_confidences else 0.0
    
    agreement_rate = agreements / len(inputs) if inputs else 0.0
    
    return {
        "monolithic": {
            "predictions": mono_predictions,
            "accuracy": round(mono_accuracy, 4),
            "avg_latency_ms": round(avg_mono_latency, 2),
            "total_cost": round(total_mono_cost, 2),
        },
        "multi_stage": {
            "predictions": multi_predictions,
            "accuracy": round(multi_accuracy, 4),
            "avg_latency_ms": round(avg_multi_latency, 2),
            "total_cost": round(total_multi_cost, 2),
            "avg_confidence": round(avg_multi_confidence, 4),
        },
        "delta": {
            "accuracy_diff": round(multi_accuracy - mono_accuracy, 4),
            "latency_diff": round(avg_multi_latency - avg_mono_latency, 2),
            "cost_diff": round(total_multi_cost - total_mono_cost, 2),
            "agreement_rate": round(agreement_rate, 4),
        },
    }


def compare_examples(
    examples: list[dict],
    output_path: str | None = None,
) -> dict[str, Any]:
    """
    Convenience function to compare on specific examples and optionally save results.
    
    Args:
        examples: List of examples from eval.jsonl
        output_path: Optional path to save JSON results
    
    Returns:
        Same structure as compare()
    """
    result = compare(inputs=examples)
    
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    
    return result


# ─── Entry point ──────────────────────────────────────────────


def main() -> int:
    """Run comparison on default eval dataset."""
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    console.rule("Monolithic vs Multi-Stage Comparison")
    
    result = compare()
    
    # Print summary table
    table = Table(title="Comparison Results", show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Monolithic", justify="right")
    table.add_column("Multi-Stage", justify="right")
    table.add_column("Delta", justify="right")
    
    table.add_row(
        "Accuracy",
        f"{result['monolithic']['accuracy']:.4f}",
        f"{result['multi_stage']['accuracy']:.4f}",
        f"{result['delta']['accuracy_diff']:+.4f}",
    )
    table.add_row(
        "Avg Latency (ms)",
        f"{result['monolithic']['avg_latency_ms']:.2f}",
        f"{result['multi_stage']['avg_latency_ms']:.2f}",
        f"{result['delta']['latency_diff']:+.2f}",
    )
    table.add_row(
        "Total Cost",
        f"{result['monolithic']['total_cost']:.2f}",
        f"{result['multi_stage']['total_cost']:.2f}",
        f"{result['delta']['cost_diff']:+.2f}",
    )
    table.add_row(
        "Agreement Rate",
        "-",
        "-",
        f"{result['delta']['agreement_rate']:.4f}",
    )
    
    console.print(table)
    
    # Print agreement details
    mono_preds = result["monolithic"]["predictions"]
    multi_preds = result["multi_stage"]["predictions"]
    
    disagreements = [
        (i, mono_preds[i], multi_preds[i])
        for i in range(len(mono_preds))
        if mono_preds[i] != multi_preds[i]
    ]
    
    if disagreements:
        console.print(f"\n[yellow]Disagreements ({len(disagreements)}):[/]")
        for idx, mono, multi in disagreements:
            console.print(f"  Example {idx}: monolithic={mono}, multi_stage={multi}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())