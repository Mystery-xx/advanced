#!/usr/bin/env python3
"""
Metrics Visualization for Multi-Stage Inference

Generates comparison charts (accuracy vs latency vs cost) for all 3 approaches:
1. Monolithic (single-request baseline)
2. Multi-Stage Local (all 3 stages on Ollama qwen3:14b)
3. Multi-Stage Hybrid (stages 1-2 local, stage 3 on GPUStack qwen3.6-27b)

Output: PNG charts in finetune/multi_stage/charts/
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

import matplotlib.pyplot as plt
import numpy as np

# ─── Constants ────────────────────────────────────────────────

CHARTS_DIR: Final[Path] = Path(__file__).parent / "charts"
RESULTS_FILE: Final[Path] = Path(__file__).parent / "results.json"

APPROACHES: Final[list[str]] = [
    "Monolithic",
    "Multi-Stage\n(Local)",
    "Multi-Stage\n(Hybrid)",
]

APPROACH_KEYS: Final[list[str]] = ["monolithic", "multi_stage_local", "multi_stage_hybrid"]

COLORS: Final[list[str]] = ["#3498db", "#2ecc71", "#e74c3c"]

METRICS: Final[dict[str, str]] = {
    "accuracy": "Accuracy",
    "avg_latency_ms": "Avg Latency (ms)",
    "total_cost": "Total Cost",
}

# ─── Helper functions ─────────────────────────────────────────


def load_results(results_path: Path | None = None) -> dict[str, Any]:
    """
    Load results from JSON file.

    Args:
        results_path: Path to results.json (default: finetune/multi_stage/results.json)

    Returns:
        dict with structure:
        {
            "monolithic": {"accuracy": float, "avg_latency_ms": float, "total_cost": float},
            "multi_stage_local": {...},
            "multi_stage_hybrid": {...}
        }

    Raises:
        FileNotFoundError: If results file doesn't exist
        json.JSONDecodeError: If results file is invalid JSON
    """
    path = results_path or RESULTS_FILE

    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")

    content = path.read_text(encoding="utf-8")
    return json.loads(content)


def ensure_charts_dir(charts_dir: Path | None = None) -> Path:
    """
    Ensure charts directory exists.

    Args:
        charts_dir: Custom directory path (default: finetune/multi_stage/charts)

    Returns:
        Path to charts directory
    """
    dir_path = charts_dir or CHARTS_DIR
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def extract_metrics(results: dict[str, Any]) -> dict[str, list[float]]:
    """
    Extract metrics for all 3 approaches from results.

    Args:
        results: Results dict from load_results()

    Returns:
        dict with keys: accuracy, avg_latency_ms, total_cost
        Each value is a list of 3 floats [monolithic, local, hybrid]
    """
    metrics: dict[str, list[float]] = {
        "accuracy": [],
        "avg_latency_ms": [],
        "total_cost": [],
    }

    for key in APPROACH_KEYS:
        approach_data = results.get(key, {})

        accuracy = approach_data.get("accuracy", 0.0)
        latency = approach_data.get("avg_latency_ms", 0.0)
        cost = approach_data.get("total_cost", 0.0)

        metrics["accuracy"].append(accuracy)
        metrics["avg_latency_ms"].append(latency)
        metrics["total_cost"].append(cost)

    return metrics


def create_accuracy_chart(metrics: dict[str, list[float]], output_path: Path) -> Path:
    """
    Create accuracy comparison bar chart.

    Args:
        metrics: Extracted metrics from extract_metrics()
        output_path: Path to save chart

    Returns:
        Path to saved chart
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    x_pos = np.arange(len(APPROACHES))
    accuracies = metrics["accuracy"]

    bars = ax.bar(x_pos, accuracies, color=COLORS, edgecolor="black", linewidth=1.2)

    ax.set_ylabel("Accuracy", fontsize=12)
    ax.set_title("Accuracy Comparison: Monolithic vs Multi-Stage Approaches", fontsize=14, fontweight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(APPROACHES, fontsize=11)
    ax.set_ylim(0, max(accuracies) * 1.2 if max(accuracies) > 0 else 1.0)
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)

    # Add value labels on bars
    for bar, acc in zip(bars, accuracies):
        height = bar.get_height()
        ax.annotate(
            f"{acc:.4f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output_path


def create_latency_chart(metrics: dict[str, list[float]], output_path: Path) -> Path:
    """
    Create latency comparison bar chart.

    Args:
        metrics: Extracted metrics from extract_metrics()
        output_path: Path to save chart

    Returns:
        Path to saved chart
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    x_pos = np.arange(len(APPROACHES))
    latencies = metrics["avg_latency_ms"]

    bars = ax.bar(x_pos, latencies, color=COLORS, edgecolor="black", linewidth=1.2)

    ax.set_ylabel("Latency (ms)", fontsize=12)
    ax.set_title("Latency Comparison: Monolithic vs Multi-Stage Approaches", fontsize=14, fontweight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(APPROACHES, fontsize=11)
    ax.set_ylim(0, max(latencies) * 1.2 if max(latencies) > 0 else 100)
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)

    # Add value labels on bars
    for bar, lat in zip(bars, latencies):
        height = bar.get_height()
        ax.annotate(
            f"{lat:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output_path


def create_cost_chart(metrics: dict[str, list[float]], output_path: Path) -> Path:
    """
    Create cost comparison bar chart.

    Args:
        metrics: Extracted metrics from extract_metrics()
        output_path: Path to save chart

    Returns:
        Path to saved chart
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    x_pos = np.arange(len(APPROACHES))
    costs = metrics["total_cost"]

    bars = ax.bar(x_pos, costs, color=COLORS, edgecolor="black", linewidth=1.2)

    ax.set_ylabel("Total Cost (arbitrary units)", fontsize=12)
    ax.set_title("Cost Comparison: Monolithic vs Multi-Stage Approaches", fontsize=14, fontweight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(APPROACHES, fontsize=11)
    ax.set_ylim(0, max(costs) * 1.2 if max(costs) > 0 else 10)
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)

    # Add value labels on bars
    for bar, cost in zip(bars, costs):
        height = bar.get_height()
        ax.annotate(
            f"{cost:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output_path


def create_combined_chart(metrics: dict[str, list[float]], output_path: Path) -> Path:
    """
    Create combined metrics radar chart.

    Args:
        metrics: Extracted metrics from extract_metrics()
        output_path: Path to save chart

    Returns:
        Path to saved chart
    """
    # Normalize metrics for radar chart (0-1 scale)
    accuracies = metrics["accuracy"]
    latencies = metrics["avg_latency_ms"]
    costs = metrics["total_cost"]

    # Normalize: accuracy (higher is better), latency/cost (lower is better)
    max_acc = max(accuracies) if max(accuracies) > 0 else 1.0
    max_lat = max(latencies) if max(latencies) > 0 else 1.0
    max_cost = max(costs) if max(costs) > 0 else 1.0

    # For radar chart: accuracy (higher=better), latency/cost inverted (lower=better)
    norm_accuracy = [a / max_acc for a in accuracies]
    norm_latency = [1.0 - (l / max_lat) for l in latencies]  # Invert: lower latency = higher score
    norm_cost = [1.0 - (c / max_cost) for c in costs]  # Invert: lower cost = higher score

    # Categories for radar chart
    categories = ["Accuracy", "Speed\n(Lower Latency)", "Cost\n(Lower is Better)"]
    num_vars = len(categories)

    # Calculate angles for radar chart
    angles = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
    angles += angles[:1]  # Close the loop

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    # Plot each approach
    for i, (approach, color) in enumerate(zip(APPROACHES, COLORS)):
        values = [norm_accuracy[i], norm_latency[i], norm_cost[i]]
        values += values[:1]  # Close the loop

        ax.plot(angles, values, linewidth=2.5, linestyle="solid", label=approach, color=color)
        ax.fill(angles, values, color=color, alpha=0.1)

    # Set labels
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels=categories, fontsize=12)

    # Set radial limits
    ax.set_rlim(0, 1.0)
    ax.set_rticks([0.25, 0.5, 0.75, 1.0])
    ax.set_rlabel_position(0)

    plt.title(
        "Combined Metrics Comparison (Normalized)",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )
    plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=11)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output_path


