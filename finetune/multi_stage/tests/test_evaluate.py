#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pytest",
#     "scikit-learn",
# ]
# ///

"""
Tests for evaluate.py

Run with: pytest finetune/multi_stage/tests/test_evaluate.py -v
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from finetune.multi_stage.evaluate import (
    EvaluationPrediction,
    evaluate_monolithic,
    evaluate_multi_stage_local,
    evaluate_multi_stage_hybrid,
    compute_metrics,
    _compute_agreement_rate,
    run_full_evaluation,
    MONOLITHIC_LATENCY_MS,
    MONOLITHIC_COST,
    MULTI_STAGE_LOCAL_LATENCY_MS,
    MULTI_STAGE_LOCAL_COST,
    MULTI_STAGE_HYBRID_LATENCY_MS,
    MULTI_STAGE_HYBRID_COST,
)
from finetune.multi_stage.pipeline import MultiStagePipeline
from finetune.multi_stage.hybrid_pipeline import HybridPipeline


# ─── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def sample_examples() -> list[dict]:
    """Sample eval.jsonl examples for testing."""
    return [
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "Отличная тачка для дачи – крепкая, удобная!"},
                {"role": "assistant", "content": "позитивный"}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "Проработала одну неделю, потом колесо пошло ходуном."},
                {"role": "assistant", "content": "крайне негативный"}
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "Брал чтобы заменить старую — та развалилась. Эта работает."},
                {"role": "assistant", "content": "нейтральный"}
            ]
        },
    ]


@pytest.fixture
def mock_pipeline():
    """Mock MultiStagePipeline for testing."""
    pipeline = Mock(spec=MultiStagePipeline)
    pipeline.run_pipeline.side_effect = [
        {"stage1": {"key_phrases": ["отличная"]}, "stage2": {"category": "позитивный", "confidence": 0.9}, "stage3": {"category": "позитивный", "confidence": 0.9, "validated": True}, "final_result": {"category": "позитивный", "confidence": 0.9, "validated": True}},
        {"stage1": {"key_phrases": ["колесо"]}, "stage2": {"category": "крайне негативный", "confidence": 0.85}, "stage3": {"category": "крайне негативный", "confidence": 0.85, "validated": True}, "final_result": {"category": "крайне негативный", "confidence": 0.85, "validated": True}},
        {"stage1": {"key_phrases": ["работает"]}, "stage2": {"category": "нейтральный", "confidence": 0.7}, "stage3": {"category": "нейтральный", "confidence": 0.7, "validated": True}, "final_result": {"category": "нейтральный", "confidence": 0.7, "validated": True}},
    ]
    return pipeline


@pytest.fixture
def mock_hybrid_pipeline():
    """Mock HybridPipeline for testing."""
    pipeline = Mock(spec=HybridPipeline)
    pipeline.run_hybrid.side_effect = [
        {
            "stage1": {"key_phrases": ["отличная"]},
            "stage2": {"category": "позитивный", "confidence": 0.9},
            "stage3": {"category": "позитивный", "confidence": 0.9, "validated": True},
            "final_result": {"category": "позитивный", "confidence": 0.9, "validated": True},
            "sources": {"stage1": "ollama", "stage2": "ollama", "stage3": "gpustack"}
        },
        {
            "stage1": {"key_phrases": ["колесо"]},
            "stage2": {"category": "крайне негативный", "confidence": 0.85},
            "stage3": {"category": "крайне негативный", "confidence": 0.85, "validated": True},
            "final_result": {"category": "крайне негативный", "confidence": 0.85, "validated": True},
            "sources": {"stage1": "ollama", "stage2": "ollama", "stage3": "gpustack"}
        },
        {
            "stage1": {"key_phrases": ["работает"]},
            "stage2": {"category": "нейтральный", "confidence": 0.7},
            "stage3": {"category": "нейтральный", "confidence": 0.7, "validated": True},
            "final_result": {"category": "нейтральный", "confidence": 0.7, "validated": True},
            "sources": {"stage1": "ollama", "stage2": "ollama", "stage3": "gpustack"}
        },
    ]
    return pipeline


# ─── Tests: EvaluationPrediction dataclass ────────────────────


def test_evaluation_prediction_creation():
    """Test 1: EvaluationPrediction dataclass can be instantiated."""
    pred = EvaluationPrediction(
        index=0,
        predicted="позитивный",
        actual="позитивный",
        correct=True,
        latency_ms=1500.0,
        cost=1.0,
        metadata={"confidence": 0.9}
    )
    
    assert pred.index == 0
    assert pred.predicted == "позитивный"
    assert pred.actual == "позитивный"
    assert pred.correct is True
    assert pred.latency_ms == 1500.0
    assert pred.cost == 1.0
    assert pred.metadata == {"confidence": 0.9}


def test_evaluation_prediction_immutable():
    """Test 2: EvaluationPrediction is frozen (immutable)."""
    pred = EvaluationPrediction(
        index=0,
        predicted="позитивный",
        actual="позитивный",
        correct=True,
        latency_ms=1500.0,
        cost=1.0
    )
    
    with pytest.raises(AttributeError):
        pred.predicted = "негативный"


# ─── Tests: evaluate_monolithic ───────────────────────────────


def test_evaluate_monolithic_basic(sample_examples):
    """Test 3: Monolithic evaluation returns correct predictions."""
    predictions = evaluate_monolithic(sample_examples)
    
    assert len(predictions) == 3
    assert all(isinstance(p, EvaluationPrediction) for p in predictions)
    assert all(p.latency_ms == MONOLITHIC_LATENCY_MS for p in predictions)
    assert all(p.cost == MONOLITHIC_COST for p in predictions)


def test_evaluate_monolithic_correctness(sample_examples):
    """Test 4: Monolithic evaluation checks correctness."""
    predictions = evaluate_monolithic(sample_examples)
    
    # Check that predictions have correct/incorrect flags
    assert all(hasattr(p, 'correct') for p in predictions)
    assert all(isinstance(p.correct, bool) for p in predictions)


# ─── Tests: evaluate_multi_stage_local ────────────────────────


def test_evaluate_local_basic(sample_examples, mock_pipeline):
    """Test 5: Local multi-stage evaluation uses pipeline."""
    predictions = evaluate_multi_stage_local(sample_examples, mock_pipeline)
    
    assert len(predictions) == 3
    assert mock_pipeline.run_pipeline.call_count == 3
    assert all(p.latency_ms == MULTI_STAGE_LOCAL_LATENCY_MS for p in predictions)
    assert all(p.cost == MULTI_STAGE_LOCAL_COST for p in predictions)


def test_evaluate_local_with_errors(sample_examples):
    """Test 6: Local multi-stage handles pipeline errors."""
    error_pipeline = Mock(spec=MultiStagePipeline)
    error_pipeline.run_pipeline.return_value = {
        "stage1": None,
        "stage2": None,
        "stage3": None,
        "final_result": {"error": "Stage 1 failed", "failed_at_stage": "stage1_analyzer"}
    }
    
    predictions = evaluate_multi_stage_local(sample_examples, error_pipeline)
    
    assert len(predictions) == 3
    # Should default to "нейтральный" on error
    assert all(p.predicted == "нейтральный" for p in predictions)
    assert all(p.metadata["confidence"] == 0.0 for p in predictions)


# ─── Tests: evaluate_multi_stage_hybrid ───────────────────────


def test_evaluate_hybrid_basic(sample_examples, mock_hybrid_pipeline):
    """Test 7: Hybrid evaluation uses hybrid pipeline."""
    predictions = evaluate_multi_stage_hybrid(sample_examples, mock_hybrid_pipeline)
    
    assert len(predictions) == 3
    assert mock_hybrid_pipeline.run_hybrid.call_count == 3
    assert all(p.latency_ms == MULTI_STAGE_HYBRID_LATENCY_MS for p in predictions)
    assert all(p.cost == MULTI_STAGE_HYBRID_COST for p in predictions)


def test_evaluate_hybrid_with_errors(sample_examples):
    """Test 8: Hybrid evaluation handles pipeline errors."""
    error_pipeline = Mock(spec=HybridPipeline)
    error_pipeline.run_hybrid.return_value = {
        "stage1": None,
        "stage2": None,
        "stage3": None,
        "final_result": {"error": "GPUStack API error", "failed_at_stage": "stage3_gpustack_formatter"}
    }
    
    predictions = evaluate_multi_stage_hybrid(sample_examples, error_pipeline)
    
    assert len(predictions) == 3
    # Should default to "нейтральный" on error
    assert all(p.predicted == "нейтральный" for p in predictions)
    assert all(p.metadata["confidence"] == 0.0 for p in predictions)
    assert all(p.metadata["error"] is not None for p in predictions)


# ─── Tests: compute_metrics ───────────────────────────────────


def test_compute_metrics_basic():
    """Test 9: Metrics computation returns correct structure."""
    predictions = [
        EvaluationPrediction(0, "позитивный", "позитивный", True, 1500.0, 1.0),
        EvaluationPrediction(1, "негативный", "негативный", True, 1500.0, 1.0),
        EvaluationPrediction(2, "нейтральный", "позитивный", False, 1500.0, 1.0),
    ]
    
    metrics = compute_metrics(predictions)
    
    assert "accuracy" in metrics
    assert "avg_latency_ms" in metrics
    assert "total_cost" in metrics
    assert "predictions" in metrics
    assert metrics["accuracy"] == pytest.approx(2/3, rel=1e-3)
    assert metrics["avg_latency_ms"] == 1500.0
    assert metrics["total_cost"] == 3.0


def test_compute_metrics_empty():
    """Test 10: Metrics computation handles empty predictions."""
    metrics = compute_metrics([])
    
    assert metrics["accuracy"] == 0.0
    assert metrics["avg_latency_ms"] == 0.0
    assert metrics["total_cost"] == 0.0
    assert metrics["predictions"] == []


def test_compute_metrics_perfect_accuracy():
    """Test 11: Metrics computation with perfect accuracy."""
    predictions = [
        EvaluationPrediction(0, "позитивный", "позитивный", True, 1000.0, 0.5),
        EvaluationPrediction(1, "негативный", "негативный", True, 1000.0, 0.5),
    ]
    
    metrics = compute_metrics(predictions)
    
    assert metrics["accuracy"] == 1.0
    assert metrics["avg_latency_ms"] == 1000.0
    assert metrics["total_cost"] == 1.0


# ─── Tests: _compute_agreement_rate ───────────────────────────


def test_agreement_rate_perfect():
    """Test 12: Agreement rate with perfect agreement."""
    predictions = [
        EvaluationPrediction(0, "позитивный", "позитивный", True, 1500.0, 1.0),
        EvaluationPrediction(1, "негативный", "негативный", True, 1500.0, 1.0),
    ]
    
    rates = _compute_agreement_rate(predictions, predictions, predictions)
    
    assert rates["mono_local"] == 1.0
    assert rates["mono_hybrid"] == 1.0
    assert rates["local_hybrid"] == 1.0


def test_agreement_rate_no_agreement():
    """Test 13: Agreement rate with no agreement."""
    mono = [
        EvaluationPrediction(0, "позитивный", "позитивный", True, 1500.0, 1.0),
        EvaluationPrediction(1, "негативный", "негативный", True, 1500.0, 1.0),
    ]
    local = [
        EvaluationPrediction(0, "негативный", "позитивный", False, 800.0, 0.6),
        EvaluationPrediction(1, "позитивный", "негативный", False, 800.0, 0.6),
    ]
    
    rates = _compute_agreement_rate(mono, local, local)
    
    assert rates["mono_local"] == 0.0


def test_agreement_rate_empty():
    """Test 14: Agreement rate with empty predictions."""
    rates = _compute_agreement_rate([], [], [])
    
    assert rates["mono_local"] == 0.0
    assert rates["mono_hybrid"] == 0.0
    assert rates["local_hybrid"] == 0.0


# ─── Tests: run_full_evaluation ───────────────────────────────


def test_run_full_evaluation_integration(sample_examples, tmp_path):
    """Test 15: Full evaluation runs and saves results."""
    # Create temp eval file
    eval_file = tmp_path / "test_eval.jsonl"
    with eval_file.open("w", encoding="utf-8") as f:
        for example in sample_examples:
            f.write(json.dumps(example) + "\n")
    
    output_file = tmp_path / "test_results.json"
    
    # Mock the pipelines to avoid actual LLM calls
    with patch('finetune.multi_stage.evaluate.MultiStagePipeline') as mock_local, \
         patch('finetune.multi_stage.evaluate.HybridPipeline') as mock_hybrid:
        
        # Setup mocks
        mock_local.return_value.run_pipeline.return_value = {
            "final_result": {"category": "позитивный", "confidence": 0.9, "validated": True}
        }
        mock_hybrid.return_value.run_hybrid.return_value = {
            "final_result": {"category": "позитивный", "confidence": 0.9, "validated": True},
            "sources": {"stage1": "ollama", "stage2": "ollama", "stage3": "gpustack"}
        }
        
        results = run_full_evaluation(eval_file, output_file)
    
    # Check results structure
    assert "monolithic" in results
    assert "multi_stage_local" in results
    assert "multi_stage_hybrid" in results
    assert "comparison" in results
    
    # Check output file exists
    assert output_file.exists()
    
    # Verify saved content
    saved = json.loads(output_file.read_text(encoding="utf-8"))
    assert "monolithic" in saved
    assert "comparison" in saved


def test_run_full_evaluation_comparison_structure(sample_examples, tmp_path):
    """Test 16: Comparison section has all required fields."""
    eval_file = tmp_path / "test_eval.jsonl"
    with eval_file.open("w", encoding="utf-8") as f:
        for example in sample_examples:
            f.write(json.dumps(example) + "\n")
    
    output_file = tmp_path / "test_results.json"
    
    with patch('finetune.multi_stage.evaluate.MultiStagePipeline') as mock_local, \
         patch('finetune.multi_stage.evaluate.HybridPipeline') as mock_hybrid:
        
        mock_local.return_value.run_pipeline.return_value = {
            "final_result": {"category": "позитивный", "confidence": 0.9, "validated": True}
        }
        mock_hybrid.return_value.run_hybrid.return_value = {
            "final_result": {"category": "позитивный", "confidence": 0.9, "validated": True},
            "sources": {"stage1": "ollama", "stage2": "ollama", "stage3": "gpustack"}
        }
        
        results = run_full_evaluation(eval_file, output_file)
    
    comp = results["comparison"]
    assert "accuracy_winner" in comp
    assert "latency_winner" in comp
    assert "cost_winner" in comp
    assert "total_examples" in comp
    assert "agreement_rate" in comp


# ─── Tests: Latency and Cost Constants ────────────────────────


def test_latency_constants_reasonable():
    """Test 17: Latency constants are reasonable values."""
    assert MONOLITHIC_LATENCY_MS > 0
    assert MULTI_STAGE_LOCAL_LATENCY_MS > 0
    assert MULTI_STAGE_HYBRID_LATENCY_MS > 0
    
    # Hybrid should be slowest (includes cloud API)
    assert MULTI_STAGE_HYBRID_LATENCY_MS >= MONOLITHIC_LATENCY_MS
    # Local should be fastest
    assert MULTI_STAGE_LOCAL_LATENCY_MS <= MONOLITHIC_LATENCY_MS


def test_cost_constants_reasonable():
    """Test 18: Cost constants are reasonable values."""
    assert MONOLITHIC_COST > 0
    assert MULTI_STAGE_LOCAL_COST > 0
    assert MULTI_STAGE_HYBRID_COST > 0
    
    # Local should be cheapest
    assert MULTI_STAGE_LOCAL_COST <= MONOLITHIC_COST
    # Hybrid may be more expensive due to cloud API
    assert MULTI_STAGE_HYBRID_COST >= MULTI_STAGE_LOCAL_COST


# ─── Tests: Metadata in predictions ───────────────────────────


def test_local_predictions_have_confidence(sample_examples, mock_pipeline):
    """Test 19: Local predictions include confidence in metadata."""
    predictions = evaluate_multi_stage_local(sample_examples, mock_pipeline)
    
    assert all("confidence" in p.metadata for p in predictions)
    assert all(p.metadata["confidence"] > 0 for p in predictions)


def test_hybrid_predictions_have_sources(sample_examples, mock_hybrid_pipeline):
    """Test 20: Hybrid predictions include sources in metadata."""
    predictions = evaluate_multi_stage_hybrid(sample_examples, mock_hybrid_pipeline)
    
    assert all("sources" in p.metadata for p in predictions)
    assert all(p.metadata["sources"]["stage1"] == "ollama" for p in predictions)
    assert all(p.metadata["sources"]["stage3"] == "gpustack" for p in predictions)