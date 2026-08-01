# Multi-Stage Inference Pipeline

Three-stage sentiment classification pipeline with rule-based analysis, local LLM execution, and hybrid cloud integration.

## Overview

Multi-stage inference breaks complex classification tasks into smaller, composable stages:

```
Review Text → Stage 1 (Analyze) → Stage 2 (Classify) → Stage 3 (Format/Validate) → Final Result
```

### Why Multi-Stage?

| Benefit | Description |
|---------|-------------|
| **Modularity** | Each stage has single responsibility, easy to test and replace |
| **Transparency** | Intermediate outputs show why classification succeeded or failed |
| **Flexibility** | Swap stages (e.g., use GPUStack for Stage 3 only) |
| **Cost Efficiency** | Smaller stages can be cheaper than monolithic LLM calls |
| **Error Isolation** | Failures are caught at specific stages, not cascading |

### Pipeline Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Stage 1         │     │ Stage 2          │     │ Stage 3         │
│ Analyzer        │────▶│ Classifier       │────▶│ Formatter       │
│                 │     │                  │     │                 │
│ - Tokenize      │     │ - Count markers  │     │ - Validate      │
│ - Extract keys  │     │ - Apply rules    │     │ - Format JSON   │
│ - Detect markers│     │ - Compute conf.  │     │ - Return result │
└─────────────────┘     └──────────────────┘     └─────────────────┘
       │                       │                        │
       ▼                       ▼                        ▼
  key_phrases: [...]      category: "позитивный"    validated: True
  markers: {pos, neg}     confidence: 0.9           errors: []
  metadata: {...}
```

### Valid Categories

All stages classify into one of 4 Russian sentiment categories:

- `крайне негативный` (extremely negative)
- `негативный` (negative)
- `нейтральный` (neutral)
- `позитивный` (positive)

---

## Stack/Dependencies

| Dependency | Purpose | Version |
|------------|---------|---------|
| **Python** | Runtime | 3.10+ |
| `requests` | HTTP client for GPUStack API | Latest |
| `python-dotenv` | Environment variable loading | Latest |
| `scikit-learn` | Accuracy metrics | Latest |
| `rich` | Terminal output formatting | Latest |
| `matplotlib` | Chart generation (visualize.py) | Latest |
| `numpy` | Array operations for charts | Latest |
| **Ollama** | Local LLM server (optional) | Latest |
| **GPUStack** | Cloud LLM API (optional) | Latest |

### Installation

```bash
# Navigate to project root
cd /mnt/f/git/advanced

# Install dependencies via uv (recommended)
uv pip install requests python-dotenv scikit-learn rich matplotlib numpy

# Or via pip
pip install requests python-dotenv scikit-learn rich matplotlib numpy
```

### Required Services

#### Ollama (Local - Optional)

If using local models for hybrid pipeline:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull required model
ollama pull qwen3:14b

# Verify
ollama list
```

#### GPUStack (Cloud - Optional)

If using hybrid pipeline with cloud validation:

1. Create account at GPUStack
2. Get API key from dashboard
3. Set environment variables (see Configuration section)

---

## Quick Start

### Basic Pipeline (Local, No External Services)

```python
from finetune.multi_stage.pipeline import MultiStagePipeline

# Initialize pipeline
pipeline = MultiStagePipeline()

# Run on review text
review = "Отличная тачка для дачи – крепкая, удобная, выносливая!"
result = pipeline.run_pipeline(review)

# Access results
print(f"Category: {result['final_result']['category']}")
print(f"Confidence: {result['final_result']['confidence']}")
print(f"Validated: {result['final_result']['validated']}")

# Access intermediate stages
print(f"Stage 1 markers: {result['stage1']['markers']}")
print(f"Stage 2 confidence: {result['stage2']['confidence']}")
```

**Expected Output:**
```
Category: позитивный
Confidence: 0.9
Validated: True
Stage 1 markers: {'positive': ['отличная', 'крепкая', 'удобная', 'выносливая'], 'negative': []}
Stage 2 confidence: 0.9
```

---

## API Reference

### StageInput

