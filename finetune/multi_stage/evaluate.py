#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "scikit-learn",
#     "rich",
#     "requests",
#     "python-dotenv",
# ]
# ///

"""
Multi-Stage Evaluation Script

Evaluates all 3 approaches (monolithic, local multi-stage, hybrid) on eval.jsonl
and outputs metrics to results.json.

Approaches:
1. Monolithic: Single LLM call (baseline from comparator.py)
2. Multi-Stage Local: 3-stage pipeline (pipeline.py)
3. Multi-Stage Hybrid: Ollama (stages 1-2) + GPUStack (stage 3) (hybrid_pipeline.py)

Metrics:
- Accuracy: Fraction of correct predictions
- Latency: Mock latency (ms) per approach
- Cost: Mock cost units per approach
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from rich.console import Console
from rich.table import Table
from sklearn.metrics import accuracy_score

from finetune.multi_stage.comparator import (
    LABELED_CATEGORIES,
    load_examples,
    extract_user_content,
    extract_actual_label,
    normalize_prediction,
    run_monolithic_prediction,
)
from finetune.multi_stage.pipeline import MultiStagePipeline
from finetune.multi_stage.hybrid_pipeline import run_hybrid, HybridPipeline

# ─── Constants ────────────────────────────────────────────────

# Mock latency constants (in milliseconds)
MONOLITHIC_LATENCY_MS: Final[float] = 1500.0  # Single LLM call
MULTI_STAGE_LOCAL_LATENCY_MS: Final[float] = 800.0  # 3 smaller stages (local)
MULTI_STAGE_HYBRID_LATENCY_MS: Final[float] = 2500.0  # Hybrid (includes cloud API call)

# Mock cost constants (in arbitrary units)
MONOLITHIC_COST: Final[float] = 1.0  # Single expensive call
MULTI_STAGE_LOCAL_COST: Final[float] = 0.6  # 3 cheaper calls (local)
MULTI_STAGE_HYBRID_COST: Final[float] = 1.2  # Hybrid (cloud API costs more)


# ─── Data models ──────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class EvaluationPrediction:
    """Single prediction result from an approach."""
    
    index: int
    predicted: str
    actual: str
    correct: bool
    latency_ms: float
    cost: float
    metadata: dict = field(default_factory=dict)


# ─── Evaluation functions ─────────────────────────────────────


def evaluate_monolithic(examples: list[dict]) -> list[EvaluationPrediction]:
    """
    Evaluate monolithic (single-request) approach on examples.
    
    Args:
        examples: List of examples from eval.jsonl format
    
    Returns:
        List of EvaluationPrediction objects
    """
    predictions: list[EvaluationPrediction] = []
    
    for idx, example in enumerate(examples):
        user_content = extract_user_content(example)
        actual = extract_actual_label(example)
        
        # Run monolithic prediction
        result = run_monolithic_prediction(user_content)
        predicted = normalize_prediction(result["predicted"])
        correct = predicted == actual
        
        predictions.append(EvaluationPrediction(
            index=idx,
            predicted=predicted,
            actual=actual,
            correct=correct,
            latency_ms=MONOLITHIC_LATENCY_MS,
            cost=MONOLITHIC_COST,
            metadata={"raw_predicted": result["predicted"]}
        ))
    
    return predictions


def evaluate_multi_stage_local(
    examples: list[dict],
    pipeline: MultiStagePipeline
) -> list[EvaluationPrediction]:
    """
    Evaluate local multi-stage pipeline approach on examples.
    
    Args:
        examples: List of examples from eval.jsonl format
        pipeline: MultiStagePipeline instance
    
    Returns:
        List of EvaluationPrediction objects
    """
    predictions: list[EvaluationPrediction] = []
    
    for idx, example in enumerate(examples):
        user_content = extract_user_content(example)
        actual = extract_actual_label(example)
        
        # Run multi-stage pipeline
        result = pipeline.run_pipeline(user_content)
        final_result = result.get("final_result", {})
        
        if "error" in final_result:
            predicted = "нейтральный"  # Default on error
            confidence = 0.0
        else:
            predicted = normalize_prediction(final_result.get("category", "нейтральный"))
            confidence = final_result.get("confidence", 0.0)
        
        correct = predicted == actual
        
        predictions.append(EvaluationPrediction(
            index=idx,
            predicted=predicted,
            actual=actual,
            correct=correct,
            latency_ms=MULTI_STAGE_LOCAL_LATENCY_MS,
            cost=MULTI_STAGE_LOCAL_COST,
            metadata={
                "confidence": confidence,
                "stages": {
                    "stage1": "success" if result.get("stage1") else "failed",
                    "stage2": "success" if result.get("stage2") else "failed",
                    "stage3": "success" if result.get("stage3") else "failed",
                }
            }
        ))
    
    return predictions


def evaluate_multi_stage_hybrid(
    examples: list[dict],
    pipeline: HybridPipeline | None = None
) -> list[EvaluationPrediction]:
    """
    Evaluate hybrid multi-stage approach on examples.
    
    Args:
        examples: List of examples from eval.jsonl format
        pipeline: Optional HybridPipeline instance (creates new if None)
    
    Returns:
        List of EvaluationPrediction objects
    """
    predictions: list[EvaluationPrediction] = []
    
    if pipeline is None:
        pipeline = HybridPipeline()
    
    for idx, example in enumerate(examples):
        user_content = extract_user_content(example)
        actual = extract_actual_label(example)
        
        # Run hybrid pipeline
        result = pipeline.run_hybrid(user_content)
        final_result = result.get("final_result", {})
        
        if "error" in final_result:
            predicted = "нейтральный"  # Default on error
            confidence = 0.0
            error_msg = final_result.get("error", "Unknown error")
        else:
            predicted = normalize_prediction(final_result.get("category", "нейтральный"))
            confidence = final_result.get("confidence", 0.)
            error_msg = None
        
        correct = predicted == actual
        
        predictions.append(EvaluationPrediction(
            index=idx,
            predicted=predicted,
            actual=actual,
            correct=correct,
            latency_ms=MULTI_STAGE_HYBRID_LATENCY_MS,
            cost=MULTI_STAGE_HYBRID_COST,
            metadata={
                "confidence": confidence,
                "error": error_msg,
                "sources": result.get("sources", {}),
                "stages": {
                    "stage1": "success" if result.get("stage1") else "failed",
                    "stage2": "success" if result.get("stage2") else "failed",
                    "stage3": "success" if result.get("stage3") else "failed",
                }
            }
        ))
    
    return predictions


# ─── Metrics computation ──────────────────────────────────────


def compute_metrics(predictions: list[EvaluationPrediction]) -> dict[str, Any]:
    """
    Compute aggregate metrics from predictions.
    
    Args:
        predictions: List of EvaluationPrediction objects
    
    Returns:
        dict with accuracy, avg_latency_ms, total_cost, and predictions list
    """
    if not predictions:
        return {
            "accuracy": 0.0,
            "avg_latency_ms": 0.0,
            "total_cost": 0.0,
            "predictions": []
        }
    
    correct = sum(1 for p in predictions if p.correct)
    accuracy = correct / len(predictions)
    
    avg_latency = sum(p.latency_ms for p in predictions) / len(predictions)
    total_cost = sum(p.cost for p in predictions)
    
    return {
        "accuracy": round(accuracy, 4),
        "avg_latency_ms": round(avg_latency, 2),
        "total_cost": round(total_cost, 2),
        "predictions": [
            {
                "index": p.index,
                "predicted": p.predicted,
                "actual": p.actual,
                "correct": p.correct,
                "latency_ms": p.latency_ms,
                "cost": p.cost,
                "metadata": p.metadata
            }
            for p in predictions
        ]
    }


# ─── Main evaluation orchestration ────────────────────────────


def run_full_evaluation(
    eval_path: Path | None = None,
    output_path: Path | None = None
) -> dict[str, Any]:
    """
    Run full evaluation on all 3 approaches.
    
    Args:
        eval_path: Path to eval.jsonl (default: finetune/dataset/eval.jsonl)
        output_path: Path to save results (default: finetune/multi_stage/results.json)
    
    Returns:
        dict with structure:
        {
            "monolithic": {...},
            "multi_stage_local": {...},
            "multi_stage_hybrid": {...},
            "comparison": {...}
        }
    """
    # Resolve paths
    if eval_path is None:
        eval_path = Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl"
    
    if output_path is None:
        output_path = Path(__file__).resolve().parent / "results.json"
    
    # Load examples
    examples = load_examples(eval_path)
    
    # Initialize pipelines
    local_pipeline = MultiStagePipeline()
    hybrid_pipeline = HybridPipeline()
    
    # Run evaluations
    mono_preds = evaluate_monolithic(examples)
    local_preds = evaluate_multi_stage_local(examples, local_pipeline)
    hybrid_preds = evaluate_multi_stage_hybrid(examples, hybrid_pipeline)
    
    # Compute metrics
    mono_metrics = compute_metrics(mono_preds)
    local_metrics = compute_metrics(local_preds)
    hybrid_metrics = compute_metrics(hybrid_preds)
    
    # Build comparison
    comparison = {
        "accuracy_winner": max(
            [("monolithic", mono_metrics["accuracy"]),
             ("multi_stage_local", local_metrics["accuracy"]),
             ("multi_stage_hybrid", hybrid_metrics["accuracy"])],
            key=lambda x: x[1]
        )[0],
        "latency_winner": min(
            [("monolithic", mono_metrics["avg_latency_ms"]),
             ("multi_stage_local", local_metrics["avg_latency_ms"]),
             ("multi_stage_hybrid", hybrid_metrics["avg_latency_ms"])],
            key=lambda x: x[1]
        )[0],
        "cost_winner": min(
            [("monolithic", mono_metrics["total_cost"]),
             ("multi_stage_local", local_metrics["total_cost"]),
             ("multi_stage_hybrid", hybrid_metrics["total_cost"])],
            key=lambda x: x[1]
        )[0],
        "total_examples": len(examples),
        "agreement_rate": _compute_agreement_rate(mono_preds, local_preds, hybrid_preds)
    }
    
    results = {
        "monolithic": mono_metrics,
        "multi_stage_local": local_metrics,
        "multi_stage_hybrid": hybrid_metrics,
        "comparison": comparison
    }
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    return results


def _compute_agreement_rate(
    mono: list[EvaluationPrediction],
    local: list[EvaluationPrediction],
    hybrid: list[EvaluationPrediction]
) -> dict[str, float]:
    """Compute agreement rates between approaches."""
    if not mono:
        return {"mono_local": 0.0, "mono_hybrid": 0.0, "local_hybrid": 0.0}
    
    mono_local = sum(1 for m, l in zip(mono, local) if m.predicted == l.predicted) / len(mono)
    mono_hybrid = sum(1 for m, h in zip(mono, hybrid) if m.predicted == h.predicted) / len(mono)
    local_hybrid = sum(1 for l, h in zip(local, hybrid) if l.predicted == h.predicted) / len(local)
    
    return {
        "mono_local": round(mono_local, 4),
        "mono_hybrid": round(mono_hybrid, 4),
        "local_hybrid": round(local_hybrid, 4)
    }


# ─── Console output ───────────────────────────────────────────


def print_evaluation_summary(console: Console, results: dict[str, Any]) -> None:
    """Print evaluation results summary to console."""
    console.rule("Evaluation Results Summary")
    
    table = Table(title="Approach Comparison", show_header=True, header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Monolithic", justify="right")
    table.add_column("Multi-Stage Local", justify="right")
    table.add_column("Multi-Stage Hybrid", justify="right")
    
    table.add_row(
        "Accuracy",
        f"{results['monolithic']['accuracy']:.4f}",
        f"{results['multi_stage_local']['accuracy']:.4f}",
        f"{results['multi_stage_hybrid']['accuracy']:.4f}",
    )
    table.add_row(
        "Avg Latency (ms)",
        f"{results['monolithic']['avg_latency_ms']:.2f}",
        f"{results['multi_stage_local']['avg_latency_ms']:.2f}",
        f"{results['multi_stage_hybrid']['avg_latency_ms']:.2f}",
    )
    table.add_row(
        "Total Cost",
        f"{results['monolithic']['total_cost']:.2f}",
        f"{results['multi_stage_local']['total_cost']:.2f}",
        f"{results['multi_stage_hybrid']['total_cost']:.2f}",
    )
    
    console.print(table)
    
    # Print comparison
    comp = results["comparison"]
    console.print(f"\n[bold]Comparison:[/]")
    console.print(f"  Accuracy winner:  [green]{comp['accuracy_winner']}[/]")
    console.print(f"  Latency winner:   [green]{comp['latency_winner']}[/]")
    console.print(f"  Cost winner:      [green]{comp['cost_winner']}[/]")
    console.print(f"  Total examples:   {comp['total_examples']}")
    console.print(f"\n  Agreement rates:")
    console.print(f"    Mono ↔ Local:   {comp['agreement_rate']['mono_local']:.2%}")
    console.print(f"    Mono ↔ Hybrid:  {comp['agreement_rate']['mono_hybrid']:.2%}")
    console.print(f"    Local ↔ Hybrid: {comp['agreement_rate']['local_hybrid']:.2%}")


# ─── Entry point ──────────────────────────────────────────────


def main() -> int:
    """Run multi-stage evaluation on all 3 approaches."""
    args = sys.argv[1:]
    
    # Parse arguments (simple --eval-path and --output-path)
    eval_path = Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl"
    output_path = Path(__file__).resolve().parent / "results.json"
    
    i = 0
    while i < len(args):
        if args[i] == "--eval-path" and i + 1 < len(args):
            eval_path = Path(args[i + 1])
            i += 2
        elif args[i] == "--output-path" and i + 1 < len(args):
            output_path = Path(args[i + 1])
            i += 2
        else:
            i += 1
    
    console = Console()
    console.rule("Multi-Stage Evaluation")
    console.print(f"Eval dataset: {eval_path}")
    console.print(f"Output path:  {output_path}")
    
    # Check eval file exists
    if not eval_path.exists():
        console.print(f"[red]Error: eval file not found: {eval_path}[/]")
        return 1
    
    # Load and report
    examples = load_examples(eval_path)
    console.print(f"Loaded {len(examples)} examples")
    
    # Run evaluation
    console.print(f"\n[bold]Running evaluation on all 3 approaches...[/]")
    start = time.perf_counter()
    
    try:
        results = run_full_evaluation(eval_path, output_path)
    except Exception as e:
        console.print(f"[red]Error during evaluation: {e}[/]")
        return 1
    
    elapsed = time.perf_counter() - start
    console.print(f"\nCompleted in {elapsed:.1f}s")
    
    # Print summary
    print_evaluation_summary(console, results)
    
    # Save confirmation
    console.print(f"\n[green][/] Results saved to [bold]{output_path}[/]")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())