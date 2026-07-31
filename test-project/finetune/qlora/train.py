#!/usr/bin/env python3
"""QLoRA fine-tuning of Qwen2.5-14B-Instruct for sentiment classification.

4-bit quantized LoRA adaptation of Qwen2.5-14B-Instruct via SFTTrainer (TRL).
Dataset: JSONL with messages format (system/user/assistant).
Target: 4-class sentiment classification (Russian reviews).

Usage:
    python train.py [--train-path PATH] [--eval-path PATH] [--output-dir DIR]
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import bitsandbytes as bnb
import torch
import datasets
from datasets import DatasetDict
from peft import LoraConfig, PeftModel, TaskType, get_peft_model, prepare_model_for_kbit_training
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
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    set_seed,
)
from trl import SFTConfig, SFTTrainer

console = Console()

# ─── Constants ────────────────────────────────────────────────
LABELED_CATEGORIES = [
    "крайне негативный",
    "негативный",
    "нейтральный",
    "позитивный",
]

DEFAULT_TRAIN = Path(__file__).resolve().parent.parent / "dataset" / "train.jsonl"
DEFAULT_EVAL = Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "outputs"

MODEL_NAME = "Qwen/Qwen2.5-14B-Instruct"


# ─── Data loading ─────────────────────────────────────────────
def load_jsonl(path: Path) -> list[dict]:
    """Load JSONL file, return list of parsed records."""
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def prepare_dataset(
    train_path: Path, eval_path: Path, tokenizer: AutoTokenizer,
) -> DatasetDict:
    """Convert JSONL → HuggingFace DatasetDict (conversational format for SFTTrainer)."""
    train_data = load_jsonl(train_path)
    eval_data = load_jsonl(eval_path)

    # SFTTrainer with format="conversational" understands records with 'messages' key
    # Each record: {"messages": [{"role":"system",...}, {"role":"user",...}, {"role":"assistant",...}]}

    # Apply chat template to generate text for training
    def apply_template(example: dict) -> dict:
        return {"text": tokenizer.apply_chat_template(example["messages"], tokenize=False, add_generation_prompt=False)}

    # Build datasets using Arrow directly to avoid PIL import in newer datasets
    train_texts = [tokenizer.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=False) for r in train_data]
    eval_texts = [tokenizer.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=False) for r in eval_data]

    import pyarrow as pa
    train_table = pa.table({"text": pa.array(train_texts, type=pa.large_string())})
    eval_table = pa.table({"text": pa.array(eval_texts, type=pa.large_string())})
    train_ds = datasets.arrow_dataset.Dataset(train_table)
    eval_ds = datasets.arrow_dataset.Dataset(eval_table)

    return DatasetDict({"train": train_ds, "eval": eval_ds})


# ─── Model loading ────────────────────────────────────────────
def load_model_quantized(model_name: str):
    """Load model in 4-bit (NF4) with bitsandbytes."""
    console.print("[bold cyan]Loading model in 4-bit NF4...[/]")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )

    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    # VRAM report
    mem = torch.cuda.mem_get_info(0)
    console.print(f"  Allocated:    {torch.cuda.memory_allocated(0) / 1e9:.2f} GB")
    console.print(f"  Reserved:     {torch.cuda.memory_reserved(0) / 1e9:.2f} GB")
    console.print(f"  Free:         {mem[0] / 1e9:.2f} GB / {mem[1] / 1e9:.2f} GB")

    return model


def apply_lora(model: AutoModelForCausalLM) -> PeftModel:
    """Configure and apply LoRA adapter."""
    console.print("[bold cyan]Applying LoRA adapter (r=16, alpha=32, dropout=0.05)...[/]")

    config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias="none",
    )

    peft_model = get_peft_model(model, config)
    peft_model.print_trainable_parameters()
    return peft_model


# ─── Evaluation ───────────────────────────────────────────────
@dataclass
class EvaluationResult:
    accuracy: float
    macro_f1: float
    macro_precision: float
    macro_recall: float
    weighted_f1: float
    per_class: dict[str, dict]
    confusion_matrix: list[list[int]]
    report: str
    predictions: list[dict]


def compute_metrics(preds: tuple) -> dict[str, float]:
    """HuggingFace-compatible metrics callback. Extracts predictions from raw token IDs."""
    predictions, labels = preds
    # SFTTrainer returns (predictions, labels) where both are logit arrays
    # For classification, we need to extract predicted text — use compute_metrics_only=False
    # and handle via EvalPredictor instead.
    return {}  # Metrics computed externally via EvalPredictor


class EvalPredictor:
    """Run inference on eval set after each epoch, print metrics."""

    def __init__(self, eval_data: list[dict], tokenizer: AutoTokenizer):
        self.eval_data = eval_data
        self.tokenizer = tokenizer

    def classify(self, model: torch.nn.Module, review: str) -> str:
        """Classify a single review using the fine-tuned model."""
        messages = [
            {"role": "system", "content": "Ты — классификатор тональности отзывов. Определи категорию отзыва.\nКатегории: крайне негативный, негативный, нейтральный, позитивный.\nОтвечай только названием категории."},
            {"role": "user", "content": review},
        ]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=16,
                temperature=0.0,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Extract only the generated part
        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        prediction = self.tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        return prediction

    def evaluate(self, model: torch.nn.Module) -> EvaluationResult:
        """Full evaluation on eval set."""
        predictions, actuals, details = [], [], []
        for i, record in enumerate(self.eval_data):
            user_text = record["messages"][1]["content"]
            actual = record["messages"][2]["content"].strip()
            pred = self.classify(model, user_text).strip()
            predictions.append(pred)
            actuals.append(actual)
            details.append({
                "index": i,
                "user_content": user_text[:100],
                "predicted": pred,
                "actual": actual,
                "correct": pred == actual,
            })

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

        return EvaluationResult(
            accuracy=round(acc, 4),
            macro_f1=round(m_f1, 4),
            macro_precision=round(m_p, 4),
            macro_recall=round(m_r, 4),
            weighted_f1=round(w_f1, 4),
            per_class=per_class,
            confusion_matrix=cm,
            report=report,
            predictions=details,
        )

    def print_report(self, result: EvaluationResult, epoch: int | None = None) -> None:
        """Pretty-print evaluation results."""
        header = f"Epoch {epoch}" if epoch else "Final"
        console.rule(f"[bold green] Evaluation — {header} [/]")
        console.print(f"  Accuracy:   [bold]{result.accuracy:.4f}[/]")
        console.print(f"  Macro F1:   [bold]{result.macro_f1:.4f}[/] (P={result.macro_precision:.4f}, R={result.macro_recall:.4f})")
        console.print(f"  Weighted F1:[bold]{result.weighted_f1:.4f}[/]")
        console.print()

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Class")
        table.add_column("Prec.")
        table.add_column("Recall")
        table.add_column("F1")
        table.add_column("N")
        for label in LABELED_CATEGORIES:
            m = result.per_class[label]
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
            for val in result.confusion_matrix[i]:
                row.append(str(val))
            cm_table.add_row(*row)
        console.print(cm_table)

        # Misclassifications
        wrong = [p for p in result.predictions if not p["correct"]]
        if wrong:
            console.print(f"\n[bold red]Misclassifications ({len(wrong)})[/]")
            for p in wrong:
                console.print(f"  #{p['index']+1} pred=[red]{p['predicted']}[/] gold=[green]{p['actual']}[/]")


# ─── Training ─────────────────────────────────────────────────
def train(
    train_path: Path,
    eval_path: Path,
    output_dir: Path,
    model_name: str = MODEL_NAME,
    num_epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 2e-4,
) -> None:
    """Full training pipeline."""
    set_seed(42)

    console.rule(f"[bold yellow]QLoRA Fine-Tuning: {Path(model_name).name}[/]")
    console.print(f"GPU:          [bold]{torch.cuda.get_device_name(0)}[/]")
    console.print(f"VRAM:         [bold]{torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB[/]")
    console.print(f"Train set:    {train_path.name} ({len(load_jsonl(train_path))} samples)")
    console.print(f"Eval set:     {eval_path.name} ({len(load_jsonl(eval_path))} samples)")
    console.print(f"Output:       {output_dir}")
    console.print(f"Epochs:       {num_epochs} | Batch: {batch_size} | LR: {learning_rate}")

    # Load tokenizer
    console.print("\n[bold cyan]Loading tokenizer...[/]")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    # Load model
    model = load_model_quantized(model_name)

    # Apply LoRA
    model = apply_lora(model)
    model.gradient_checkpointing_enable()
    model.gradient_checkpointing_kwargs = {"use_reentrant": False}

    # Prepare datasets
    console.print("[bold cyan]Preparing datasets...[/]")
    dataset = prepare_dataset(train_path, eval_path, tokenizer)
    console.print(f"  Train: {len(dataset['train'])} | Eval: {len(dataset['eval'])}")

    # Eval predictor
    eval_predictor = EvalPredictor(load_jsonl(eval_path), tokenizer)

    # Training args
    console.print("[bold cyan]Configuring SFTTrainer...[/]")
    training_args = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=2,
        gradient_checkpointing=True,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        fp16=False,
        bf16=False,
        logging_steps=2,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        report_to="none",
        seed=42,
        max_steps=0,
        max_length=1024,
        packing=False,
        dataset_text_field="text",
        remove_unused_columns=False,
        optim="paged_adamw_8bit",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["eval"],
    )

    from transformers import TrainerCallback

    class PostEpochEval(TrainerCallback):
        def on_evaluate(self, args, state, control, metrics=None, **kwargs):
            # Estimate current epoch
            current_epoch = int(state.epoch)
            if current_epoch > 0 and current_epoch % 1.0 == 0:
                console.print(f"\n[yellow]── Evaluation after epoch {current_epoch} ──[/]")
                model.eval()
                try:
                    result = eval_predictor.evaluate(model)
                    eval_predictor.print_report(result, epoch=current_epoch)
                finally:
                    model.train()
            return control

    trainer.add_callback(PostEpochEval())

    # Train
    console.print("\n[bold green]━━━ START TRAINING ━━━[/]\n")
    train_result = trainer.train()
    console.print(f"\n[bold]Training loss: {train_result.training_loss:.4f}[/]")

    # Final evaluation
    console.print("\n[bold green]━━━ FINAL EVALUATION ━━━[/]\n")
    model.eval()
    result = eval_predictor.evaluate(model)
    eval_predictor.print_report(result)

    # Save adapter
    adapter_dir = output_dir / "adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    console.print(f"\n[green]✓ Adapter saved to {adapter_dir}[/]")

    # Save merged model
    console.print("[bold cyan]Saving merged model...[/]")
    merged_dir = output_dir / "merged"
    merged_dir.mkdir(parents=True, exist_ok=True)
    merged_model = model.merge_and_unload()
    merged_model.save_pretrained(str(merged_dir))
    tokenizer.save_pretrained(str(merged_dir))
    console.print(f"[green]✓ Merged model saved to {merged_dir}[/]")

    # Save metrics
    metrics_path = output_dir / "results.json"
    metrics_data = {
        "model": model_name,
        "fine_tuning": "qlora",
        "lora_r": 16,
        "lora_alpha": 32,
        "epochs": num_epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "training_loss": round(train_result.training_loss, 4),
        "eval_accuracy": result.accuracy,
        "eval_macro_f1": result.macro_f1,
        "eval_weighted_f1": result.weighted_f1,
        "per_class": result.per_class,
        "confusion_matrix": result.confusion_matrix,
        "classification_report": result.report,
        "predictions": result.predictions,
    }
    metrics_path.write_text(
        json.dumps(metrics_data, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    console.print(f"[green]✓ Metrics saved to {metrics_path}[/]")


# ─── Entry point ──────────────────────────────────────────────
def parse_args(argv: list[str]) -> dict[str, Any]:
    """Parse CLI arguments."""
    opts: dict[str, Any] = {
        "train_path": DEFAULT_TRAIN,
        "eval_path": DEFAULT_EVAL,
        "output_dir": DEFAULT_OUTPUT,
        "model_name": MODEL_NAME,
        "num_epochs": 3,
        "batch_size": 4,
        "learning_rate": 2e-4,
    }
    i = 0
    while i < len(argv):
        if argv[i] == "--train-path" and i + 1 < len(argv):
            opts["train_path"] = Path(argv[i + 1])
        elif argv[i] == "--eval-path" and i + 1 < len(argv):
            opts["eval_path"] = Path(argv[i + 1])
        elif argv[i] == "--output-dir" and i + 1 < len(argv):
            opts["output_dir"] = Path(argv[i + 1])
        elif argv[i] == "--model" and i + 1 < len(argv):
            opts["model_name"] = argv[i + 1]
        elif argv[i] == "--epochs" and i + 1 < len(argv):
            opts["num_epochs"] = int(argv[i + 1])
        elif argv[i] == "--batch-size" and i + 1 < len(argv):
            opts["batch_size"] = int(argv[i + 1])
        elif argv[i] == "--lr" and i + 1 < len(argv):
            opts["learning_rate"] = float(argv[i + 1])
        i += 1
    return opts


def main() -> int:
    opts = parse_args(sys.argv[1:])

    # GPU check
    if not torch.cuda.is_available():
        console.print("[red]Error: CUDA not available. QLoRA requires GPU.[/]")
        return 1

    gpu_name = torch.cuda.get_device_name(0)
    total_vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    console.print(f"✓ CUDA available: {gpu_name} ({total_vram:.1f} GB VRAM)")
    if total_vram < 12:
        console.print(f"[yellow]Warning: {total_vram:.1f} GB VRAM is low. Minimum recommended: 12 GB.[/]")

    # File checks
    if not opts["train_path"].exists():
        console.print(f"[red]Error: train file not found: {opts['train_path']}[/]")
        return 1
    if not opts["eval_path"].exists():
        console.print(f"[red]Error: eval file not found: {opts['eval_path']}[/]")
        return 1

    # Run training
    train(**opts)
    console.print("\n[bold green]━━━ DONE ━━━[/]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
