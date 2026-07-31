#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
#     "rich",
# ]
# ///
"""
Demo: Model routing on 5 selected examples from eval.jsonl.

Runs 5 hand-picked examples through route_request() and displays:
- Which model handled each request (cheap vs expensive)
- Confidence level and escalation status
- Correctness vs expected label
- Summary statistics

Usage:
    cd finetune/routing
    uv run demo_run.py

Requires:
    - Ollama running at http://localhost:11434
    - Models: llama3.2:1b, qwen3:14b
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
from rich.panel import Panel

# ─── Import routing module ─────────────────────────────────────

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from finetune.routing.model_router import route_request, RouterConfig, check_ollama

# ─── Constants ─────────────────────────────────────────────────

OUTPUT_PATH: Final[Path] = Path(__file__).resolve().parent / "demo_results.json"

# 5 selected examples from eval.jsonl
# Format: (line_number_1based, user_content, expected_label)
EXAMPLES: Final[list[tuple[int, str, str]]] = [
    (
        20,
        "Супер покупка! Тачка крепкая, лёгкая, удобная. "
        "Колесо пневматическое, мягко катит. Корыто вместительное — "
        "за раз много везёшь. Рама не шатается. Ручки с мягкими "
        "накладками за 15 минут — всё подогнано. Пользуюсь каждый "
        "день — ни поломки!",
        "позитивный",
    ),
    (
        6,
        "Проработала одну неделю, потом колесо пошло ходуном, "
        "рама покрылась ржавчиной на швах, корыто провисло к "
        "колесу. Обратился в службу поддержки — пропало. Через "
        "месяц ответа — отправил фото дефектов, в ответ тишина. "
        "Качество на уровне мусора, цена как на нормальную тачку. "
        "Никому не советую.",
        "крайне негативный",
    ),
    (
        1,
        "Брал чтобы заменить старую — та развалилась. Эта "
        "работает. Колесо накачиваю раз в 5 дней, корыто не "
        "гнило. Рама не шатается. Минус — покраска. Гайки "
        "ослабевают. Средняя оценка — работает.",
        "нейтральный",
    ),
    (
        15,
        "При условии небольших доработок прослужить должна "
        "долго. Под кузов сразу проложил лист текстолита для "
        "жесткости. Ту шпильку для колес, на которую много "
        "нареканий, которой комплектует производитель, заменил "
        "на 14 усиленную шпильку, в колеса она подошла с "
        "небольшим натягом, а проушины в раме пришлось "
        "рассверлить.",
        "негативный",
    ),
    (
        13,
        "Отвратительный товар. Считаю недопустимо продавать "
        "товар такого качества. Накачал колеса не более 15-20 "
        "psi (колесо на ощупь было мягкое). Через 1 минуту без "
        "нагрузки корд покрышки вырвало сбоку и оттуда вылезла "
        "камера. Получил тачку в разобранном виде. Винт, который "
        "соединяет корыто с отверстием в трубе над колесом не "
        "совпадают примерно на 10см. Два часа пытался понять, "
        "что я делаю не так. После этого пришлось ехать и "
        "сдавать тачку.",
        "крайне негативный",
    ),
]

EXAMPLE_TYPES: Final[list[str]] = [
    "Simple positive",
    "Simple negative",
    "Neutral mixed",
    "Complex technical",
    "Extremely negative",
]


@dataclass
class DemoResult:
    """Result from running a single demo example."""
    number: int          # Line number in eval.jsonl (1-based)
    example_type: str    # Short description
    expected: str        # Expected label
    answer: str          # Model answer
    correct: bool        # Whether answer matches expected
    model_used: str      # Which model handled it
    confidence: str      # HIGH / MEDIUM / LOW
    escalated: bool      # Was request escalated
    latency_ms: int      # Total latency
    cost_units: int      # Cost units spent
    cheap_answer: str    # What cheap model said
    cheap_confidence: str  # Cheap model's confidence


def normalize(s: str) -> str:
    """Normalize a label for comparison."""
    return s.strip().lower().rstrip(".,!?;:")


def run_demo(config: RouterConfig, console: Console) -> list[DemoResult]:
    """Run all demo examples and return results."""
    results: list[DemoResult] = []

    for idx, (line_num, text, expected) in enumerate(EXAMPLES):
        example_type = EXAMPLE_TYPES[idx]

        console.print(f"\n[bold cyan]─── Example #{idx + 1}: [{example_type}] "
                      f"(eval.jsonl line {line_num}) ───[/]")

        try:
            result = route_request(text, config)
            correct = normalize(result.answer) == normalize(expected)

            demo_result = DemoResult(
                number=line_num,
                example_type=example_type,
                expected=expected,
                answer=result.answer,
                correct=correct,
                model_used=result.model_used,
                confidence=result.confidence_status,
                escalated=result.escalated,
                latency_ms=result.latency_ms,
                cost_units=result.cost_units,
                cheap_answer=result.cheap_answer,
                cheap_confidence=result.cheap_confidence,
            )
            results.append(demo_result)

            status = "✓" if correct else "✗"
            color = "green" if correct else "red"
            esc = " [yellow](escalated)[/]" if result.escalated else ""
            console.print(
                f"  [{color}]{status}[/] Expected: [bold]{expected}[/]"
                f" | Got: [bold]{result.answer}[/]"
            )
            console.print(
                f"  Model: [bold]{result.model_used}[/]{esc}"
                f" | Confidence: [bold]{result.confidence_status}[/]"
                f" | Cost: {result.cost_units} units"
                f" | Latency: {result.latency_ms} ms"
            )
            if result.escalated:
                console.print(
                    f"  Cheap answer: [dim]{result.cheap_answer}[/]"
                    f" (confidence: {result.cheap_confidence})"
                )

        except EnvironmentError as e:
            console.print(f"  [red]ERROR: {e}[/]")
            demo_result = DemoResult(
                number=line_num,
                example_type=example_type,
                expected=expected,
                answer="ERROR",
                correct=False,
                model_used="",
                confidence="ERROR",
                escalated=False,
                latency_ms=0,
                cost_units=0,
                cheap_answer="",
                cheap_confidence="",
            )
            results.append(demo_result)

    return results


def print_summary_table(console: Console, results: list[DemoResult]) -> None:
    """Print formatted summary table."""
    table = Table(title="Demo Routing Results", title_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Type", style="dim", width=20)
    table.add_column("Model", style="bold", width=22)
    table.add_column("Answer", width=18)
    table.add_column("Expected", width=18)
    table.add_column("Conf.", width=8)
    table.add_column("Esc.", width=5)
    table.add_column("Correct", width=7)

    correct_count = 0
    for r in results:
        correct = r.answer == r.expected or normalize(r.answer) == normalize(r.expected)
        if correct:
            correct_count += 1
        correct_str = f"[green]✓[/]" if correct else f"[red]✗[/]"
        esc_str = f"[yellow]Y[/]" if r.escalated else "N"
        ans_display = r.answer if r.answer != "ERROR" else "[red]ERROR[/]"

        table.add_row(
            str(r.number),
            r.example_type,
            r.model_used if r.model_used else "[red]—[/]",
            ans_display,
            r.expected,
            r.confidence,
            esc_str,
            correct_str,
        )

    console.print()
    console.print(table)

    # Summary stats line
    total = len(results)
    accuracy = correct_count / total * 100 if total else 0
    escalated = sum(1 for r in results if r.escalated)
    avg_latency = sum(r.latency_ms for r in results) / total if total else 0
    avg_cost = sum(r.cost_units for r in results) / total if total else 0

    scores = "".join(
        "[green]✓[/]" if normalize(r.answer) == normalize(r.expected) else "[red]✗[/]"
        for r in results
    )

    console.print()
    console.print(Panel.fit(
        f"[bold]Accuracy:[/] {accuracy:.0f}%   "
        f"[bold]Escalation rate:[/] {escalated}/{total} ({escalated/total*100:.0f}%)   "
        f"[bold]Avg latency:[/] {avg_latency:.0f} ms   "
        f"[bold]Avg cost:[/] {avg_cost:.1f} units   "
        f"[bold]Scores:[/] {scores}",
        title="Summary Statistics",
        border_style="bold cyan",
    ))


def save_results(results: list[DemoResult], output_path: Path) -> None:
    """Save results to JSON file."""
    output_data = {
        "config": {
            "cheap_model": "llama3.2:1b",
            "expensive_model": "qwen3:14b",
            "escalate_on": ["MEDIUM", "LOW"],
        },
        "statistics": {
            "total": len(results),
            "correct": sum(1 for r in results if r.correct),
            "accuracy_pct": round(
                sum(1 for r in results if r.correct) / len(results) * 100, 1
            ) if results else 0.0,
            "escalated": sum(1 for r in results if r.escalated),
            "escalation_rate_pct": round(
                sum(1 for r in results if r.escalated) / len(results) * 100, 1
            ) if results else 0.0,
            "avg_latency_ms": round(
                sum(r.latency_ms for r in results) / len(results), 1
            ) if results else 0.0,
            "avg_cost_units": round(
                sum(r.cost_units for r in results) / len(results), 2
            ) if results else 0.0,
        },
        "results": [
            {
                "line_number": r.number,
                "example_type": r.example_type,
                "expected": r.expected,
                "answer": r.answer,
                "correct": r.correct,
                "model_used": r.model_used,
                "confidence": r.confidence,
                "escalated": r.escalated,
                "latency_ms": r.latency_ms,
                "cost_units": r.cost_units,
                "cheap_answer": r.cheap_answer,
                "cheap_confidence": r.cheap_confidence,
            }
            for r in results
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    """Run the demo."""
    console = Console()

    console.rule("[bold cyan]Model Routing Demo — 5 Selected Examples[/]")
    console.print()

    config = RouterConfig(
        cheap_model="llama3.2:1b",
        expensive_model="qwen3:14b",
    )

    console.print(f"  Cheap model:     [bold]{config.cheap_model}[/]")
    console.print(f"  Expensive model: [bold]{config.expensive_model}[/]")
    console.print(f"  Escalate on:     [bold]{', '.join(config.escalate_on)}[/]")
    console.print(f"  Use self-check:  [bold]{config.use_self_check}[/]")
    console.print(f"  Ollama URL:      [bold]{config.ollama_url}[/]")
    console.print()

    # Verify Ollama is available
    try:
        check_ollama(config)
        console.print("[green]✓[/] Ollama running, models available")
    except EnvironmentError as e:
        console.print(f"[red]Error: {e}[/]")
        console.print()
        console.print("[yellow]Cannot proceed without Ollama. "
                      "Start with: ollama serve[/]")
        console.print("[yellow]Then pull models: ollama pull llama3.2:1b "
                      "&& ollama pull qwen3:14b[/]")
        return 1

    # Run demo
    console.print(f"\n[bold]Running {len(EXAMPLES)} examples...[/]")
    start = time.perf_counter()
    results = run_demo(config, console)
    elapsed = time.perf_counter() - start

    console.print(f"\nCompleted in {elapsed:.1f}s "
                  f"({elapsed / len(results):.2f}s per example)")

    # Summary
    print_summary_table(console, results)

    # Save
    save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]✓[/] Results saved to [bold]{OUTPUT_PATH}[/]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
