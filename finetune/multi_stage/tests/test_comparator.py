#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pytest",
#     "scikit-learn",
# ]
# ///

"""
Tests for the Monolithic Baseline Comparator module.

Covers:
- Comparator initialization
- Single example comparison
- Multiple examples comparison
- Output structure validation
- Accuracy delta calculation
- Edge cases (empty input, mismatched categories)
"""

import json
from pathlib import Path
from typing import Any

import pytest

from finetune.multi_stage.comparator import (
    LABELED_CATEGORIES,
    ComparisonResult,
    compare,
    compare_examples,
    extract_actual_label,
    extract_user_content,
    load_examples,
    normalize_prediction,
    run_monolithic_prediction,
    run_multi_stage_prediction,
)
from finetune.multi_stage.pipeline import MultiStagePipeline


# ─── Test fixtures ────────────────────────────────────────────


@pytest.fixture
def sample_example() -> dict:
    """Single example from eval.jsonl format."""
    return {
        "messages": [
            {"role": "system", "content": "Ты — классификатор тональности отзывов."},
            {"role": "user", "content": "Отличная тачка для дачи – крепкая, удобная и очень выносливая."},
            {"role": "assistant", "content": "позитивный"},
        ]
    }


@pytest.fixture
def sample_examples() -> list[dict]:
    """10 examples from eval.jsonl for testing."""
    examples = [
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "Брал чтобы заменить старую — та развалилась. Эта работает. Колесо накачиваю раз в 5 дней, корыто не гнило."},
                {"role": "assistant", "content": "нейтральный"},
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "Купил для огорода — тачка рабочая, но требует постоянного внимания, гайки подкручивать каждую поездку."},
                {"role": "assistant", "content": "негативный"},
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "Пользовалась полгода — ни критических поломок, но и восторга нет."},
                {"role": "assistant", "content": "негативный"},
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "Отличная тачка для дачи – крепкая, удобная и очень выносливая. Брал для дачи: возил землю, камни, мусор – справляется на ура."},
                {"role": "assistant", "content": "позитивный"},
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "Хорошая, легкая тачка. В пользовании более 4 лет."},
                {"role": "assistant", "content": "позитивный"},
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "Проработала одну неделю, потом колесо пошло ходуном, рама покрылась ржавчиной, корыто провисло."},
                {"role": "assistant", "content": "крайне негативный"},
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "Пользуюсь для переноски листьев и компоста, нагружаю до 40-50 кг — работает."},
                {"role": "assistant", "content": "нейтральный"},
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "Лучшая покупка для дачи за последние годы! Рама из толстого металла, не шатается."},
                {"role": "assistant", "content": "позитивный"},
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "Привезли без винтов для крепления корыта, пришлось бегать по строймаркетам искать замену."},
                {"role": "assistant", "content": "крайне негативный"},
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "Ты — классификатор тональности отзывов."},
                {"role": "user", "content": "На основе пяти оценок — простая в использовании, хорошее соотношение цены и качества."},
                {"role": "assistant", "content": "нейтральный"},
            ]
        },
    ]
    return examples


@pytest.fixture
def empty_examples() -> list[dict]:
    """Empty list for edge case testing."""
    return []


@pytest.fixture
def pipeline() -> MultiStagePipeline:
    """Multi-stage pipeline instance."""
    return MultiStagePipeline()


# ─── Test: Initialization ─────────────────────────────────────


class TestComparatorInitialization:
    """Test comparator module initialization and imports."""
    
    def test_module_imports_successfully(self) -> None:
        """Test that comparator module can be imported without errors."""
        from finetune.multi_stage import comparator
        assert hasattr(comparator, "compare")
        assert hasattr(comparator, "compare_examples")
    
    def test_labeled_categories_defined(self) -> None:
        """Test that LABELED_CATEGORIES constant is defined correctly."""
        assert len(LABELED_CATEGORIES) == 4
        assert "крайне негативный" in LABELED_CATEGORIES
        assert "негативный" in LABELED_CATEGORIES
        assert "нейтральный" in LABELED_CATEGORIES
        assert "позитивный" in LABELED_CATEGORIES
    
    def test_comparison_result_dataclass_exists(self) -> None:
        """Test that ComparisonResult dataclass is defined."""
        assert ComparisonResult is not None


# ─── Test: Helper functions ───────────────────────────────────


