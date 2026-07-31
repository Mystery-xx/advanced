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
Model Router - Confidence-based routing with fallback logic.

This module implements intelligent request routing between cheap and expensive models
based on confidence evaluation. Low-confidence answers from the cheap model are
automatically escalated to the expensive model.

Usage:
    uv run model_router.py --eval-path finetune/dataset/eval.jsonl
    uv run model_router.py --eval-path finetune/dataset/eval.jsonl --cheap-model llama3.1:8b --expensive-model qwen3:14b
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

# Import confidence evaluators from finetune.confidence package
from finetune.confidence.constraint_check import constraint_check, LABELED_CATEGORIES
from finetune.confidence.self_check import self_check

# ─── Constants ────────────────────────────────────────────────

SYSTEM_PROMPT: Final[str] = (
    "Ты — классификатор тональности отзывов. Определи категорию отзыва.\n"
    "Категории: крайне негативный, негативный, нейтральный, позитивный.\n"
    "Отвечай только названием категории."
)

DEFAULT_CHEAP_MODEL: Final[str] = "llama3.1:8b"
DEFAULT_EXPENSIVE_MODEL: Final[str] = "qwen3:14b"
DEFAULT_OLLAMA_URL: Final[str] = "http://localhost:11434"

# Cost units (relative, not actual $)
COST_UNITS: Final[dict[str, int]] = {
    "cheap": 1,
    "expensive": 3,
}

# ─── Data models ──────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class RouterConfig:
    """Configuration for model routing."""

    cheap_model: str = DEFAULT_CHEAP_MODEL
    expensive_model: str = DEFAULT_EXPENSIVE_MODEL
    escalate_on: list[str] = ("MEDIUM", "LOW")
    use_self_check: bool = True
    ollama_url: str = DEFAULT_OLLAMA_URL


@dataclass(frozen=True, slots=True)
class RouterResult:
    """Result from routing a single request."""

    answer: str
    model_used: str
    confidence_status: str  # "HIGH", "MEDIUM", "LOW"
    explanation: str  # From self_check
    constraint_passed: bool
    escalated: bool  # Whether request was escalated to expensive model
    cheap_answer: str  # Answer from cheap model (before escalation)
    cheap_confidence: str  # Confidence from cheap model
    latency_ms: int
    cost_units: int  # Relative cost units spent


# ─── Core logic ───────────────────────────────────────────────


def compute_confidence(
    user_content: str,
    answer: str,
    model: str,
    ollama_url: str = DEFAULT_OLLAMA_URL,
) -> dict:
    """
    Compute confidence for a classification answer.

    This function combines:
    1. Self-check: Model explains its answer
    2. Constraint check: Validate answer against allowed categories

    Args:
        user_content: The review text that was classified
        answer: The model's classification answer
        model: Ollama model name used for classification
        ollama_url: Ollama API URL

    Returns:
        Dictionary with keys:
        - confidence_status (str): "HIGH", "MEDIUM", or "LOW"
        - explanation (str): Model's explanation from self_check
        - constraint_passed (bool): Whether answer passes constraint check
        - latency_ms (int): Time taken for confidence evaluation

    Example:
        >>> result = compute_confidence(
        ...     user_content="Отличная тачка для дачи",
        ...     answer="позитивный",
        ...     model="llama3.1:8b"
        ... )
        >>> print(result["confidence_status"])
        "HIGH"
    """
    start_time = time.perf_counter()

    # Step 1: Self-check (model explains its answer)
    explanation = ""
    self_check_latency = 0
    if user_content and user_content.strip():
        try:
            self_check_result = self_check(user_content, answer, model)
            explanation = self_check_result["explanation"]
            self_check_latency = self_check_result["latency_ms"]
        except Exception as e:
            explanation = f"Error in self-check: {str(e)}"
            self_check_latency = 0

    # Step 2: Constraint check (validate answer against allowed categories)
    constraint_result = constraint_check(answer, LABELED_CATEGORIES)
    constraint_passed = constraint_result["passed"]

    # Step 3: Compute confidence status
    # HIGH: constraint passed + confident explanation
    # MEDIUM: constraint passed but weak explanation
    # LOW: constraint failed
    if not constraint_passed:
        confidence_status = "LOW"
    elif explanation and len(explanation) > 20:
        confidence_status = "HIGH"
    else:
        confidence_status = "MEDIUM"

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    return {
        "confidence_status": confidence_status,
        "explanation": explanation,
        "constraint_passed": constraint_passed,
        "latency_ms": latency_ms,
    }


