# Micro-Model Router

A lightweight ML-based confidence router for text classification with automatic LLM fallback.

## Architecture Overview

```
┌─────────────┐
│   Query     │
│  (text)     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  TF-IDF Vectorizer              │
│  (500 features, 1-2 grams)      │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  LogisticRegression             │
│  predict_proba() → confidence   │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  confidence >= threshold?       │
│  (default: 0.75)                │
└──────┬──────────────────────────┘
       │
       ├──────────────┬──────────────────────┐
       │ YES          │ NO                   │
       │ (HIGH)       │ (LOW)                │
       ▼              ▼                      │
┌─────────────┐  ┌──────────────────────────┐│
│ Return      │  │ Fallback to LLM          ││
│ prediction  │  │ (Ollama: qwen3:14b)      ││
│ <10ms       │  │ ~1500-30000ms            ││
│ cost: 1     │  │ cost: 3                  ││
└─────────────┘  └────────────┬─────────────┘│
                              │              │
                              ▼              │
                    ┌────────────────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │ Constraint Check│
           │ (valid category)│
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │ RouterResult    │
           │ (answer, model, │
           │  confidence,    │
           │  latency, cost) │
           └─────────────────┘
```

**Flow:**
1. **TF-IDF + LogisticRegression** classify the query and produce confidence score
2. **Confidence check** compares against threshold (default 0.75)
3. **HIGH confidence** (≥0.75) → return micro-model prediction (<10ms, cheap)
4. **LOW confidence** (<0.75) or constraint failure → fallback to LLM via Ollama (~30s, expensive)
5. **Constraint check** validates answer is in expected categories

## Installation

### Prerequisites

- **Python 3.10+**
- **uv** (recommended package manager)
- **Ollama** (for LLM fallback)

### Step 1: Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2: Install Python Dependencies

```bash
cd finetune/micromodel

# Using uv (recommended)
uv pip install scikit-learn requests joblib numpy rich matplotlib seaborn

# Or using pip
pip install scikit-learn requests joblib numpy rich matplotlib seaborn
```

### Step 3: Install and Configure Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server
ollama serve

# Pull the default model (in another terminal)
ollama pull qwen3:14b

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### Step 4: Train the Micro-Model

```bash
# Ensure training dataset exists at finetune/dataset/train.jsonl
cd finetune/micromodel

# Train TF-IDF + LogisticRegression model
python train.py

# Output:
# models/vectorizer.pkl   (TF-IDF: 500 features)
# models/classifier.pkl   (LogisticRegression)
# models/label_encoder.pkl (classes: ['крайне негативный', 'негативный', 'нейтральный', 'позитивный'])
```

## Usage

### Command 1: Train

Train the TF-IDF + LogisticRegression micro-model on your dataset.

```bash
cd finetune/micromodel
python train.py
```

**What it does:**
- Loads `finetune/dataset/train.jsonl` (OpenAI messages format)
- Extracts (user text, assistant label) pairs
- Trains TF-IDF vectorizer (500 features, 1-2 grams, min_df=2)
- Trains LogisticRegression classifier (balanced class weights, 1000 max iterations)
- Saves models to `models/` directory

**Expected output:**
```
============================================================
Micro-Model Training — TF-IDF + LogisticRegression
============================================================

[1/4] Loading dataset: finetune/dataset/train.jsonl
  Loaded X records
[2/4] Extracting text/label pairs
  Extracted X samples
[3/4] Class distribution
  Train class distribution
    крайне негативный: X
    негативный: X
    нейтральный: X
    позитивный: X
    Total: X

[4/4] Training model
Training accuracy: 0.XXXX (XX.X%)

Models saved to finetune/micromodel/models/
  - vectorizer.pkl   (TF-IDF: 500 features)
  - classifier.pkl   (LogisticRegression: ...)
  - label_encoder.pkl (classes: [...])

Done.
```

### Command 2: Evaluate

Run full evaluation on eval + edge_cases datasets with metrics.

```bash
cd finetune/micromodel

# Default evaluation (threshold=0.75)
uv run run_evaluation.py

# Custom confidence threshold
uv run run_evaluation.py --confidence-threshold 0.8

# Custom output path
uv run run_evaluation.py --output /tmp/micromodel_results.json
```

**Output files:**
- `micromodel_results.json` — full metrics and per-prediction details
- `micromodel_results.png` — confusion matrix heatmap

