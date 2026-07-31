# QLoRA Fine-Tuning — Llama-3.2-1B-Instruct

4-bit quantized LoRA fine-tuning of **meta-llama/Llama-3.2-1B-Instruct** for Russian review sentiment classification.

## Why Llama-3.2-1B?

- Zero-shot accuracy was 20% (answer bias: "Нейтральный" on everything)
- Fine-tuning on domain data targets 70-80%+ accuracy
- 1B model is much faster than 14B even with fine-tuning overhead
- Same LoRA target modules as Qwen (share Transformer architecture)

## Hardware Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **GPU** | 8 GB VRAM (RTX 3060/4060) | 16 GB VRAM (RTX 4080) |
| **CPU RAM** | 16 GB | 32 GB |
| **Disk** | 10 GB free (model + adapters) | 20 GB free |
| **HuggingFace** | Login + model approval required | |

## Prerequisites

### 1. HuggingFace Access (REQUIRED)

Llama-3.2-1B-Instruct is a **gated model**. You must:

```bash
# Step 1: Request access (one-time)
# Visit: https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
# Click "Access repo" → "Request access" → Accept Meta's license

# Step 2: Generate token
# Visit: https://huggingface.co/settings/tokens

# Step 3: Set environment variable
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OR login interactively
huggingface-cli login
```

### 2. Python Environment

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
```

## Dataset

Pre-formatted JSONL in `../dataset/`:
- `train.jsonl` — 80 samples (4 categories × 20 each)
- `eval.jsonl` — 20 samples

Format: conversation with system/user/assistant roles. Categories: `крайне негативный`, `негативный`, `нейтральный`, `позитивный`

## Training

### Prerequisites

```bash
# Set HuggingFace token
export HF_TOKEN=hf_your_token_here

# Verify setup
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0)}')"
```

### Quick start

```bash
python train_llama3_1b.py
```

### With custom paths

```bash
python train_llama3_1b.py \
  --train-path ../dataset/train.jsonl \
  --eval-path ../dataset/eval.jsonl \
  --output-dir outputs/llama3_1b_adapter
```

### All options

```bash
python train_llama3_1b.py \
  --train-path ../dataset/train.jsonl \
  --eval-path ../dataset/eval.jsonl \
  --output-dir outputs/llama3_1b_adapter \
  --epochs 3 \
  --batch-size 8 \
  --lr 0.0002
```

### Default hyperparameters

| Parameter | Value | Note |
|-----------|-------|------|
| Model | meta-llama/Llama-3.2-1B-Instruct | Gated |
| Quantization | NF4 (4-bit) | Same as Qwen |
| LoRA rank (r) | 16 | Same as Qwen |
| LoRA alpha | 32 | Same as Qwen |
| LoRA dropout | 0.05 | Same as Qwen |
| Target modules | q,k,v,o + gate,up,down | Same Transformer arch |
| Epochs | 3 | |
| Batch size | 8 | Larger than Qwen (4) |
| Gradient accumulation | 2 | |
| Learning rate | 2e-4 | |
| Scheduler | Cosine with 5% warmup | |
| Optimizer | paged_adamw_8bit | |

## Inference

### Evaluate on eval set

```bash
# With adapter (default location)
python inference_llama3_1b.py

# Specify adapter path
python inference_llama3_1b.py --adapter-path outputs/llama3_1b_adapter/adapter

# With merged model
python inference_llama3_1b.py --merged-path outputs/llama3_1b_adapter/merged

# Interactive mode
python inference_llama3_1b.py --interactive
```

Results saved to `inference_llama3_1b_results.json`.

## Output Structure

```
outputs/llama3_1b_adapter/
├── adapter/
│   ├── adapter_config.json
│   ├── adapter_model.safetensors    # ~20-40 MB (tiny!)
│   ├── special_tokens_map.json
│   └── tokenizer.model
├── merged/
│   ├── model.safetensors             # ~2.3 GB (1B model)
│   └── config.json
└── results.json                      # Training + eval metrics
```

## Expected Results

| Metric | Target |
|--------|--------|
| Accuracy | 70-80%+ |
| Macro F1 | 65-75%+ |
| Training time | ~5-10 min on RTX 4080 |
| Inference speed | ~10-50ms per sample |

## Comparison with Qwen Training

| Aspect | Qwen2.5-14B | Llama-3.2-1B |
|--------|-------------|--------------|
| VRAM required | 12 GB+ | 8 GB+ |
| Training time | ~30-60 min | ~5-10 min |
| Adapter size | ~100-200 MB | ~20-40 MB |
| Inference speed | 200-500ms | 10-50ms |
| HF access | Public | Gated (approval) |

## Troubleshooting

### HuggingFace access denied
```
huggingface_hub.utils._errors.GatedRepoError: ...
```
→ Request access: https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
→ Wait for approval (usually instant for Meta Community License)
→ Verify: `huggingface-cli whoami`

### Model download too slow
```bash
# Use HF mirror
export HF_ENDPOINT=https://hf-mirror.com

# Or download manually first
huggingface-cli download meta-llama/Llama-3.2-1B-Instruct --local-dir ./models/llama3.2-1b
```

### OOM (CUDA out of memory)
- Reduce `--batch-size 4` or `--batch-size 2`
- Reduce `--epochs 2`

### CUDA not detected
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
# If False, reinstall PyTorch with CUDA:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

### bitsandbytes import error
```bash
pip install --upgrade bitsandbytes
```

## Notes

- **Adapter is tiny** — ~20-40 MB (vs 2.3GB for merged model)
- **Merge and Unload** creates a standalone model usable without PEFT runtime
- **Original base model preserved** — adapter is additive LoRA weights
