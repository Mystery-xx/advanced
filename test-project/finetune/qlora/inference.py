#!/usr/bin/env python3
"""Inference and evaluation for QLoRA-fine-tuned sentiment classifier.

Loads base model + LoRA adapter (or merged model), evaluates on the eval set.

Usage:
    # With adapter:
    python inference.py --adapter-path test-project/finetune/qlora/outputs/adapter

    # With merged model:
    python inference.py --merged-path test-project/finetune/qlora/outputs/merged

    # Default: auto-detect latest output dir
    python inference.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch
from peft import PeftModel
from rich.console import Console
from rich.table import Table
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from transformers import AutoModelForCausalLM, AutoTokenizer

console = Console()

LABELED_CATEGORIES = [
    "крайне негативный",
    "негативный",
    "нейтральный",
    "позитивный",
]

SYSTEM_PROMPT = (
    "Ты — классификатор тональности отзывов. Определи категорию отзыва.\n"
    "Категории: крайне негативный, негативный, нейтральный, позитивный.\n"
    "Отвечай только названием категории."
)

BASE_MODEL = "Qwen/Qwen2.5-14B-Instruct"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "outputs"
DEFAULT_EVAL = Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def load_model_and_tokenizer(
    adapter_path: Path | None = None,
    merged_path: Path | None = None,
):
    """Load the fine-tuned model and tokenizer.

    Priority: merged model > base + adapter > error.
    """
    console.print("[bold cyan]Loading model...[/]")

    # Load tokenizer first
    load_dir = str(merged_path) if merged_path else str(adapter_path) if adapter_path else str(DEFAULT_OUTPUT / "adapter")
    tokenizer = AutoTokenizer.from_pretrained(load_dir, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    # Model loading strategy
    if merged_path and merged_path.exists():
        console.print(f"  Loading merged model: {merged_path}")
        model = AutoModelForCausalLM.from_pretrained(
            str(merged_path),
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
    elif adapter_path and adapter_path.exists():
        console.print(f"  Loading base + adapter: {adapter_path}")
        base = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
        model = PeftModel.from_pretrained(base, str(adapter_path))
        model.eval()
    else:
        console.print("[yellow]No adapter or merged model found. Loading base model for comparison.[/]")
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )

    console.print(f"  Device: {model.device}")
    return model, tokenizer


def classify(model, tokenizer, review: str) -> str:
    """Classify a single review."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": review},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=16,
            temperature=0.0,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
    prediction = tokenizer.decode(generated_ids, skip_special_tokens=True).strip().lower()
    return prediction


