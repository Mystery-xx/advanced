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
Fine-tune local LLM via Ollama API.

Supports two modes:
  — Ollama >= 0.9.x : Native /api/train (full weight fine-tuning)
  — Ollama  < 0.9.x : /api/create with few-shot Modelfile (prompt customisation)

Usage:
    uv run finetune.py
    uv run finetune.py --model qwen3:14b --tag my-model
    uv run finetune.py --train-path custom/train.jsonl --epochs 5
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# ─── Constants ────────────────────────────────────────────────

OLLAMA_URL: Final[str] = "http://localhost:11434"
DEFAULT_MODEL: Final[str] = "qwen3:14b"
DEFAULT_TAG: Final[str] = "qwen3:14b-sentiment"
DEFAULT_TRAIN_PATH: Final[str] = str(Path("..") / "dataset" / "train.jsonl")
DEFAULT_EVAL_PATH: Final[str] = str(Path("..") / "dataset" / "eval.jsonl")

LABELED_CATEGORIES: Final[list[str]] = [
    "крайне негативный", "негативный", "нейтральный", "позитивный",
]

SYSTEM_PROMPT: Final[str] = (
    "Ты — классификатор тональности отзывов. Определи категорию отзыва.\n"
    "Категории: крайне негативный, негативный, нейтральный, позитивный.\n"
    "Отвечай только названием категории."
)

# /api/train defaults
DEFAULT_EPOCHS: Final[int] = 3
DEFAULT_LEARNING_RATE: Final[float] = 5e-5
DEFAULT_BATCH_SIZE: Final[int] = 4

# ─── Data models ──────────────────────────────────────────────


@dataclass
class TrainingResult:
    output_model: str
    mode: str  | None = None  # "train" or "create"
    epochs: int | None = None
    epoch_losses: list[float] | None = field(default_factory=list)
    duration_secs: float | None = None
    eval_accuracy: float | None = None


# ─── Helpers ──────────────────────────────────────────────────


def load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file; skip blank lines, raise on bad JSON."""
    records: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if raw:
            records.append(json.loads(raw))
    return records


def extract_fields(example: dict) -> tuple[str, str, str]:
    """Return (system, user, assistant) from messages-format example."""
    system = user = assistant = ""
    for msg in example.get("messages", []):
        match msg["role"]:
            case "system": system = msg["content"]
            case "user":   user   = msg["content"]
            case "assistant": assistant = msg["content"]
    return system, user, assistant


def validate_messages_format(records: list[dict]) -> None:
    """Ensure every record has a valid messages array."""
    for i, rec in enumerate(records):
        if "messages" not in rec:
            raise ValueError(f"Line {i + 1}: missing 'messages' key")
        roles = {m["role"] for m in rec["messages"]}
        if "user" not in roles or "assistant" not in roles:
            raise ValueError(
                f"Line {i + 1}: messages must contain 'user' and 'assistant' roles"
            )


def convert_to_ollama_train(records: list[dict]) -> str:
    """
    Convert train.jsonl to Ollama /api/train Modelfile format.

    /api/train expects a Modelfile with FROM + message commands:

        FROM base_model
        message user "..."
        message assistant "..."
        message user "..."
        message assistant "..."

    We also keep a raw JSONL copy for reference.
    """
    validate_messages_format(records)

    # Modelfile for /api/train
    lines = []
    for rec in records:
        for msg in rec["messages"]:
            role = msg["role"]
            content = msg["content"]
            if role in ("user", "assistant"):
                # Escape quotes and newlines for Modelfile literal
                escaped = content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
                lines.append(f'message {role} "{escaped}"')

    return "\n".join(lines)


def classify(text: str, model: str) -> str:
    """Single-shot classification via /api/chat."""
    resp = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": text},
            ],
            "temperature": 0.0,
            "stream": False,
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


# ─── Ollama checks ────────────────────────────────────────────


def check_ollama_running() -> str:
    """Return Ollama version string or raise."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/version", timeout=10)
    except requests.ConnectionError:
        raise EnvironmentError(
            f"Cannot connect to Ollama at {OLLAMA_URL}. Start it with: ollama serve"
        )
    resp.raise_for_status()
    return resp.json().get("version", "unknown")