def generate_all_charts(
    results_path: Path | None = None,
    charts_dir: Path | None = None,
) -> dict[str, Path]:
    """
    Generate all 4 comparison charts.

    Args:
        results_path: Path to results.json (default: finetune/multi_stage/results.json)
        charts_dir: Path to charts directory (default: finetune/multi_stage/charts)

    Returns:
        dict with keys: accuracy, latency, cost, combined
        Each value is the Path to the generated chart

    Raises:
        FileNotFoundError: If results file doesn't exist
        ValueError: If results structure is invalid
    """
    # Load results
    results = load_results(results_path)

    # Validate structure
    for key in APPROACH_KEYS:
        if key not in results:
            raise ValueError(f"Missing key in results: {key}")

    # Ensure charts directory exists
    charts_path = ensure_charts_dir(charts_dir)

    # Extract metrics
    metrics = extract_metrics(results)

    # Generate charts
    chart_paths: dict[str, Path] = {}

    chart_paths["accuracy"] = create_accuracy_chart(
        metrics,
        charts_path / "accuracy_comparison.png",
    )

    chart_paths["latency"] = create_latency_chart(
        metrics,
        charts_path / "latency_comparison.png",
    )

    chart_paths["cost"] = create_cost_chart(
        metrics,
        charts_path / "cost_comparison.png",
    )

    chart_paths["combined"] = create_combined_chart(
        metrics,
        charts_path / "combined_metrics.png",
    )

    return chart_paths


def main() -> int:
    """Main entry point."""
    from rich.console import Console

    console = Console()
    console.rule("Metrics Visualization")

    try:
        # Generate all charts
        chart_paths = generate_all_charts()

        console.print("\n[bold green]✓ Generated 4 charts:[/]")
        for chart_type, path in chart_paths.items():
            console.print(f"  - {chart_type}: {path}")

        return 0

    except FileNotFoundError as e:
        console.print(f"\n[bold red]Error:[/] {e}")
        console.print("Run evaluate.py first to generate results.json")
        return 1

    except ValueError as e:
        console.print(f"\n[bold red]Error:[/] {e}")
        return 1

    except Exception as e:
        console.print(f"\n[bold red]Unexpected error:[/] {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())