def run_evaluation(
    model, tokenizer, eval_path: Path, output_path: Path | None = None,
) -> dict:
    """Evaluate model on eval set, return metrics dict."""
    examples = load_jsonl(eval_path)
    console.print(f"\n[bold]Evaluating {len(examples)} samples...[/]\n")

    predictions, actuals, details = [], [], []
    for i, record in enumerate(examples):
        user_text = record["messages"][1]["content"]
        actual = record["messages"][2]["content"].strip()
        pred = classify(model, tokenizer, user_text)
        predictions.append(pred)
        actuals.append(actual)
        details.append({
            "index": i,
            "user_content": user_text[:120],
            "predicted": pred,
            "actual": actual,
            "correct": pred == actual,
        })

        status = "[green]✓[/]" if pred == actual else "[red]✗[/]"
        console.print(f"  {status} #{i+1:2d} pred=[bold]{pred}[/] gold=[bold]{actual}[/]")

    # Metrics
    acc = accuracy_score(actuals, predictions)
    m_p = precision_score(actuals, predictions, labels=LABELED_CATEGORIES, average="macro", zero_division=0)
    m_r = recall_score(actuals, predictions, labels=LABELED_CATEGORIES, average="macro", zero_division=0)
    m_f1 = f1_score(actuals, predictions, labels=LABELED_CATEGORIES, average="macro", zero_division=0)
    w_f1 = f1_score(actuals, predictions, labels=LABELED_CATEGORIES, average="weighted", zero_division=0)
    cm = confusion_matrix(actuals, predictions, labels=LABELED_CATEGORIES).tolist()
    report = classification_report(actuals, predictions, labels=LABELED_CATEGORIES, zero_division=0)

    per_class = {}
    for label in LABELED_CATEGORIES:
        single = [label]
        p = precision_score(actuals, predictions, labels=single + ["unknown"], zero_division=0, average=None)
        r = recall_score(actuals, predictions, labels=single + ["unknown"], zero_division=0, average=None)
        f = f1_score(actuals, predictions, labels=single + ["unknown"], zero_division=0, average=None)
        support = sum(1 for a in actuals if a == label)
        per_class[label] = {"precision": round(p[0], 4), "recall": round(r[0], 4), "f1": round(f[0], 4), "support": support}

    # Print results
    console.rule("[bold green]Evaluation Results[/]")
    console.print(f"  Accuracy:   [bold]{acc:.4f}[/]")
    console.print(f"  Macro F1:   [bold]{m_f1:.4f}[/] (P={m_p:.4f}, R={m_r:.4f})")
    console.print(f"  Weighted F1:[bold]{w_f1:.4f}[/]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Class")
    table.add_column("Prec.")
    table.add_column("Recall")
    table.add_column("F1")
    table.add_column("N")
    for label in LABELED_CATEGORIES:
        m = per_class[label]
        table.add_row(label, f"{m['precision']:.4f}", f"{m['recall']:.4f}", f"{m['f1']:.4f}", str(m['support']))
    console.print(table)

    # Confusion matrix
    console.print("\n[bold]Confusion Matrix:[/]")
    cm_table = Table(show_header=True, header_style="bold magenta")
    cm_table.add_column("Actual ↘ Pred ↙", style="dim")
    for label in LABELED_CATEGORIES:
        cm_table.add_column(label, justify="right")
    for i, label in enumerate(LABELED_CATEGORIES):
        row = [label]
        for val in cm[i]:
            row.append(str(val))
        cm_table.add_row(*row)
    console.print(cm_table)

    # Misclassifications
    wrong = [d for d in details if not d["correct"]]
    if wrong:
        console.print(f"\n[bold red]Misclassifications ({len(wrong)})[/]")
        for d in wrong:
            console.print(f"  #{d['index']+1} pred=[red]{d['predicted']}[/] gold=[green]{d['actual']}[/]")
            console.print(f"    \"{d['user_content']}...\"" if len(d["user_content"]) > 80 else f'    "{d["user_content"]}"')

    console.print(f"\n{report}")

    # Save
    results = {
        "model": BASE_MODEL,
        "fine_tuning": "qlora",
        "dataset_path": str(eval_path),
        "total_samples": len(details),
        "accuracy": round(acc, 4),
        "macro_f1": round(m_f1, 4),
        "macro_precision": round(m_p, 4),
        "macro_recall": round(m_r, 4),
        "weighted_f1": round(w_f1, 4),
        "per_class": per_class,
        "confusion_matrix": cm,
        "classification_report": report,
        "predictions": details,
    }

    save_path = output_path or Path(__file__).resolve().parent / "inference_results.json"
    save_path.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    console.print(f"\n[green]✓ Results saved: {save_path}[/]")

    return results


def interact(model, tokenizer) -> None:
    """Interactive classification loop."""
    console.print("\n[bold cyan]Interactive mode (Ctrl+C to exit)[/]\n")
    while True:
        review = console.input("[dim]Review> [/]").strip()
        if not review:
            continue
        pred = classify(model, tokenizer, review)
        console.print(f"  → [bold]{pred}[/]\n")


# ─── Entry point ──────────────────────────────────────────────
def main() -> int:
    adapter_path: Path | None = None
    merged_path: Path | None = None
    eval_path = DEFAULT_EVAL
    interactive = False

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--adapter-path" and i + 1 < len(sys.argv):
            adapter_path = Path(sys.argv[i + 1])
        elif sys.argv[i] == "--merged-path" and i + 1 < len(sys.argv):
            merged_path = Path(sys.argv[i + 1])
        elif sys.argv[i] == "--eval-path" and i + 1 < len(sys.argv):
            eval_path = Path(sys.argv[i + 1])
        elif sys.argv[i] == "--interactive":
            interactive = True
        i += 1

    # Auto-detect
    if not adapter_path and not merged_path:
        out = DEFAULT_OUTPUT
        if (out / "merged").exists():
            merged_path = out / "merged"
        elif (out / "adapter").exists():
            adapter_path = out / "adapter"

    if not eval_path.exists():
        console.print(f"[red]Error: eval file not found: {eval_path}[/]")
        return 1

    model, tokenizer = load_model_and_tokenizer(adapter_path, merged_path)

    if interactive:
        try:
            interact(model, tokenizer)
        except KeyboardInterrupt:
            console.print("\nBye!")
    else:
        run_evaluation(model, tokenizer, eval_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