def check_model_available(model: str) -> None:
    """Raise if the base model is not in Ollama's library."""
    resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
    resp.raise_for_status()
    names = [m["name"] for m in resp.json().get("models", [])]
    if model not in names:
        raise EnvironmentError(
            f"Model '{model}' not found in Ollama. "
            f"Available: {names}. Pull it with: ollama pull {model}"
        )


def has_train_endpoint() -> bool:
    """Probe /api/train — available in Ollama >= 0.9.x."""
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/train",
            json={"model": "nonexistent-test"},
            timeout=5,
        )
        return resp.status_code != 404
    except Exception:
        return False


# ─── Training (Ollama >= 0.9.x) ──────────────────────────────


def train_native(
    model: str,
    tag: str,
    dataset_text: str,
    epochs: int,
    learning_rate: float,
    batch_size: int,
    console: Console,
) -> TrainingResult:
    """
    Full fine-tuning via /api/train.

    Steps:
      1. POST /api/copy  model:tag  ->  model:tag-training
      2. POST /api/train with dataset + params
      3. Resulting model is tagged as `tag`
    """
    training_name = f"{model.split(':')[0]}:tag-training"
    output_model = tag  # e.g. qwen3:14b-sentiment

    # Step 1: prepare training model
    console.print(f"\n  [dim]Preparing training copy: {training_name}[/]")
    prep = requests.post(
        f"{OLLAMA_URL}/api/copy",
        json={"source": model, "destination": training_name},
        timeout=60,
    )
    prep.raise_for_status()

    # Step 2: Build Modelfile for /api/train
    modelfile_train = f"FROM {model}\n{dataset_text}"

    # POST /api/train
    payload = {
        "model": training_name,
        "modelfile": modelfile_train,
        "stream": True,
        "quantize": "",
        "epochs": epochs,
        "learning_rate": learning_rate,
        "batch_size": batch_size,
    }
    console.print(
        f"  Training  [bold]{model}[/]  →  [bold]{output_model}[/]  "
        f"({epochs} epochs, lr={learning_rate}, bs={batch_size})"
    )

    epoch_losses: list[float] = []
    t0 = time.perf_counter()

    with Progress(
        SpinnerColumn(), TextColumn("{task.description}"), console=console
    ) as pg:
        task_id = pg.add_task("Training in progress…")
        with requests.post(
            f"{OLLAMA_URL}/api/train",
            json=payload,
            stream=True,
            timeout=3600,
        ) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_lines(decode_unicode=True):
                if not chunk.strip():
                    continue
                data = json.loads(chunk)
                desc = data.get("status", "")

                if "epoch" in desc.lower() and "loss" in desc.lower():
                    # e.g. "epoch 1 — loss 0.1234"
                    loss = float(desc.split("loss")[-1].strip())
                    epoch_losses.append(loss)

                pg.update(task_id, description=desc)

    elapsed = time.perf_counter() - t0

    # Step 3: rename to output tag
    console.print(f"\n  [dim]Renaming to output tag: {output_model}[/]")
    rename = requests.post(
        f"{OLLAMA_URL}/api/copy",
        json={"source": training_name, "destination": output_model},
        timeout=60,
    )
    rename.raise_for_status()

    # Clean up intermediate
    try:
        resp_del = requests.delete(
            f"{OLLAMA_URL}/api/delete",
            data=json.dumps({"name": training_name}),
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if resp_del.status_code == 405:
            # Fallback: some Ollama versions use POST for delete
            requests.post(
                f"{OLLAMA_URL}/api/delete",
                json={"name": training_name},
                timeout=30,
            )
    except Exception:
        pass

    return TrainingResult(
        output_model=output_model,
        mode="train",
        epochs=epochs,
        epoch_losses=epoch_losses,
        duration_secs=round(elapsed, 2),
    )


# ─── Prompt customisation (Ollama < 0.9.x) ───────────────────


def build_modelfile(
    model: str,
    examples: list[dict],
    few_shot_count: int = 8,
) -> str:
    """
    Build a Modelfile that embeds few-shot examples in the system prompt.

    This does NOT change model weights — it customises inference behaviour
    via prompt engineering, which is the closest Ollama < 0.9.x can get.
    """
    few_shot = []
    seen_users = set()
    for ex in examples:
        _, user, assistant = extract_fields(ex)
        if user not in seen_users:
            seen_users.add(user)
            few_shot.append((user[:120], assistant))
        if len(few_shot) >= few_shot_count:
            break

    shots = "\n\n".join(
        f"[Пример]\nОтзыв: \"{u}\"\nОтвет: {a}" for u, a in few_shot
    )

    enhanced_prompt = f"{SYSTEM_PROMPT}\n\nПримеры классификации:\n{shots}"

    return (
        f"FROM {model}\n"
        f'SYSTEM """{enhanced_prompt}\"""\n'
        f"PARAMETER temperature 0.0\n"
        f"PARAMETER seed 42\n"
    )


def create_custom_model(
    model: str,
    tag: str,
    examples: list[dict],
    console: Console,
) -> TrainingResult:
    """
    Create a specialised model via /api/create with few-shot system prompt.

    Equivalent to:
        ollama create mymodel -f <(echo "$MODELFILTER")
    """
    t0 = time.perf_counter()
    modelfile = build_modelfile(model, examples)

    console.print(f"\n  [dim]Writing Modelfile ({len(modelfile)} bytes)[/]\n")
    console.print(modelfile)
    console.print()

    # Save Modelfile for reproducibility
    modelfile_path = Path(__file__).resolve().parent / "Modelfile"
    modelfile_path.write_text(modelfile, encoding="utf-8")
    console.print(f"  [dim]Saved: {modelfile_path}[/]")

    console.print(f"\n  Creating model  [bold]{tag}[/]  (few-shot customisation)…")
    resp = requests.post(
        f"{OLLAMA_URL}/api/create",
        json={
            "model": tag,
            "from": model,
            "modelfile": modelfile,
            "stream": True,
        },
        timeout=300,
    )
    resp.raise_for_status()

    # Stream status
    for chunk in resp.iter_lines(decode_unicode=True):
        if not chunk.strip():
            continue
        data = json.loads(chunk)
        desc = data.get("status", "")
        if desc:
            console.print(f"    {desc}")

    elapsed = time.perf_counter() - t0

    return TrainingResult(
        output_model=tag,
        mode="create",
        duration_secs=round(elapsed, 2),
    )


# ─── Quick evaluation ─────────────────────────────────────────


def quick_eval(output_model: str, eval_path: Path, console: Console) -> float | None:
    """Run eval on the fine-tuned model. Returns accuracy or None on error."""
    if not eval_path.exists():
        console.print(f"  [dim]Eval file not found: {eval_path} — skipping[/]")
        return None

    records = load_jsonl(eval_path)
    console.print(f"\n  Quick evaluation ({len(records)} examples)…")

    correct = 0
    for rec in records:
        _, user_text, actual = extract_fields(rec)
        try:
            pred = classify(user_text, output_model)
        except Exception:
            pred = ""
        if pred == actual:
            correct += 1

    acc = correct / len(records) if records else 0.0
    console.print(f"  Accuracy:  [bold]{acc:.4f}[/] ({correct}/{len(records)})")
    return round(acc, 4)


# ─── CLI ──────────────────────────────────────────────────────


def parse_args(argv: list[str]) -> dict:
    """Minimal argument parser."""
    cfg: dict = {
        "model": DEFAULT_MODEL,
        "tag": DEFAULT_TAG,
        "train_path": Path(DEFAULT_TRAIN_PATH).resolve(),
        "eval_path": Path(DEFAULT_EVAL_PATH).resolve(),
        "epochs": DEFAULT_EPOCHS,
        "learning_rate": DEFAULT_LEARNING_RATE,
        "batch_size": DEFAULT_BATCH_SIZE,
        "skip_eval": False,
    }

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in {"--model"} and i + 1 < len(argv):
            cfg["model"] = argv[i + 1]
        elif arg in {"--tag"} and i + 1 < len(argv):
            cfg["tag"] = argv[i + 1]
        elif arg in {"--train-path"} and i + 1 < len(argv):
            cfg["train_path"] = Path(argv[i + 1]).resolve()
        elif arg in {"--eval-path"} and i + 1 < len(argv):
            cfg["eval_path"] = Path(argv[i + 1]).resolve()
        elif arg in {"--epochs"} and i + 1 < len(argv):
            cfg["epochs"] = int(argv[i + 1])
        elif arg in {"--learning-rate"} and i + 1 < len(argv):
            cfg["learning_rate"] = float(argv[i + 1])
        elif arg in {"--batch-size"} and i + 1 < len(argv):
            cfg["batch_size"] = int(argv[i + 1])
        elif arg == "--skip-eval":
            cfg["skip_eval"] = True
        i += 1

    return cfg


def main() -> int:
    console = Console()
    cfg = parse_args(sys.argv[1:])

    model       = cfg["model"]
    tag         = cfg["tag"]
    train_path  = cfg["train_path"]
    eval_path   = cfg["eval_path"]
    epochs      = cfg["epochs"]
    learning_rate = cfg["learning_rate"]
    batch_size  = cfg["batch_size"]
    skip_eval   = cfg["skip_eval"]

    console.rule(f"Ollama Fine-tuning — {model} → {tag}")

    # ── 0. Prerequisites ──────────────────────────────
    console.print(f"Ollama URL : {OLLAMA_URL}")
    console.print(f"Train file : {train_path}")
    console.print(f"Eval file  : {eval_path}")
    console.print(f"Output tag : {tag}")

    # Check Ollama
    version = check_ollama_running()
    console.print(f"Ollama version: [green]{version}[/]")
    check_model_available(model)
    console.print(f"Base model: [green]{model}[/]")

    # Check train file
    if not train_path.exists():
        console.print(f"[red]Error: train file not found: {train_path}[/]")
        return 1

    records = load_jsonl(train_path)
    console.print(f"Training samples: [green]{len(records)}[/]")

    # Check eval file
    if eval_path.exists():
        eval_rec_count = len(load_jsonl(eval_path))
        console.print(f"Eval samples: [green]{eval_rec_count}[/]")
    else:
        console.print(f"[yellow]Warning: eval file not found: {eval_path}[/]")

    # ── 1. Convert dataset ────────────────────────────
    console.print("\n[dim]Converting dataset to Ollama format…[/]")
    dataset_text = convert_to_ollama_train(records)

    ollama_dataset = Path(__file__).resolve().parent / "train_ollama.jsonl"
    ollama_dataset.write_text(dataset_text, encoding="utf-8")
    console.print(f"Saved: [green]{ollama_dataset}[/] ({len(dataset_text)} bytes)")

    # ── 2. Choose mode ────────────────────────────────
    train_available = has_train_endpoint()

    if train_available:
        console.print("\n[bold green]✓[/] /api/train available — using native fine-tuning")
        result = train_native(
            model=model,
            tag=tag,
            dataset_text=dataset_text,
            epochs=epochs,
            learning_rate=learning_rate,
            batch_size=batch_size,
            console=console,
        )
    else:
        console.print(
            "\n[yellow]⚠[/] /api/train not available (Ollama < 0.9.x)."
            "\n[yellow]   Using /api/create with few-shot prompt customisation"
            " (no weight changes).[/]"
        )
        result = create_custom_model(
            model=model,
            tag=tag,
            examples=records,
            console=console,
        )

    # ── 3. Quick evaluation ───────────────────────────
    if not skip_eval:
        acc = quick_eval(tag, eval_path, console)
        if acc is not None:
            result.eval_accuracy = acc

    # ── 4. Save summary ───────────────────────────────
    summary = {
        "model": model,
        "output_tag": result.output_model,
        "mode": result.mode,
        "ollama_version": version,
        "train_samples": len(records),
        "epochs": result.epochs,
        "epoch_losses": result.epoch_losses,
        "duration_secs": result.duration_secs,
        "eval_accuracy": result.eval_accuracy,
        "ollama_url": OLLAMA_URL,
        "dataset_path": str(train_path),
        "modelfile": str(Path(__file__).resolve().parent / "Modelfile"),
    }

    results_path = Path(__file__).resolve().parent / "training_results.json"
    results_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    console.print(f"\n[green]✓[/] Training complete → [bold]{tag}[/]")
    console.print(f"[green]✓[/] Results saved to [bold]{results_path}[/]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
