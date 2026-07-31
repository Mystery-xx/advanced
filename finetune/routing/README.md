# Model Routing — Confidence-Based Fallback (Cheap → Expensive)

Intelligent request routing between cheap and expensive models with automatic escalation based on confidence evaluation.

## Description

The routing module implements a two-tier model architecture:

1. **First tier**: Fast, cheap model handles all incoming requests
2. **Confidence check**: Evaluates confidence in the cheap model's answer
3. **Fallback**: Low-confidence answers are automatically escalated to the expensive model

This approach optimizes for cost and latency while maintaining accuracy on difficult cases.

### Routing Flow

```
Request → Cheap Model → Confidence Check → HIGH confidence → Return answer
                                    ↓
                              MEDIUM/LOW confidence
                                    ↓
                            Expensive Model → Return answer
```

**Confidence determination:**
- **HIGH**: Constraint passed + confident explanation (answer stays on cheap model)
- **MEDIUM**: Constraint passed but weak explanation (escalates to expensive model)
- **LOW**: Constraint failed (escalates expensive model)

Default configurationates on `MEDIUM` andLOW` confidence.

## Stack/Dependencies

| Dependency | Purpose |
|------------|---------|
| **Python** | 3.10+ |
| `requests` | HTTP client for Ollama API |
| `rich` | Terminal output formatting |
| `scikit-learn` | Metrics computation |
| **Ollama** | Local model server (http://localhost:11434) |

### Required Models

Both models must be loaded in Ollama:

```bash
# Default cheap model (1B parameters)
ollama pull llama3.1:8b

# Default expensive model (14B parameters)
ollama pull qwen3:14b

# Verify both are available
ollama list
```

## Configuration

### Default Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `cheap_model` | `llama3.1:8b` (1B) | Fast model for initial classification |
| `expensive_model` | `qwen3:14b` (14B) | Accurate model for fallback |
| `escalate_on` | `["MEDIUM", "LOW"]` | Confidence levels triggering escalation |
| `use_self_check` | `True` | Enable self-check for confidence evaluation |
| `ollama_url` | `http://localhost:11434` | Ollama API endpoint |

### Cost Model

Relative cost units (not actual USD):

| Model | Cost Units | Rationale |
|-------|------------|-----------|
| Cheap (llama3.1:8b — 1B) | 1 | Baseline cost |
| Expensive (qwen3:14b — 14B) | 15 | 14B / 1B ≈ 15× more resources |

**Cost savings calculation:**
```
Cost savings = (All expensive - Actual cost) / All expensive
             = (3 × N - Σ actual_units) / (3 × N)
```

Where N is the total number of requests.

### Custom Configuration

```bash
# Custom models
uv run model_router.py \
  --cheap-model llama3.1:8b \
  --expensive-model qwen3:14b

# Custom escalation policy (escalate on LOW only)
uv run model_router.py --escalate-on LOW

# Custom escalation policy (escalate on MEDIUM and LOW)
uv run model_router.py --escalate-on "MEDIUM,LOW"

# Disable self-check (faster but less reliable confidence)
uv run model_router.py --no-self-check

# Custom Ollama URL
uv run model_router.py --ollama-url http://192.168.1.100:11434
```

## Usage Examples

### Basic Evaluation

Run routing evaluation on the default eval dataset:

```bash
cd finetune/routing

# Using uv (recommended)
uv run model_router.py

# Or with explicit path
uv run model_router.py --eval-path finetune/dataset/eval.jsonl
```

### Full Example with All Options

```bash
uv run model_router.py \
  --eval-path finetune/dataset/eval.jsonl \
  --cheap-model llama3.1:8b \
  --expensive-model qwen3:14b \
  --escalate-on "MEDIUM,LOW" \
  --ollama-url http://localhost:11434
```

### Expected Output

```
──────────────────────────── Model Routing Evaluation ────────────────────────────
Ollama URL:      http://localhost:11434
Cheap model:     llama3.1:8b
Expensive model: qwen3:14b
Escalate on:     MEDIUM, LOW
Use self-check:  True
Eval dataset:    finetune/dataset/eval.jsonl
Output:          finetune/routing/routing_results.json

Loaded 20 examples
✓ Ollama running, models available

Running routing evaluation...
✓ # 1 ✓ Model: llama3.1:8b | Answer позитивный | Confidence: HIGH
✓ # 2 ✗ Model: qwen3:14b (escalated) | Answer: негативный | Confidence: HIGH
...

Completed in 45.2s (2.26s per sample)

──────────────────────────── Routing Summary ─────────────────────────────────────
Total samples:     20
Escalation rate:   35.00%
Avg latency:       2000.0 ms
Avg cost units:    1.00

Confidence Distribution:
  HIGH  : 13
  MEDIUM: 0
  LOW   : 0
  ERROR : 0

✓ Results saved to finetune/routing/routing_results.json
```

