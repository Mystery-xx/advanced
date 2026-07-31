# QLoRA Fine-Tuning — Sentiment Classification

4-bit quantized LoRA fine-tuning of **Qwen2.5-14B-Instruct** for Russian review sentiment classification using Hugging Face stack.

## Hardware Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **GPU** | 12 GB VRAM (RTX 3060/4070) | 24 GB VRAM (RTX 3090/4090) |
| **CPU RAM** | 32 GB | 64 GB |
| **Disk** | 30 GB free (model + adapters) | 60 GB free |

## Stack

| Library | Purpose |
|---------|---------|
| `transformers` | Model/tokenizer loading |
| `peft` | LoRA adapter configuration |
| `bitsandbytes` | 4-bit (NF4) quantization |
| `trl` | SFTTrainer (Supervised Fine-Tuning) |
| `accelerate` | Multi-GPU / CPU offload (auto) |
| `datasets` | HuggingFace Dataset utilities |
| `scikit-learn` | Evaluation metrics (accuracy, F1, confusion matrix) |

## Setup

Requires **Python 3.12 or 3.13** (Python 3.14+ not yet supported by PyTorch).

```bash
cd test-project/finetune/qlora

# Option A: Using uv (recommended — auto-provisions Python 3.13)
uv venv .venv --python 3.13
source .venv/bin/activate
uv pip install -r requirements.txt

# Option B: Using system Python 3.12
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Verify GPU
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0)}')"
```

> ⚠️ **On some systems** (WSL, custom Linux), NVIDIA CUDA libraries may need `LD_LIBRARY_PATH` set:
> ```bash
> CUDA_VENV=$(find .venv -path '*/site-packages/nvidia/cudnn/lib' -type d 2>/dev/null | head -1)
> if [ -d "$CUDA_VENV" ]; then
>   for d in .venv/lib/*/site-packages/nvidia/*/lib .venv/lib/*/site-packages/cusparselt/lib; do
>     [ -d "$d" ] && export LD_LIBRARY_PATH="$d:$LD_LIBRARY_PATH"
>   done
> fi
> ```

## Dataset

Pre-formatted JSONL in `../dataset/`:
- `train.jsonl` — 80 samples (4 categories × 20 each)
- `eval.jsonl` — 20 samples

Format: conversation with system/user/assistant roles.

```json
{"messages": [
  {"role": "system", "content": "Ты — классификатор тональности..."},
  {"role": "user", "content": "текст отзыва"},
  {"role": "assistant", "content": "позитивный"}
]}
```

Categories: `крайне негативный`, `негативный`, `нейтральный`, `позитивный`

## Training

### Quick start

```bash
python train.py
```

### With custom paths

```bash
python train.py \
  --train-path ../dataset/train.jsonl \
  --eval-path ../dataset/eval.jsonl \
  --output-dir outputs
```

### All options

```bash
python train.py \
  --train-path ../dataset/train.jsonl \
  --eval-path ../dataset/eval.jsonl \
  --output-dir outputs \
  --model Qwen/Qwen2.5-14B-Instruct \
  --epochs 3 \
  --batch-size 4 \
  --lr 0.0002
```

### Default hyperparameters

| Parameter | Value |
|-----------|-------|
| Model | Qwen2.5-14B-Instruct |
| Quantization | NF4 (4-bit) |
| LoRA rank (r) | 16 |
| LoRA alpha | 32 |
| LoRA dropout | 0.05 |
| Target modules | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |
| Epochs | 3 |
| Batch size | 4 |
| Gradient accumulation | 2 |
| Learning rate | 2e-4 |
| Scheduler | Cosine with 5% warmup |
| Optimizer | paged_adamw_8bit |
| Weight decay | 0.01 |

## Inference

### Evaluate on eval set (auto-detects adapter)

```bash
python inference.py
```

### Specify adapter or merged model

```bash
# Load adapter
python inference.py --adapter-path outputs/adapter

# Load merged
python inference.py --merged-path outputs/merged

# Interactive mode
python inference.py --interactive
```

Results saved to `inference_results.json` with full metrics.

## Output Structure

```
outputs/
├── adapter/
│   ├── adapter_config.json
│   ├── adapter_model.safetensors
│   ├── special_tokens_map.json
│   └── tokenizer.model
├── merged/
│   ├── model.safetensors
│   └── config.json
├── results.json          # Training + eval metrics
└── checkpoints/          # Per-epoch checkpoints
```

## Results Comparison

| Method | Accuracy | Macro F1 | Weighted F1 |
|--------|----------|----------|-------------|
| Baseline (Ollama, zero-shot) | 80.0% | 77.1% | 81.3% |
| QLoRA (target) | 85-90%+ | TBD | TBD |

## Troubleshooting

### OOM (CUDA out of memory)
- Reduce `--batch-size 2` or `--batch-size 1`
- Reduce `--epochs 2`
- Use `max_seq_length=512` in train.py

### bitsandbytes import error
```bash
pip install --upgrade bitsandbytes
# Verify: python3 -c "import bitsandbytes; print(bnb.__version__)"
```

### Model download too slow
```bash
# Use HF mirror
export HF_ENDPOINT=https://hf-mirror.com

# Or download manually
huggingface-cli download Qwen/Qwen2.5-14B-Instruct --local-dir ./models/qwen2.5-14b
```

### CUDA not detected
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
# If False, reinstall PyTorch with CUDA:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

## Notes

- **Full fine-tuning NOT used** — 14B model requires ~140GB VRAM for full weights update
- **Adapter size** — ~100-200MB (vs 28GB for full model)
- **Merged model** — useful for deployment, ~28GB but standalone (no LoRA runtime needed)
- Original base model is preserved — adapter is additive