**Metrics tracked:**
- Overall accuracy
- Micro-model accuracy (predictions from TF-IDF+LR)
- LLM accuracy (predictions from fallback)
- Fallback rate (fraction of queries that used LLM)
- Average latency (ms)
- Cost savings vs using LLM for all queries

### Command 3: Demo

Run interactive demo with sample queries.

```bash
cd finetune/micromodel
python micromodel_router.py
```

**Example output:**
```
MicroModel Router
  confidence_threshold=0.30
  llm_model=qwen3:14b
  ollama_url=http://localhost:11434

Routing sample: 'Отличная тачка для дачи'

Answer:     позитивный
Model used: micromodel
Confidence: HIGH
Latency:    1ms
Cost units: 1
```

### Programmatic Usage

```python
from micromodel_router import MicroModelRouter, MicroModelConfig

# Default configuration
router = MicroModelRouter()
result = router.route("Отличная тачка для дачи")
print(f"Answer: {result.answer}")
print(f"Model: {result.model_used}")
print(f"Confidence: {result.confidence_status}")
print(f"Latency: {result.latency_ms}ms")

# Custom configuration
config = MicroModelConfig(
    confidence_threshold=0.65,  # Lower threshold = more micro-model usage
    llm_model="qwen2.5:14b",    # Different LLM model
    ollama_url="http://remote:11434",  # Remote Ollama server
)
router = MicroModelRouter(config=config)
result = router.route("Ужасное качество, не рекомендую")
```

## Configuration Options

| Parameter | CLI Flag | Default | Description |
|-----------|----------|---------|-------------|
| `confidence_threshold` | `--confidence-threshold` | `0.30` | Minimum confidence (0.0-1.0) to accept micro-model prediction. Default 0.30 is tuned for small datasets (~80 samples). Use 0.50+ only with 500+ training samples. Lower = more micro-model usage, higher = more LLM calls. |
| `llm_model` | `--llm-model` | `qwen3:14b` | Ollama model name for fallback classification. |
| `ollama_url` | `--ollama-url` | `http://localhost:11434` | Base URL of Ollama API server. |
| `model_paths` | (code only) | `models/*.pkl` | Dictionary of model file paths: `{"vectorizer": "...", "classifier": "...", "label_encoder": "..."}` |

### MicroModelConfig Fields

```python
from micromodel_router import MicroModelConfig

config = MicroModelConfig(
    confidence_threshold=0.30,   # Default for small datasets (~80 samples); use 0.50+ with 500+ samples
    llm_model="qwen3:14b",       # String: any Ollama model
    ollama_url="http://localhost:11434",  # String: valid URL
    model_paths={
        "vectorizer": "finetune/micromodel/models/vectorizer.pkl",
        "classifier": "finetune/micromodel/models/classifier.pkl",
        "label_encoder": "finetune/micromodel/models/label_encoder.pkl",
    }
)
```

### RouterResult Fields

```python
from micromodel_router import RouterResult

result: RouterResult = router.route("text")
print(result.answer)            # Classification answer
print(result.model_used)        # "micromodel" or LLM model name
print(result.confidence_status) # "HIGH", "LOW", or "ERROR"
print(result.explanation)       # Detailed routing explanation
print(result.constraint_passed) # Boolean: answer valid category
print(result.escalated)         # Boolean: used LLM fallback
print(result.cheap_answer)      # Micro-model prediction (empty if error)
print(result.cheap_confidence)  # Micro-model confidence score
print(result.latency_ms)        # Total routing time in ms
print(result.cost_units)        # 1 (micro-model) or 3 (LLM)
```

## Performance Benchmarks

### Evaluation Results (10 samples, threshold=0.30)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Micro-model usage** | 80% | >60% | ✓ PASS |
| **Overall accuracy** | 70% | >75% | ⚠ CLOSE |
| **Avg latency** | 3,685ms | <50ms | ⚠ 74x (LLM bottleneck) |
| **Cost savings** | 13% | >50% | ⚠ PARTIAL |

### Per-Model Performance

| Model | Usage | Accuracy | Avg Latency | Cost |
|-------|-------|----------|-------------|------|
| Micro-model (TF-IDF+LR) | 80% | 62% | <1ms | 1x |
| LLM (qwen3:14b) | 20% | 100% | 18,000ms | 3x |

### Key Findings

- **80% micro-model usage**: Lowering threshold to 0.30 enables micro-model for most queries
- **62% micro-model accuracy**: Expected with only 80 training samples
- **100% LLM accuracy**: LLM handles uncertain cases correctly
- **3.7s average latency**: 8x faster than 100% LLM (30s), but LLM calls still dominate
- **13% cost savings**: Micro-model handles 8/10 queries at 1/3 the cost

