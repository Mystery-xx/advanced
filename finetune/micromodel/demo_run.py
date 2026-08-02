from __future__ import annotations

import time

import sys
from pathlib import Path


_repo_root = str(Path(__file__).resolve().parents[2])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from finetune.micromodel.micromodel_router import (
    MicroModelConfig,
    RouterResult,
    route_with_fallback,
)

SIMPLE_QUERIES: list[dict] = [
    {
        "text": "Этот фильм просто великолепен!",
        "expected": "micromodel",
        "note": "Simple positive",
    },
    {
        "text": "Ужасное обслуживание, больше не приду",
        "expected": "micromodel",
        "note": "Simple negative",
    },
]

EDGE_QUERIES: list[dict] = [
    {
        "text": "",
        "expected": "llm fallback",
        "note": "Empty string",
    },
    {
        "text": "asdfgh jklwq",
        "expected": "llm fallback",
        "note": "Gibberish",
    },
]

HARD_QUERIES: list[dict] = [
    {
        "text": "Сначала было плохо, но потом стало ещё хуже",
        "expected": "llm fallback",
        "note": "Temporal shift -> low confidence",
    },
]

ALL_QUERIES = SIMPLE_QUERIES + EDGE_QUERIES + HARD_QUERIES


def print_separator(char: str = "─", width: int = 72) -> None:
    print(char * width)


def print_result(idx: int, item: dict, result: RouterResult) -> None:

    print_separator()
    print(f"  [{idx}] {item['note']}")
    print(f"  Query:       {item['text']!r}")
    print(f"  ─────────────────────────────────────────────")
    print(f"  Answer:      {result.answer}")
    print(f"  Model used:  {result.model_used}")
    print(f"  Confidence:  {result.confidence_status}")
    print(f"  Escalated:   {result.escalated}")
    print(f"  Latency:     {result.latency_ms} ms")
    print(f"  Cost units:  {result.cost_units}")
    print(f"  Cheap pred:  {result.cheap_answer}")
    print(f"  Cheap conf:  {result.cheap_confidence}")
    print(f"  Constraint:  {'PASSED' if result.constraint_passed else 'FAILED'}")
    print(f"  Explanation: {result.explanation}")


def main() -> None:
    config = MicroModelConfig(confidence_threshold=0.30)

    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║         Micro-Model Routing Demo — 5 Test Examples          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"  Confidence threshold:  {config.confidence_threshold}")
    print(f"  LLM fallback model:    {config.llm_model}")
    print(f"  Ollama URL:            {config.ollama_url}")
    print()

    results: list[RouterResult] = []
    total_start = time.perf_counter()

    for i, item in enumerate(ALL_QUERIES, start=1):
        try:
            result = route_with_fallback(item["text"], config)
        except Exception as exc:
            print_separator()
            print(f"  [{i}] {item['note']} — UNEXPECTED ERROR")
            print(f"  Query:  {item['text']!r}")
            print(f"  Error:  {exc}")
            print()
            continue

        results.append(result)
        print_result(i, item, result)
        print()

    total_elapsed = time.perf_counter() - total_start

    
    print_separator("═")
    print("  SUMMARY STATISTICS")
    print_separator("─")

    total = len(results)
    fallbacks = sum(1 for r in results if r.escalated)
    micromodel_count = total - fallbacks
    latencies = [r.latency_ms for r in results]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    total_cost = sum(r.cost_units for r in results)

    cost_if_all_llm = total * 3
    savings = cost_if_all_llm - total_cost
    savings_pct = (savings / cost_if_all_llm) * 100 if cost_if_all_llm else 0.0

    print(f"  Total queries:          {total}")
    print(f"  Micro-model handled:    {micromodel_count}  ({micromodel_count / total * 100:.0f}%)")
    print(f"  LLM fallback:           {fallbacks}  ({fallbacks / total * 100:.0f}%)")
    print(f"  Total wall time:        {total_elapsed * 1000:.0f} ms")
    print(f"  Average latency:        {avg_latency:.1f} ms")
    print(f"  Total cost units:       {total_cost}")
    print(f"  Cost savings vs all-LLM: {savings} units ({savings_pct:.0f}%)")
    print_separator("═")
    print()


if __name__ == "__main__":
    main()