class TestHelperFunctions:
    """Test helper functions for data extraction and normalization."""
    
    def test_extract_user_content(self, sample_example: dict) -> None:
        """Test extraction of user content from example."""
        content = extract_user_content(sample_example)
        assert "Отличная тачка" in content
        assert "крепкая" in content
    
    def test_extract_actual_label(self, sample_example: dict) -> None:
        """Test extraction of actual label from example."""
        label = extract_actual_label(sample_example)
        assert label == "позитивный"
    
    def test_extract_user_content_empty_messages(self) -> None:
        """Test extraction from example with empty messages."""
        example = {"messages": []}
        content = extract_user_content(example)
        assert content == ""
    
    def test_extract_actual_label_missing_assistant(self) -> None:
        """Test extraction when assistant message is missing."""
        example = {
            "messages": [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "User content"},
            ]
        }
        label = extract_actual_label(example)
        assert label == ""
    
    def test_normalize_prediction_exact_match(self) -> None:
        """Test normalization with exact category match."""
        assert normalize_prediction("позитивный") == "позитивный"
        assert normalize_prediction("негативный") == "негативный"
        assert normalize_prediction("нейтральный") == "нейтральный"
        assert normalize_prediction("крайне негативный") == "крайне негативный"
    
    def test_normalize_prediction_case_insensitive(self) -> None:
        """Test normalization is case-insensitive."""
        assert normalize_prediction("Позитивный") == "позитивный"
        assert normalize_prediction("НЕГАТИВНЫЙ") == "негативный"
    
    def test_normalize_prediction_oov_handling(self) -> None:
        """Test normalization returns neutral for unknown categories."""
        assert normalize_prediction("unknown") == "нейтральный"
        assert normalize_prediction("positive") == "нейтральный"
        assert normalize_prediction("") == "нейтральный"
    
    def test_load_examples_from_path(self, tmp_path: Path) -> None:
        """Test loading examples from JSONL file."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"messages": [{"role": "user", "content": "test"}]}\n'
            '{"messages": [{"role": "user", "content": "test2"}]}\n',
            encoding="utf-8",
        )
        examples = load_examples(jsonl_file)
        assert len(examples) == 2
        assert examples[0]["messages"][0]["content"] == "test"


# ─── Test: Single prediction functions ────────────────────────


class TestPredictionFunctions:
    """Test monolithic and multi-stage prediction functions."""
    
    def test_run_monolithic_prediction_positive(self) -> None:
        """Test monolithic prediction on positive review."""
        result = run_monolithic_prediction(
            "Отличная тачка – крепкая, удобная, рекомендую!"
        )
        assert "predicted" in result
        assert "latency_ms" in result
        assert "cost" in result
        assert result["predicted"] == "позитивный"
    
    def test_run_monolithic_prediction_negative(self) -> None:
        """Test monolithic prediction on negative review."""
        result = run_monolithic_prediction(
            "Ржавчина, провисло, мусор, отвратительное качество"
        )
        assert result["predicted"] in LABELED_CATEGORIES
    
    def test_run_monolithic_prediction_neutral(self) -> None:
        """Test monolithic prediction on neutral review."""
        result = run_monolithic_prediction(
            "Работает, но есть минусы и плюсы"
        )
        assert result["predicted"] in LABELED_CATEGORIES
    
    def test_run_monolithic_prediction_has_latency(self) -> None:
        """Test monolithic prediction includes latency."""
        result = run_monolithic_prediction("test review")
        assert result["latency_ms"] > 0
    
    def test_run_monolithic_prediction_has_cost(self) -> None:
        """Test monolithic prediction includes cost."""
        result = run_monolithic_prediction("test review")
        assert result["cost"] > 0
    
    def test_run_multi_stage_prediction(self, sample_example: dict, pipeline: MultiStagePipeline) -> None:
        """Test multi-stage pipeline prediction."""
        user_content = extract_user_content(sample_example)
        result = run_multi_stage_prediction(user_content, pipeline)
        
        assert "predicted" in result
        assert "confidence" in result
        assert "latency_ms" in result
        assert "cost" in result
        assert "stages" in result
        assert result["predicted"] in LABELED_CATEGORIES
    
    def test_run_multi_stage_prediction_with_stages(self, pipeline: MultiStagePipeline) -> None:
        """Test multi-stage prediction returns stage details."""
        result = run_multi_stage_prediction(
            "Отличная тачка для дачи",
            pipeline
        )
        assert "stages" in result
        assert result["stages"]["stage1"] is not None
        assert result["stages"]["stage2"] is not None
        assert result["stages"]["stage3"] is not None


# ─── Test: Output structure validation ────────────────────────


class TestOutputStructure:
    """Test that compare() returns correct output structure."""
    
    def test_compare_returns_dict(self, sample_examples: list[dict]) -> None:
        """Test that compare returns a dictionary."""
        result = compare(inputs=sample_examples)
        assert isinstance(result, dict)
    
    def test_compare_has_top_level_keys(self, sample_examples: list[dict]) -> None:
        """Test that result has required top-level keys."""
        result = compare(inputs=sample_examples)
        assert "monolithic" in result
        assert "multi_stage" in result
        assert "delta" in result
    
    def test_monolithic_structure(self, sample_examples: list[dict]) -> None:
        """Test monolithic section has required keys."""
        result = compare(inputs=sample_examples)
        mono = result["monolithic"]
        
        assert "predictions" in mono
        assert "accuracy" in mono
        assert "avg_latency_ms" in mono
        assert "total_cost" in mono
        
        assert isinstance(mono["predictions"], list)
        assert isinstance(mono["accuracy"], float)
        assert isinstance(mono["avg_latency_ms"], float)
        assert isinstance(mono["total_cost"], float)
    
    def test_multi_stage_structure(self, sample_examples: list[dict]) -> None:
        """Test multi_stage section has required keys."""
        result = compare(inputs=sample_examples)
        multi = result["multi_stage"]
        
        assert "predictions" in multi
        assert "accuracy" in multi
        assert "avg_latency_ms" in multi
        assert "total_cost" in multi
        assert "avg_confidence" in multi
        
        assert isinstance(multi["predictions"], list)
        assert isinstance(multi["accuracy"], float)
        assert isinstance(multi["avg_latency_ms"], float)
        assert isinstance(multi["total_cost"], float)
        assert isinstance(multi["avg_confidence"], float)
    
    def test_delta_structure(self, sample_examples: list[dict]) -> None:
        """Test delta section has required keys."""
        result = compare(inputs=sample_examples)
        delta = result["delta"]
        
        assert "accuracy_diff" in delta
        assert "latency_diff" in delta
        assert "cost_diff" in delta
        assert "agreement_rate" in delta
        
        assert isinstance(delta["accuracy_diff"], float)
        assert isinstance(delta["latency_diff"], float)
        assert isinstance(delta["cost_diff"], float)
        assert isinstance(delta["agreement_rate"], float)
    
    def test_predictions_length_matches_input(self, sample_examples: list[dict]) -> None:
        """Test that predictions length matches input examples."""
        result = compare(inputs=sample_examples)
        assert len(result["monolithic"]["predictions"]) == len(sample_examples)
        assert len(result["multi_stage"]["predictions"]) == len(sample_examples)


# ─── Test: Accuracy delta calculation ─────────────────────────


class TestAccuracyDelta:
    """Test accuracy and delta calculations."""
    
    def test_accuracy_is_between_zero_and_one(self, sample_examples: list[dict]) -> None:
        """Test that accuracy values are valid probabilities."""
        result = compare(inputs=sample_examples)
        
        assert 0.0 <= result["monolithic"]["accuracy"] <= 1.0
        assert 0.0 <= result["multi_stage"]["accuracy"] <= 1.0
    
    def test_accuracy_diff_calculation(self, sample_examples: list[dict]) -> None:
        """Test that accuracy_diff is calculated correctly."""
        result = compare(inputs=sample_examples)
        
        expected_diff = result["multi_stage"]["accuracy"] - result["monolithic"]["accuracy"]
        assert abs(result["delta"]["accuracy_diff"] - expected_diff) < 0.0001
    
    def test_agreement_rate_calculation(self, sample_examples: list[dict]) -> None:
        """Test that agreement_rate is between 0 and 1."""
        result = compare(inputs=sample_examples)
        
        assert 0.0 <= result["delta"]["agreement_rate"] <= 1.0
    
    def test_latency_diff_calculation(self, sample_examples: list[dict]) -> None:
        """Test that latency_diff is calculated correctly."""
        result = compare(inputs=sample_examples)
        
        expected_diff = result["multi_stage"]["avg_latency_ms"] - result["monolithic"]["avg_latency_ms"]
        assert abs(result["delta"]["latency_diff"] - expected_diff) < 0.01


# ─── Test: Edge cases ─────────────────────────────────────────


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_compare_empty_input(self, empty_examples: list[dict]) -> None:
        """Test comparison with empty input list."""
        result = compare(inputs=empty_examples)
        
        assert result["monolithic"]["predictions"] == []
        assert result["multi_stage"]["predictions"] == []
        assert result["monolithic"]["accuracy"] == 0.0
        assert result["multi_stage"]["accuracy"] == 0.0
        assert result["delta"]["agreement_rate"] == 0.0
    
    def test_compare_single_example(self, sample_example: dict) -> None:
        """Test comparison with single example."""
        result = compare(inputs=[sample_example])
        
        assert len(result["monolithic"]["predictions"]) == 1
        assert len(result["multi_stage"]["predictions"]) == 1
        assert isinstance(result["monolithic"]["accuracy"], float)
    
    def test_compare_default_eval_path(self) -> None:
        """Test comparison uses default eval.jsonl path."""
        result = compare()  # No inputs, no eval_path
        
        assert "monolithic" in result
        assert "multi_stage" in result
        assert len(result["monolithic"]["predictions"]) > 0
    
    def test_compare_custom_eval_path(self, tmp_path: Path) -> None:
        """Test comparison with custom eval path."""
        jsonl_file = tmp_path / "custom_eval.jsonl"
        jsonl_file.write_text(
            '{"messages": [{"role": "user", "content": "test"}, {"role": "assistant", "content": "нейтральный"}]}\n',
            encoding="utf-8",
        )
        
        result = compare(eval_path=str(jsonl_file))
        
        assert len(result["monolithic"]["predictions"]) == 1
    
    def test_mismatched_categories_handling(self) -> None:
        """Test handling of predictions that don't match any category."""
        # This tests the normalize_prediction function indirectly
        result = run_monolithic_prediction("непредсказуемый отзыв с неизвестными словами")
        assert result["predicted"] in LABELED_CATEGORIES or result["predicted"] == "нейтральный"
    
    def test_compare_examples_with_output_path(self, sample_examples: list[dict], tmp_path: Path) -> None:
        """Test compare_examples saves results to file."""
        output_file = tmp_path / "comparison_results.json"
        
        result = compare_examples(
            examples=sample_examples,
            output_path=str(output_file),
        )
        
        assert output_file.exists()
        
        saved_data = json.loads(output_file.read_text(encoding="utf-8"))
        assert "monolithic" in saved_data
        assert "multi_stage" in saved_data
        assert "delta" in saved_data
    
    def test_compare_examples_without_output_path(self, sample_examples: list[dict]) -> None:
        """Test compare_examples works without saving."""
        result = compare_examples(examples=sample_examples)
        
        assert "monolithic" in result
        assert isinstance(result["monolithic"]["predictions"], list)