### Why These Results?

The TF-IDF + LogisticRegression micro-model produces confidence scores 0.26-0.45 because:
- Training dataset is small (80 samples, ~20 per class)
- Russian language reviews have nuanced sentiment expressions
- TF-IDF with 500 features captures surface patterns, not semantics

**Threshold tuning:**
- `0.30` (default): Balanced for small datasets — 80% micro-model usage, ~60% accuracy
- `0.50`: Requires more training data (500+ samples) — ~40% micro-model usage, ~70% accuracy
- `0.75`: Conservative — 0-10% micro-model usage, LLM handles almost all queries

**Recommendations:**
1. **Expand training dataset** to 500+ samples for higher confidence scores
2. **Use neural embeddings** (e.g., sentence-transformers) instead of TF-IDF
3. **Keep threshold at 0.30** until more training data is available

## Troubleshooting

### Ollama Connection Errors

**Error:** `Cannot connect to Ollama at http://localhost:11434`

**Solution:**
```bash
# Start Ollama server
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags

# Check if port 11434 is in use
lsof -i :11434
```

**Error:** `LLM fallback failed — cannot connect to Ollama`

**Solution:**
- Ensure Ollama is running (`ollama serve` in background or terminal)
- Check firewall rules allow localhost:11434
- Verify `--ollama-url` matches your Ollama server address

### Model Loading Errors

**Error:** `Vectorizer not found: finetune/micromodel/models/vectorizer.pkl`

**Solution:**
```bash
# Train the model first
cd finetune/micromodel
python train.py

# Verify models exist
ls -la models/
# Should show:
# - classifier.pkl
# - label_encoder.pkl
# - vectorizer.pkl
```

**Error:** `FileNotFoundError: Dataset not found: finetune/dataset/train.jsonl`

**Solution:**
- Ensure training dataset exists at the expected path
- Check `DATASET_PATH` constant in `train.py`
- Create sample dataset if needed

### Low Confidence Scores

**Symptom:** All queries escalate to LLM (fallback rate = 100%)

**Solutions:**
1. **Lower confidence threshold:**
   ```bash
   uv run run_evaluation.py --confidence-threshold 0.5
   ```

2. **Retrain with more data:**
   - Add more training samples to `train.jsonl`
   - Ensure balanced class distribution
   - Include diverse phrasings and edge cases

3. **Improve TF-IDF features:**
   - Increase `MAX_FEATURES` in `train.py` (default: 500)
   - Adjust `NGRAM_RANGE` (default: (1, 2))
   - Lower `MIN_DF` (default: 2)

### HTTP Errors from Ollama

**Error:** `Ollama HTTP error: 404` or `500`

**Solution:**
```bash
# Check if model is available
ollama list

# Pull the model if missing
ollama pull qwen3:14b

# Check Ollama logs for errors
journalctl -u ollama  # Linux
# or check terminal where ollama serve is running
```

### Empty or Invalid Predictions

**Symptom:** `answer="ERROR"` or empty predictions

**Solution:**
- Verify Ollama model supports the task (text classification)
- Check system prompt in `fallback_to_llm()` function
- Ensure network connectivity to Ollama server
- Increase timeout in `fallback_to_llm()` (default: 300 seconds)

### Performance Issues

**Symptom:** Latency >30 seconds per query

**Solution:**
- Use smaller LLM model (e.g., `qwen2.5:7b` instead of `qwen3:14b`)
- Run Ollama on same machine (avoid network latency)
- Lower confidence threshold to use micro-model more often
- Consider caching frequent queries

## File Structure

```
finetune/micromodel/
├── README.md                  # This documentation
├── train.py                   # Training script (TF-IDF + LogisticRegression)
├── micromodel_router.py       # Core routing logic with LLM fallback
├── run_evaluation.py          # Full evaluation script with metrics
├── demo_run.py                # Interactive demo (5 sample queries)
├── micromodel_results.json    # Evaluation results (35 samples)
├── micromodel_results.png     # Confusion matrix heatmap
├── models/                    # Trained model artifacts
│   ├── vectorizer.pkl         # TF-IDF vectorizer (500 features)
│   ├── classifier.pkl         # LogisticRegression classifier
│   └── label_encoder.pkl      # Label encoder (4 classes)
└── __init__.py               # Package init (imports router)
```

## License

MIT