Dataclass for passing data between stages.

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True, slots=True)
class StageInput:
    data: Any                    # The main payload
    metadata: dict = field(default_factory=dict)  # Optional metadata
```

**Usage:**
```python
from finetune.multi_stage.base import StageInput

input_data = StageInput(
    data="Review text here",
    metadata={"source": "user_review"}
)
```

---

### StageOutput

Dataclass for stage execution results.

```python
@dataclass(frozen=True, slots=True)
class StageOutput:
    result: Any                  # The computed result
    success: bool                # True if stage completed successfully
    error_message: str = ""      # Error message if success=False
    metadata: dict = field(default_factory=dict)  # Stage metadata
```

**Usage:**
```python
from finetune.multi_stage.base import StageOutput

# Success case
output = StageOutput(
    result={"category": "позитивный"},
    success=True,
    metadata={"stage": "stage2_classifier"}
)

# Error case
output = StageOutput(
    result=None,
    success=False,
    error_message="Invalid input format"
)
```

---

### Stage (Abstract Base Class)

Base class for all pipeline stages.

```python
from abc import ABC, abstractmethod
from finetune.multi_stage.base import Stage, StageInput, StageOutput

class Stage(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Return stage name for logging."""
        pass
    
    @abstractmethod
    def execute(self, input_data: StageInput) -> StageOutput:
        """Execute stage logic."""
        pass
```

**Implementing a Custom Stage:**
```python
class CustomStage(Stage):
    @property
    def name(self) -> str:
        return "custom_stage"
    
    def execute(self, input_data: StageInput) -> StageOutput:
        try:
            result = self.process(input_data.data)
            return StageOutput(result=result, success=True)
        except Exception as e:
            return StageOutput(
                result=None,
                success=False,
                error_message=str(e)
            )
    
    def process(self, data: Any) -> Any:
        # Custom logic here
        return data
```

---

### Stage1Analyzer

Extracts key phrases, sentiment markers, and metadata from review text.

**Signature:**
```python
class Stage1Analyzer(Stage):
    def analyze(self, review_text: str) -> dict:
        """
        Analyze review text and extract key information.
        
        Args:
            review_text: The review text to analyze
            
        Returns:
            dict with keys:
                - key_phrases: list[str] - important nouns and adjectives
                - markers: dict - {'positive': [...], 'negative': [...]}
                - metadata: dict - text statistics
        """
        pass
    
    def execute(self, input_data: StageInput) -> StageOutput:
        """Execute via Stage interface."""
        pass
```

**Return Structure:**
```python
{
    "key_phrases": ["тачка", "крепкая", "удобная", "выносливая"],
    "markers": {
        "positive": ["отличная", "крепкая", "удобная", "выносливая"],
        "negative": []
    },
    "metadata": {
        "length": 58,
        "word_count": 8,
        "language": "ru",
        "char_count_no_spaces": 47,
        "avg_word_length": 5.88
    }
}
```

**Usage:**
```python
from finetune.multi_stage.stage1_analyzer import Stage1Analyzer
from finetune.multi_stage.base import StageInput

analyzer = Stage1Analyzer()

# Direct method
result = analyzer.analyze("Отличная тачка!")
print(result["markers"]["positive"])  # ['отличная']

# Via Stage interface
input_data = StageInput(data="Отличная тачка!")
output = analyzer.execute(input_data)
print(output.result["key_phrases"])
```

---

### Stage2Classifier

Classifies sentiment into 4 categories based on Stage 1 output using rule-based classification.

**Signature:**
```python
class Stage2Classifier(Stage):
    def classify(self, stage1_output: dict) -> str:
        """
        Classify sentiment based on Stage 1 output.
        
        Args:
            stage1_output: dict from Stage1Analyzer with keys:
                - key_phrases: list[str]
                - markers: dict with 'positive' and 'negative' lists
                - metadata: dict
                
        Returns:
            One of 4 categories:
            - крайне негативный
            - негативный
            - нейтральный
            - позитивный
        """
        pass
    
    def execute(self, input_data: StageInput) -> StageOutput:
        """Execute via Stage interface."""
        pass
```

**Classification Rules:**

| Condition | Category |
|-----------|----------|
| `pos_count >= 3` and `neg_count == 0` | позитивный |
| `neg_count >= 3` and `pos_count == 0` | крайне негативный |
| `pos_count >= 2` and `neg_count <= 1` | позитивный |
| `neg_count >= 4` and `pos_count <= 1` | крайне негативный |
| `neg_count >= 3` and `pos_count <= 1` | негативный |
| Balanced or few markers | нейтральный |

**Usage:**
```python
from finetune.multi_stage.stage2_classifier import Stage2Classifier

classifier = Stage2Classifier()

# Simulated Stage 1 output
stage1_result = {
    "markers": {
        "positive": ["отличная", "крепкая"],
        "negative": []
    }
}

# Classify
category = classifier.classify(stage1_result)
print(category)  # позитивный
```

---

### Stage3Formatter

Validates classification result and formats final JSON output.

**Signature:**
```python
class Stage3Formatter(Stage):
    def format(
        self,
        classification: str,
        stage1_output: dict,
        confidence: float = 0.5
    ) -> dict:
        """
        Format and validate the classification result.
        
        Args:
            classification: Predicted category from Stage 2
            stage1_output: Preprocessing metadata from Stage 1
            confidence: Confidence score (default: 0.5)
            
        Returns:
            dict with keys:
                - category: str
                - confidence: float (clamped to [0.0, 1.0])
                - validated: bool
                - errors: list[str]
        """
        pass
    
    def execute(self, input_data: StageInput) -> StageOutput:
        """Execute via Stage interface."""
        pass
```

**Usage:**
```python
from finetune.multi_stage.stage3_formatter import Stage3Formatter

formatter = Stage3Formatter()

# Valid category
result = formatter.format("позитивный", {}, 0.9)
print(result)
# {'category': 'позитивный', 'confidence': 0.9, 'validated': True, 'errors': []}

# Invalid category
result = formatter.format("отлично!", {}, 0.8)
print(result)
# {'category': 'отлично!', 'confidence': 0.8, 'validated': False, 
#  'errors': ["Invalid category 'отлично!'. Must be one of: ..."]}
```

---

### MultiStagePipeline

Orchestrates all 3 stages sequentially with error handling.

**Signature:**
```python
class MultiStagePipeline:
    def __init__(self):
        """Initialize 3-stage pipeline with default stage instances."""
        pass
    
    def run_pipeline(self, review_text: str) -> dict:
        """
        Execute the 3-stage pipeline on review text.
        
        Args:
            review_text: The review text to classify
            
        Returns:
            dict with keys:
                - stage1: Stage 1 output (key_phrases, markers, metadata)
                - stage2: Stage 2 output (category, confidence)
                - stage3: Stage 3 output (category, confidence, validated, errors)
                - final_result: Same as stage3 output
                
            On error:
                - final_result: {"error": str, "failed_at_stage": str}
        """
        pass
```

**Usage:**
```python
from finetune.multi_stage.pipeline import MultiStagePipeline

pipeline = MultiStagePipeline()
result = pipeline.run_pipeline("Отличная тачка для дачи!")

if result["final_result"]["validated"]:
    print(f"Classification: {result['final_result']['category']}")
else:
    print(f"Error: {result['final_result']['errors']}")
```

---

### GPUStackHybridPipeline

Hybrid pipeline using Ollama (local) for stages 1-2 and GPUStack (cloud) for stage 3.

**Signature:**
```python
class HybridPipeline:
    def __init__(
        self,
        gpustack_url: str | None = None,
        gpustack_key: str | None = None
    ):
        """
        Initialize hybrid pipeline.
        
        Args:
            gpustack_url: GPUStack API URL (default: from env GPUSTACK_API_URL)
            gpustack_key: GPUStack API key (default: from env AI_API_KEY)
        """
        pass
    
    def run_hybrid(self, review_text: str) -> dict:
        """
        Execute hybrid pipeline.
        
        Returns:
            dict with keys:
                - stage1, stage2, stage3: Stage outputs
                - final_result: Final classification
                - sources: {"stage1": "ollama", "stage2": "ollama", "stage3": "gpustack"}
        """
        pass

def run_hybrid(review_text: str) -> dict:
    """Convenience function to run hybrid pipeline."""
    pass
```

**Usage:**
```python
from finetune.multi_stage.hybrid_pipeline import HybridPipeline, run_hybrid

# Option 1: Using class
pipeline = HybridPipeline()
result = pipeline.run_hybrid("Отличная тачка!")

# Option 2: Convenience function
result = run_hybrid("Отличная тачка!")

print(f"Sources: {result['sources']}")
# {'stage1': 'ollama', 'stage2': 'ollama', 'stage3': 'gpustack'}
```

---

### compare() Function

Compares monolithic vs multi-stage approaches on same inputs.

**Signature:**
```python
def compare(
    inputs: list[dict] | None = None,
    eval_path: str | None = None
) -> dict[str, Any]:
    """
    Compare monolithic vs multi-stage approaches.
    
    Args:
        inputs: List of examples from eval.jsonl format.
                Each example: {"messages": [{"role": "user", "content": "..."}, ...]}
                If None, loads from eval_path or default location.
        eval_path: Path to eval.jsonl (default: finetune/dataset/eval.jsonl)
    
    Returns:
        dict with structure:
        {
            "monolithic": {
                "predictions": [...],
                "accuracy": float,
                "avg_latency_ms": float,
                "total_cost": float
            },
            "multi_stage": {
                "predictions": [...],
                "accuracy": float,
                "avg_latency_ms": float,
                "total_cost": float,
                "avg_confidence": float
            },
            "delta": {
                "accuracy_diff": float,      # multi_stage - monolithic
                "latency_diff": float,       # multi_stage - monolithic
                "cost_diff": float,          # multi_stage - monolithic
                "agreement_rate": float      # % where both predict same
            }
        }
    """
    pass
```

**Usage:**
```python
from finetune.multi_stage.comparator import compare

# Compare on default eval dataset
result = compare()

print(f"Accuracy diff: {result['delta']['accuracy_diff']:+.4f}")
print(f"Latency diff: {result['delta']['latency_diff']:+.2f}ms")
print(f"Cost diff: {result['delta']['cost_diff']:+.2f}")
print(f"Agreement rate: {result['delta']['agreement_rate']:.2%}")
```

---

### evaluate.py Script

Full evaluation script comparing all 3 approaches (monolithic, local multi-stage, hybrid).

**Usage:**
```bash
# Run on default eval dataset
cd finetune/multi_stage
uv run evaluate.py

# Custom eval path
uv run evaluate.py --eval-path finetune/dataset/eval.jsonl

# Custom output path
uv run evaluate.py --output-path custom_results.json
```

**Output Structure:**
```json
{
  "monolithic": {
    "accuracy": 0.8500,
    "avg_latency_ms": 1500.0,
    "total_cost": 20.0,
    "predictions": [...]
  },
  "multi_stage_local": {
    "accuracy": 0.8000,
    "avg_latency_ms": 800.0,
    "total_cost": 12.0,
    "predictions": [...]
  },
  "multi_stage_hybrid": {
    "accuracy": 0.8500,
    "avg_latency_ms": 2500.0,
    "total_cost": 24.0,
    "predictions": [...]
  },
  "comparison": {
    "accuracy_winner": "monolithic",
    "latency_winner": "multi_stage_local",
    "cost_winner": "multi_stage_local",
    "total_examples": 20,
    "agreement_rate": {
      "mono_local": 0.85,
      "mono_hybrid": 0.95,
      "local_hybrid": 0.85
    }
  }
}
```

---

### visualize.py Script

Generates comparison charts from evaluation results.

**Usage:**
```bash
# Generate all 4 charts (requires results.json from evaluate.py)
cd finetune/multi_stage
uv run visualize.py

# Output:
# - charts/accuracy_comparison.png
# - charts/latency_comparison.png
# - charts/cost_comparison.png
# - charts/combined_metrics.png (radar chart)
```

**Chart Types:**

1. **Accuracy Comparison** - Bar chart showing accuracy for all 3 approaches
2. **Latency Comparison** - Bar chart showing average latency (ms)
3. **Cost Comparison** - Bar chart showing total cost units
4. **Combined Metrics** - Radar chart with normalized metrics (accuracy, speed, cost)

---

## Examples

### Example 1: Basic Pipeline Usage

```python
#!/usr/bin/env python3
"""Basic multi-stage pipeline example."""

from finetune.multi_stage.pipeline import MultiStagePipeline

# Initialize pipeline
pipeline = MultiStagePipeline()

# Sample reviews
reviews = [
    "Отличная тачка для дачи – крепкая, удобная, выносливая!",
    "Полный мусор. Ржавчина через месяц, колёса спустили.",
    "Нормальная вещь, ничего особенного.",
    "Ужасное качество. Развалилась через неделю."
]

# Classify each review
for review in reviews:
    result = pipeline.run_pipeline(review)
    
    if result["final_result"]["validated"]:
        print(f"Review: {review[:50]}...")
        print(f"  Category: {result['final_result']['category']}")
        print(f"  Confidence: {result['final_result']['confidence']}")
        print()
    else:
        print(f"Error: {result['final_result']['errors']}")
```

**Expected Output:**
```
Review: Отличная тачка для дачи – крепкая, удобная, вынослив...
  Category: позитивный
  Confidence: 0.9

Review: Полный мусор. Ржавчина через месяц, колёса спустили....
  Category: крайне негативный
  Confidence: 0.9

Review: Нормальная вещь, ничего особенного....
  Category: нейтральный
  Confidence: 0.5

Review: Ужасное качество. Развалилась через неделю....
  Category: крайне негативный
  Confidence: 0.9
```

---

### Example 2: Hybrid Pipeline with GPUStack

```python
#!/usr/bin/env python3
"""Hybrid pipeline with GPUStack cloud validation."""

from finetune.multi_stage.hybrid_pipeline import HybridPipeline

# Initialize with explicit credentials (or use env vars)
pipeline = HybridPipeline(
    gpustack_url="https://api.gpustack.example.com",
    gpustack_key="your-api-key-here"
)

# Run classification
review = "Отличная тачка для дачи – крепкая, удобная!"
result = pipeline.run_hybrid(review)

# Check sources
print(f"Stage 1 source: {result['sources']['stage1']}")  # ollama
print(f"Stage 2 source: {result['sources']['stage2']}")  # ollama
print(f"Stage 3 source: {result['sources']['stage3']}")  # gpustack

# Access final result
if result["final_result"]["validated"]:
    print(f"Validated category: {result['final_result']['category']}")
else:
    print(f"Validation failed: {result['final_result']['errors']}")
```

**Environment Variables (Alternative):**

Create `.env` file in `finetune/` directory:
```bash
GPUSTACK_API_URL=https://api.gpustack.example.com
AI_API_KEY=your-api-key-here
```

Then use default constructor:
```python
pipeline = HybridPipeline()  # Reads from .env
```

---

### Example 3: Running Evaluation

```python
#!/usr/bin/env python3
"""Run full evaluation on all 3 approaches."""

from finetune.multi_stage.evaluate import run_full_evaluation
from pathlib import Path

# Run evaluation
results = run_full_evaluation(
    eval_path=Path("finetune/dataset/eval.jsonl"),
    output_path=Path("finetune/multi_stage/results.json")
)

# Print summary
print("=" * 60)
print("EVALUATION SUMMARY")
print("=" * 60)

# Accuracy comparison
print(f"\nAccuracy:")
print(f"  Monolithic:       {results['monolithic']['accuracy']:.4f}")
print(f"  Multi-Stage Local: {results['multi_stage_local']['accuracy']:.4f}")
print(f"  Multi-Stage Hybrid: {results['multi_stage_hybrid']['accuracy']:.4f}")
print(f"  Winner: {results['comparison']['accuracy_winner']}")

# Latency comparison
print(f"\nLatency (ms):")
print(f"  Monolithic:       {results['monolithic']['avg_latency_ms']:.2f}")
print(f"  Multi-Stage Local: {results['multi_stage_local']['avg_latency_ms']:.2f}")
print(f"  Multi-Stage Hybrid: {results['multi_stage_hybrid']['avg_latency_ms']:.2f}")
print(f"  Winner: {results['comparison']['latency_winner']}")

# Cost comparison
print(f"\nCost:")
print(f"  Monolithic:       {results['monolithic']['total_cost']:.2f}")
print(f"  Multi-Stage Local: {results['multi_stage_local']['total_cost']:.2f}")
print(f"  Multi-Stage Hybrid: {results['multi_stage_hybrid']['total_cost']:.2f}")
print(f"  Winner: {results['comparison']['cost_winner']}")

# Agreement rates
print(f"\nAgreement Rates:")
print(f"  Mono ↔ Local:   {results['comparison']['agreement_rate']['mono_local']:.2%}")
print(f"  Mono ↔ Hybrid:  {results['comparison']['agreement_rate']['mono_hybrid']:.2%}")
print(f"  Local ↔ Hybrid: {results['comparison']['agreement_rate']['local_hybrid']:.2%}")
```

---

### Example 4: Generating Visualizations

```python
#!/usr/bin/env python3
"""Generate comparison charts from evaluation results."""

from finetune.multi_stage.visualize import generate_all_charts
from pathlib import Path

# Generate all charts
try:
    chart_paths = generate_all_charts(
        results_path=Path("finetune/multi_stage/results.json"),
        charts_dir=Path("finetune/multi_stage/charts")
    )
    
    print("Generated charts:")
    for chart_type, path in chart_paths.items():
        print(f"  {chart_type}: {path}")
        
except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Run evaluate.py first to generate results.json")
```

**Chart Output:**
```
Generated charts:
  accuracy: finetune/multi_stage/charts/accuracy_comparison.png
  latency: finetune/multi_stage/charts/latency_comparison.png
  cost: finetune/multi_stage/charts/cost_comparison.png
  combined: finetune/multi_stage/charts/combined_metrics.png
```

---

## Configuration

### Environment Variables

Create `.env` file in `finetune/` directory:

```bash
# GPUStack Configuration (for hybrid pipeline)
GPUSTACK_API_URL=https://api.gpustack.example.com
AI_API_KEY=your-api-key-here

# Ollama Configuration (optional, defaults shown)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:14b
```

### Ollama Setup

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start server
ollama serve

# Pull required model
ollama pull qwen3:14b

# Verify
curl http://localhost:11434/api/tags
```

### GPUStack Setup

1. **Create Account:** Sign up at [GPUStack](https://gpustack.example.com)
2. **Get API Key:** Navigate to Dashboard → API Keys → Create New
3. **Set Environment Variables:**
   ```bash
   export GPUSTACK_API_URL=https://api.gpustack.example.com
   export AI_API_KEY=sk-xxxxx
   ```
4. **Test Connection:**
   ```python
   from finetune.multi_stage.hybrid_pipeline import run_hybrid
   result = run_hybrid("Test review")
   print(result["sources"])  # Should show all stages completed
   ```

---

## Results Interpretation

### Pipeline Output Structure

```python
{
    "stage1": {
        "key_phrases": ["тачка", "крепкая", "удобная"],
        "markers": {
            "positive": ["отличная", "крепкая", "удобная"],
            "negative": []
        },
        "metadata": {
            "length": 58,
            "word_count": 8,
            "language": "ru"
        }
    },
    "stage2": {
        "category": "позитивный",
        "confidence": 0.9
    },
    "stage3": {
        "category": "позитивный",
        "confidence": 0.9,
        "validated": True,
        "errors": []
    },
    "final_result": {
        "category": "позитивный",
        "confidence": 0.9,
        "validated": True,
        "errors": []
    }
}
```

### Understanding Confidence Scores

| Confidence Range | Interpretation |
|------------------|----------------|
| 0.8 - 1.0 | High confidence - clear sentiment markers |
| 0.6 - 0.8 | Moderate confidence - some ambiguity |
| 0.5 - 0.6 | Low confidence - mixed or weak signals |
| < 0.5 | Very low confidence - likely neutral or noisy input |

### Validation Errors

Common validation errors from Stage 3:

```python
# Invalid category
{
    "validated": False,
    "errors": ["Invalid category 'отлично!'. Must be one of: крайне негативный, негативный, нейтральный, позитивный"]
}

# Invalid confidence
{
    "validated": False,
    "errors": ["Confidence must be between 0.0 and 1.0, got 1.5"]
}
```

### Evaluation Metrics

| Metric | Best Value | Interpretation |
|--------|------------|----------------|
| **Accuracy** | Higher (max 1.0) | Fraction of correct predictions |
| **Avg Latency** | Lower (ms) | Faster inference time |
| **Total Cost** | Lower (units) | Cheaper computation |
| **Agreement Rate** | Context-dependent | How often approaches agree |

**Trade-offs:**

- **Monolithic**: Highest accuracy, but slower and more expensive
- **Multi-Stage Local**: Fastest and cheapest, slightly lower accuracy
- **Multi-Stage Hybrid**: Balanced - local speed for stages 1-2, cloud accuracy for stage 3

---

## Troubleshooting

### Cannot Connect to Ollama

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama server
ollama serve

# Verify model is pulled
ollama list | grep qwen3
```

### GPUStack API Errors

```python
# Check environment variables
import os
print(f"GPUSTACK_API_URL: {os.getenv('GPUSTACK_API_URL')}")
print(f"AI_API_KEY: {os.getenv('AI_API_KEY')}")

# Test connection manually
import requests
response = requests.get(
    "https://api.gpustack.example.com/health",
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)
print(response.status_code)
```

### High Error Rate in Stage 3

If many classifications fail validation:

1. **Check Stage 2 output**: Ensure classifier returns valid categories
2. **Review classification rules**: Adjust thresholds in `stage2_classifier.py`
3. **Add more sentiment markers**: Expand `POSITIVE_WORDS` / `NEGATIVE_WORDS` in `stage1_analyzer.py`

### Slow Inference

- **Stage 1**: Should be instant (rule-based, no LLM)
- **Stage 2**: Should be instant (rule-based, no LLM)
- **Stage 3 (Hybrid)**: Depends on GPUStack API latency (typically 500-2000ms)

**Optimization:**
```python
# Use local pipeline for faster inference
from finetune.multi_stage.pipeline import MultiStagePipeline
pipeline = MultiStagePipeline()  # No cloud API calls
```

---

## Module Structure

```
finetune/multi_stage/
├── __init__.py              # Module exports
├── base.py                  # Stage, StageInput, StageOutput
├── stage1_analyzer.py       # Stage 1: Input analysis
├── stage2_classifier.py     # Stage 2: Sentiment classification
├── stage3_formatter.py      # Stage 3: Validation & formatting
├── pipeline.py              # MultiStagePipeline orchestrator
├── hybrid_pipeline.py       # HybridPipeline (Ollama + GPUStack)
├── comparator.py            # compare() function
├── evaluate.py              # Full evaluation script
├── visualize.py             # Chart generation
├── tests/                   # Unit tests
├── charts/                  # Generated visualization charts
└── README.md                # This file
```

---

## Comparison with Other Modules

| Module | Purpose | When to Use |
|--------|---------|-------------|
| **baseline** | Single-model zero-shot evaluation | Establish accuracy baseline |
| **qlora** | Fine-tune model on domain data | Improve accuracy with training |
| **confidence** | Evaluate prediction confidence | Quality assurance, filtering |
| **routing** | Multi-model cost optimization | Production with cost constraints |
| **multi_stage** | Modular 3-stage pipeline | Transparency, flexibility, hybrid deployment |

---

## Best Practices

1. **Start with local pipeline**: Test with `MultiStagePipeline` before adding GPUStack complexity
2. **Monitor stage outputs**: Inspect intermediate results to understand classification decisions
3. **Use evaluation script**: Run `evaluate.py` before deploying to production
4. **Set up environment variables**: Use `.env` file for GPUStack credentials
5. **Generate visualizations**: Run `visualize.py` to compare approaches visually
6. **Handle errors gracefully**: Check `validated` flag before using classification results
7. **Extend with custom stages**: Implement `Stage` interface for domain-specific logic

---

**Last Updated:** 2026-08-01  
**Module:** `finetune/multi_stage/`  
**Python Version:** 3.10+