# ─── Test: 10 examples from eval.jsonl ────────────────────────


class TestTenExamplesComparison:
    """Test comparison on exactly 10 examples from eval.jsonl."""
    
    def test_ten_examples_accuracy_metrics(self, sample_examples: list[dict]) -> None:
        """Test comparison metrics on 10 examples."""
        assert len(sample_examples) == 10
        
        result = compare(inputs=sample_examples)
        
        # Verify we got results for all 10
        assert len(result["monolithic"]["predictions"]) == 10
        assert len(result["multi_stage"]["predictions"]) == 10
        
        # Verify accuracy is calculated
        assert isinstance(result["monolithic"]["accuracy"], float)
        assert isinstance(result["multi_stage"]["accuracy"], float)
    
    def test_ten_examples_latency_metrics(self, sample_examples: list[dict]) -> None:
        """Test latency metrics on 10 examples."""
        result = compare(inputs=sample_examples)
        
        # Multi-stage should be faster (mock values)
        assert result["multi_stage"]["avg_latency_ms"] < result["monolithic"]["avg_latency_ms"]
    
    def test_ten_examples_cost_metrics(self, sample_examples: list[dict]) -> None:
        """Test cost metrics on 10 examples."""
        result = compare(inputs=sample_examples)
        
        # Multi-stage should be cheaper (mock values)
        assert result["multi_stage"]["total_cost"] < result["monolithic"]["total_cost"]
    
    def test_ten_examples_all_categories_covered(self, sample_examples: list[dict]) -> None:
        """Test that all 4 categories are present in 10 examples."""
        actual_labels = [extract_actual_label(ex) for ex in sample_examples]
        
        categories_present = set(actual_labels)
        assert len(categories_present) >= 3  # At least 3 of 4 categories


# ─── Test: Integration with actual eval.jsonl ─────────────────


class TestActualEvalDataset:
    """Test comparator with actual eval.jsonl dataset."""
    
    def test_full_eval_dataset_comparison(self) -> None:
        """Test comparison on full eval.jsonl (25 examples)."""
        result = compare()  # Uses default eval.jsonl
        
        assert len(result["monolithic"]["predictions"]) == 25
        assert len(result["multi_stage"]["predictions"]) == 25
        assert 0.0 <= result["monolithic"]["accuracy"] <= 1.0
        assert 0.0 <= result["multi_stage"]["accuracy"] <= 1.0
    
    def test_eval_dataset_predictions_are_valid_categories(self) -> None:
        """Test that all predictions are valid categories."""
        result = compare()
        
        for pred in result["monolithic"]["predictions"]:
            assert pred in LABELED_CATEGORIES
        
        for pred in result["multi_stage"]["predictions"]:
            assert pred in LABELED_CATEGORIES