def classify(user_content: str, system_prompt: str, model: str, ollama_url: str) -> tuple[str, int]:
    """
    Send single classification request to Ollama and return model's response.

    Returns:
        tuple: (answer, latency_ms)
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.0,
        "stream": False,
    }

    start_time = time.perf_counter()
    response = requests.post(
        f"{ollama_url}/api/chat",
        json=payload,
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()
    latency_ms = int((time.perf_counter() - start_time) * 1000)

    answer = data.get("message", {}).get("content", "").strip()
    return answer, latency_ms


def route_request(
    user_content: str,
    config: RouterConfig,
) -> RouterResult:
    """
    Route a single request through the confidence-based routing chain.

    This function:
    1. Sends request to cheap model
    2. Computes confidence in cheap model's answer
    3. If confidence is low (per escalate_on), escalates to expensive model
    4. Returns result with routing metadata

    Args:
        user_content: The review text to classify
        config: RouterConfig with routing parameters

    Returns:
        RouterResult with all routing metadata

    Example:
        >>> config = RouterConfig(
        ...     cheap_model="llama3.1:8b",
        ...     expensive_model="qwen3:14b",
        ...     escalate_on=["MEDIUM", "LOW"]
        ... )
        >>> result = route_request("Отличная тачка!", config)
        >>> print(result.model_used)
        "llama3.1:8b"  # or "qwen3:14b" if escalated
        >>> print(result.escalated)
        False  # or True if escalated
    """
    start_time = time.perf_counter()

    # Step 1: Cheap model classification
    try:
        cheap_answer, cheap_latency = classify(
            user_content, SYSTEM_PROMPT, config.cheap_model, config.ollama_url
        )
    except requests.ConnectionError:
        raise EnvironmentError(
            f"Cannot connect to Ollama at {config.ollama_url}. "
            "Start it with: ollama serve"
        )
    except requests.HTTPError as e:
        raise EnvironmentError(
            f"Ollama API error: {e}. "
            "Is Ollama running? (ollama serve)"
        )

    # Step 2: Compute confidence in cheap model's answer
    try:
        confidence_result = compute_confidence(
            user_content, cheap_answer, config.cheap_model, config.ollama_url
        )
        confidence_status = confidence_result["confidence_status"]
        explanation = confidence_result["explanation"]
        constraint_passed = confidence_result["constraint_passed"]
    except Exception as e:
        confidence_status = "LOW"
        explanation = f"Error computing confidence: {str(e)}"
        constraint_passed = False

    # Step 3: Decide whether to escalate
    escalate = confidence_status in config.escalate_on
    cost_units = COST_UNITS["cheap"]

    # Step 4: Escalate if needed
    final_answer = cheap_answer
    model_used = config.cheap_model
    total_latency = cheap_latency

    if escalate:
        # Escalate to expensive model
        try:
            expensive_answer, expensive_latency = classify(
                user_content, SYSTEM_PROMPT, config.expensive_model, config.ollama_url
            )
            final_answer = expensive_answer
            model_used = config.expensive_model
            total_latency += expensive_latency
            cost_units = COST_UNITS["expensive"]

            # Re-compute confidence for expensive model's answer
            if config.use_self_check:
                try:
                    new_confidence_result = compute_confidence(
                        user_content, expensive_answer, config.expensive_model, config.ollama_url
                    )
                    confidence_status = new_confidence_result["confidence_status"]
                    explanation = new_confidence_result["explanation"]
                    constraint_passed = new_confidence_result["constraint_passed"]
                except Exception:
                    pass  # Keep original confidence data
        except Exception:
            # Fallback to cheap model if expensive model fails
            pass

    total_latency_ms = int((time.perf_counter() - start_time) * 1000)

    return RouterResult(
        answer=final_answer,
        model_used=model_used,
        confidence_status=confidence_status,
        explanation=explanation,
        constraint_passed=constraint_passed,
        escalated=escalate,
        cheap_answer=cheap_answer,
        cheap_confidence=confidence_status if not escalate else compute_confidence(
            user_content, cheap_answer, config.cheap_model, config.ollama_url
        )["confidence_status"],
        latency_ms=total_latency_ms,
        cost_units=cost_units,
    )


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


def run_routing_evaluation(
    examples: list[dict],
    config: RouterConfig,
) -> list[RouterResult]:
    """
    Run routing evaluation on all examples.

    Args:
        examples: List of evaluation examples from JSONL
        config: RouterConfig with routing parameters

    Returns:
        List of RouterResult objects for each example
    """
    console = Console()
    results: list[RouterResult] = []

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
                f"Confidence: [bold]{result.confidence_status}[/]"
            )
        except EnvironmentError as e:
            console.print(f"[red]Error on example #{i + 1}: {e}[/]")
            # Create a failed result
            result = RouterResult(
                answer="ERROR",
                model_used="",
                confidence_status="ERROR",
                explanation=str(e),
                constraint_passed=False,
                escalated=False,
                cheap_answer="",
                cheap_confidence="ERROR",
                latency_ms=0,
                cost_units=0,
            )

        results.append(result)

    return results


def compute_routing_metrics(results: list[RouterResult]) -> dict:
    """
    Compute routing metrics from evaluation results.

    Returns dict with:
    - total_samples: Number of samples evaluated
    - escalation_rate: Fraction of requests escalated
    - avg_latency_ms: Average latency across all requests
    - avg_cost_units: Average cost units spent
    - confidence_distribution: Count of HIGH/MEDIUM/LOW confidence results
    - accuracy_by_confidence: Accuracy for each confidence level
    """
    total = len(results)
    if total == 0:
        return {
            "total_samples": 0,
            "escalation_rate": 0.0,
            "avg_latency_ms": 0.0,
            "avg_cost_units": 0.0,
            "confidence_distribution": {},
            "accuracy_by_confidence": {},
        }

    escalated_count = sum(1 for r in results if r.escalated)
    total_latency = sum(r.latency_ms for r in results)
    total_cost = sum(r.cost_units for r in results)

    # Confidence distribution
    confidence_counts: dict[str, int] = {}
    for r in results:
        conf = r.confidence_status
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

    # Accuracy by confidence level
    accuracy_by_confidence: dict[str, float] = {}
    for conf_level in ["HIGH", "MEDIUM", "LOW", "ERROR"]:
        conf_results = [r for r in results if r.confidence_status == conf_level]
        if conf_results:
            # Note: We can't compute accuracy without the actual labels in RouterResult
            # This would need to be computed externally
            accuracy_by_confidence[conf_level] = 0.0  # Placeholder
        else:
            accuracy_by_confidence[conf_level] = 0.0

    return {
        "total_samples": total,
        "escalation_rate": round(escalated_count / total, 4),
        "avg_latency_ms": round(total_latency / total, 2),
        "avg_cost_units": round(total_cost / total, 2),
        "confidence_distribution": confidence_counts,
        "accuracy_by_confidence": accuracy_by_confidence,
    }


def print_routing_summary(console: Console, metrics: dict) -> None:
    """Print formatted routing summary."""
    console.print()
    console.rule("Routing Summary")
    console.print(f"Total samples:     [bold]{metrics['total_samples']}[/]")
    console.print(f"Escalation rate:   [bold]{metrics['escalation_rate']:.2%}[/]")
    console.print(f"Avg latency:       [bold]{metrics['avg_latency_ms']:.1f} ms[/]")
    console.print(f"Avg cost units:    [bold]{metrics['avg_cost_units']:.2f}[/]")
    console.print()

    # Confidence distribution
    console.print("[bold]Confidence Distribution:[/]")
    conf_dist = metrics["confidence_distribution"]
    for level in ["HIGH", "MEDIUM", "LOW", "ERROR"]:
        count = conf_dist.get(level, 0)
        console.print(f"  {level:6s}: {count}")


def save_routing_results(
    output_path: Path,
    metrics: dict,
    results: list[RouterResult],
    dataset_path: str,
    config: RouterConfig,
) -> None:
    """Save routing results to JSON file."""

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

    results_dict = {
        "cheap_model": config.cheap_model,
        "expensive_model": config.expensive_model,
        "escalate_on": config.escalate_on,
        "use_self_check": config.use_self_check,
        "ollama_url": config.ollama_url,
        "dataset_path": dataset_path,
        "total_samples": len(results),
        **metrics,
        "predictions": [
            {
                "answer": r.answer,
                "model_used": r.model_used,
                "confidence_status": r.confidence_status,
                "explanation": r.explanation,
                "constraint_passed": r.constraint_passed,
                "escalated": r.escalated,
                "cheap_answer": r.cheap_answer,
                "cheap_confidence": r.cheap_confidence,
                "latency_ms": r.latency_ms,
                "cost_units": r.cost_units,
            }
            for r in results
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


def parse_args(args: list[str]) -> tuple[Path, RouterConfig]:
    """Parse command-line arguments."""
    eval_path: Path | None = None
    cheap_model: str = DEFAULT_CHEAP_MODEL
    expensive_model: str = DEFAULT_EXPENSIVE_MODEL
    escalate_on: list[str] = ("MEDIUM", "LOW")
    use_self_check: bool = True
    ollama_url: str = DEFAULT_OLLAMA_URL

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
            escalate_on = tuple(s.strip() for s in args[i + 1].split(","))
            i += 2
        elif arg == "--ollama-url" and i + 1 < len(args):
            ollama_url = args[i + 1]
            i += 2
        elif arg == "--no-self-check":
            use_self_check = False
            i += 1
        else:
            i += 1

    config = RouterConfig(
        cheap_model=cheap_model,
        expensive_model=expensive_model,
        escalate_on=list(escalate_on),
        use_self_check=use_self_check,
        ollama_url=ollama_url,
    )

    return eval_path or Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl", config


def main() -> int:
    """Run model routing evaluation."""
    args = sys.argv[1:]
    eval_path, config = parse_args(args)
    output_path = Path(__file__).resolve().parent / "routing_results.json"
    console = Console()

    console.rule(f"Model Routing Evaluation")
    console.print(f"Ollama URL:      {config.ollama_url}")
    console.print(f"Cheap model:     {config.cheap_model}")
    console.print(f"Expensive model: {config.expensive_model}")
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
    results = run_routing_evaluation(examples, config)
    elapsed = time.perf_counter() - start
    console.print(f"\nCompleted in {elapsed:.1f}s ({elapsed / len(results):.2f}s per sample)")

    # Metrics
    metrics = compute_routing_metrics(results)
    print_routing_summary(console, metrics)

    # Save
    save_routing_results(output_path, metrics, results, str(eval_path), config)
    console.print(f"\n[green]✓[/] Results saved to [bold]{output_path}[/]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())