## Metrics Explanation

### Routing Statistics

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| **Escalation rate** | Fraction of escalated to expensive model | Lower = more savings, but ensure accuracy isn't sacrificed |
| **Cheap %** | Requests handled by cheap model only | `100% - escalation_rate` |
| **Expensive %** | Requests requiring expensive model | Same as escalation rate |
| **Avg cost units** | Average cost per request (1-3 scale) | Lower = better cost efficiency |

### Latency Metrics

| Metric | Description |
|--------|-------------|
| **Avg latency** | Mean latency across all requests (ms) |
| **Per-sample latency** | Time per request (shown in output) |

**Note:** Escalated requests have higher latency (cheap + expensive model inference time).

### Cost Savings

**Example calculation:**

- 100 requests total
- 65 handled by cheap model (65 cost units)
- 35 escalated (35 × 15 = 525 cost units)
- Total actual cost: 65 + 525 = 590 units
- All-expensive cost: 100 × 15 = 1500 units
- **Cost savings: (1500 - 590) / 1500 = 60.67%**

### Confidence Distribution

Shows how many requests fell into each confidence category:

- **HIGH**: Confident answers (stayed on cheap model)
- **MEDIUM**: Uncertain answers (escalated)
- **LOW**: Failed constraint check (escalated)
- **ERROR**: Confidence evaluation failed (escalated as fallback)

Ideal distribution: High percentage of HIGH confidence (cheap model handles most cases).

### Output File Structure

Results are saved to `routing_results.json`:

```json
{
  "cheap_model": "llama3.1:8b",
  "expensive_model": "qwen3:14b",
  "escalate_on": ["MEDIUM", "LOW"],
  "use_self_check": true,
  "ollama_url": "http://localhost:11434",
  "dataset_path": "finetune/dataset/eval.jsonl",
  "total_samples": 20,
  "escalation_rate": 0.35,
  "avg_latency_ms": 2260.5,
  "avg_cost_units": 1.00,
  "confidence_distribution": {
    "HIGH": 13,
    "MEDIUM": 0,
    "LOW": 0,
    "ERROR": 0
  },
  "predictions": [
    {
      "answer": "позитивный",
      "model_used": "llama3.1:8b",
      "confidence_status": "HIGH",
      "explanation": "Ответ содержит четкую категорию...",
      "constraint_passed": true,
      "escalated": false,
      "cheap_answer": "позитивный",
      "cheap_confidence": "HIGH",
      "latency_ms": 1850,
      "cost_units": 1
    },
    ...
  ]
}
```

## Troubleshooting

### Cannot connect to Ollama

```bash
# Start Ollama server
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

### Model not found

```bash
# Pull the missing model
ollama pull llama3.1:8b
ollama pull qwen3:14b

# Verify availability
ollama list
```

### High escalation rate

If most requests escalate to the expensive model:

1. **Check cheap model quality**: Try a larger cheap model (e.g., `llama3.1:8b`)
2. **Adjust escalation policy**: `--escalate-on LOW` (only escalate on LOW confidence)
3. **Review confidence thresholds**: The self-check may be too strict for your use case

### Slow inference

- **Cheap model latency**: Expected 100-500ms for 1B model
- **Expensive model latency**: Expected 500-2000ms for 14B model
- **Escalated requests**: Sum of both (cheap + expensive)

## Comparison with Other Modules

| Module | Purpose | When to Use |
|--------|---------|-------------|
| **baseline** | Zero-shot evaluation of single model | Establish accuracy baseline |
| **qlora** | Fine-tune model for specific task | Improve accuracy on domain data |
| **confidence** | Evaluate confidence in predictions | Quality assurance, filtering |
| **routing** | Multi-model cost optimization | Production deployment with cost constraints |

## Best Practices

1. **Start with defaults**: `llama3.1:8b` → `qwen3:14b` works well for sentiment classification
2. **Monitor escalation rate**: Target 20-40% (cheap model handles 60-80% of requests)
3. **Validate accuracy**: Compare routing accuracy vs. all-expensive baseline
4. **Tune escalation policy**: Adjust based on cost/accuracy tradeoff requirements

---

**Last Updated:** 2026-07-31  
**Module:** `finetune/routing/model_router.py`