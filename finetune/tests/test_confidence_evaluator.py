#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pytest",
#     "requests",
#     "rich",
#     "scikit-learn",
# ]
# ///

"""
Test suite for confidence_evaluator.py

Tests:
1. evaluate_with_confidence() returns correct structure
2. CLI arguments parsing
3. Ollama unavailable → graceful error
4. Integration with 3 confidence approaches
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests

# Add confidence directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "confidence"))

from confidence_evaluator import (
    evaluate_with_confidence,
    parse_args,
    load_examples,
    extract_fields,
    LABELED_CATEGORIES,
)


class TestEvaluateWithConfidence:
    """Test evaluate_with_confidence() function."""

    @patch('finetune.confidence.confidence_evaluator.classify')
    @patch('finetune.confidence.confidence_evaluator.self_check')
    @patch('finetune.confidence.confidence_evaluator.redundancy_check')
    @patch('finetune.confidence.confidence_evaluator.constraint_check')
    def test_returns_correct_structure(self, mock_constraint, mock_redundancy, mock_self_check, mock_classify):
        """Test that evaluate_with_confidence returns dict with all required fields."""
        # Setup mocks
        mock_classify.return_value = "позитивный"
        mock_self_check.return_value = {
            "explanation": "Model chose positive because...",
            "latency_ms": 100
        }
        mock_redundancy.return_value = {
            "votes": {"позитивный": 3},
            "consensus": "позитивный",
            "status": "OK",
            "latency_ms": 150
        }
        mock_constraint.return_value = {
            "passed": True,
            "expected": LABELED_CATEGORIES,
            "actual": "позитивный"
        }

        # Call function
        result = evaluate_with_confidence(
            user_content="Отличный товар!",
            model="qwen3:14b",
            use_confidence=True
        )

        # Verify structure
        assert "answer" in result
        assert "confidence_status" in result
        assert "explanation" in result
        assert "redundancy_votes" in result
        assert "constraint_passed" in result
        assert "latency_ms" in result

        # Verify values
        assert result["answer"] == "позитивный"
        assert result["confidence_status"] == "HIGH"  # All checks passed
        assert result["explanation"] == "Model chose positive because..."
        assert result["redundancy_votes"] == {"позитивный": 3}
        assert result["constraint_passed"] is True
        assert isinstance(result["latency_ms"], int)

    @patch('finetune.confidence.confidence_evaluator.classify')
    def test_without_confidence(self, mock_classify):
        """Test that use_confidence=False skips confidence evaluators."""
        mock_classify.return_value = "негативный"

        result = evaluate_with_confidence(
            user_content="Плохой товар",
            model="qwen3:14b",
            use_confidence=False
        )

        assert result["answer"] == "негативный"
        assert result["confidence_status"] == "UNKNOWN"
        assert result["explanation"] == ""
        assert result["redundancy_votes"] == {}
        assert result["constraint_passed"] is True

    @patch('finetune.confidence.confidence_evaluator.classify')
    @patch('finetune.confidence.confidence_evaluator.constraint_check')
    def test_constraint_failed_low_confidence(self, mock_constraint, mock_classify):
        """Test that constraint failure results in LOW confidence."""
        mock_classify.return_value = "отлично!"  # Invalid category
        mock_constraint.return_value = {
            "passed": False,
            "expected": LABELED_CATEGORIES,
            "actual": "отлично!"
        }

        result = evaluate_with_confidence(
            user_content="Some review",
            model="qwen3:14b",
            use_confidence=True
        )

        assert result["constraint_passed"] is False
        assert result["confidence_status"] == "LOW"

    @patch('finetune.confidence.confidence_evaluator.classify')
    @patch('finetune.confidence.confidence_evaluator.redundancy_check')
    @patch('finetune.confidence.confidence_evaluator.constraint_check')
    def test_no_consensus_medium_confidence(self, mock_constraint, mock_redundancy, mock_classify):
        """Test that no redundancy consensus results in MEDIUM confidence."""
        mock_classify.return_value = "позитивный"
        mock_constraint.return_value = {
            "passed": True,
            "expected": LABELED_CATEGORIES,
            "actual": "позитивный"
        }
        mock_redundancy.return_value = {
            "votes": {"позитивный": 1, "негативный": 1, "нейтральный": 1},
            "consensus": None,
            "status": "UNSURE",
            "latency_ms": 150
        }

        result = evaluate_with_confidence(
            user_content="Some review",
            model="qwen3:14b",
            use_confidence=True
        )

        assert result["constraint_passed"] is True
        assert result["confidence_status"] == "MEDIUM"


class TestOllamaUnavailable:
    """Test graceful error handling when Ollama is unavailable."""

    @patch('finetune.confidence.confidence_evaluator.requests.post')
    def test_connection_error_graceful_handling(self, mock_post):
        """Test that ConnectionError raises EnvironmentError with clear message."""
        mock_post.side_effect = requests.ConnectionError("Connection refused")

        with pytest.raises(EnvironmentError) as exc_info:
            evaluate_with_confidence(
                user_content="Test review",
                model="qwen3:14b",
                use_confidence=True
            )

        assert "Cannot connect to Ollama" in str(exc_info.value)
        assert "ollama serve" in str(exc_info.value)

    @patch('finetune.confidence.confidence_evaluator.requests.post')
    def test_http_error_graceful_handling(self, mock_post):
        """Test that HTTPError raises EnvironmentError with clear message."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        with pytest.raises(EnvironmentError) as exc_info:
            evaluate_with_confidence(
                user_content="Test review",
                model="qwen3:14b",
                use_confidence=True
            )

        assert "Ollama API error" in str(exc_info.value)


class TestParseArgs:
    """Test CLI argument parsing."""

    def test_default_args(self):
        """Test default argument values."""
        eval_path, model, use_confidence = parse_args([])

        assert eval_path == Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl"
        assert model == "qwen3:14b"
        assert use_confidence is True

    def test_eval_path_arg(self):
        """Test --eval-path argument."""
        eval_path, model, use_confidence = parse_args([
            "--eval-path", "/custom/path/eval.jsonl"
        ])

        assert eval_path == Path("/custom/path/eval.jsonl")
        assert model == "qwen3:14b"
        assert use_confidence is True

    def test_model_arg(self):
        """Test --model argument."""
        eval_path, model, use_confidence = parse_args([
            "--model", "llama3.1"
        ])

        assert eval_path == Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl"
        assert model == "llama3.1"
        assert use_confidence is True

    def test_confidence_enabled_explicit(self):
        """Test --confidence true enables confidence."""
        eval_path, model, use_confidence = parse_args([
            "--confidence", "true"
        ])

        assert use_confidence is True

    def test_confidence_disabled(self):
        """Test --confidence false disables confidence."""
        eval_path, model, use_confidence = parse_args([
            "--confidence", "false"
        ])

        assert use_confidence is False

    def test_no_confidence_flag(self):
        """Test --no-confidence disables confidence."""
        eval_path, model, use_confidence = parse_args([
            "--no-confidence"
        ])

        assert use_confidence is False

    def test_combined_args(self):
        """Test multiple arguments together."""
        eval_path, model, use_confidence = parse_args([
            "--eval-path", "/test/eval.jsonl",
            "--model", "llama3.1",
            "--no-confidence"
        ])

        assert eval_path == Path("/test/eval.jsonl")
        assert model == "llama3.1"
        assert use_confidence is False


class TestLoadExamples:
    """Test load_examples() function."""

    def test_load_eval_jsonl(self):
        """Test loading actual eval.jsonl file."""
        eval_path = Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl"

        if eval_path.exists():
            examples = load_examples(eval_path)

            assert len(examples) == 20
            assert "messages" in examples[0]
            assert isinstance(examples[0]["messages"], list)

    def test_extract_fields(self):
        """Test extract_fields() helper function."""
        example = {
            "messages": [
                {"role": "system", "content": "You are a classifier"},
                {"role": "user", "content": "Great product!"},
                {"role": "assistant", "content": "позитивный"}
            ]
        }

        system, user, assistant = extract_fields(example)

        assert system == "You are a classifier"
        assert user == "Great product!"
        assert assistant == "позитивный"


class TestIntegrationOnFiveExamples:
    """Integration test: run on 5 examples from eval.jsonl."""

    @pytest.mark.integration
    @patch('finetune.confidence.confidence_evaluator.classify')
    @patch('finetune.confidence.confidence_evaluator.self_check')
    @patch('finetune.confidence.confidence_evaluator.redundancy_check')
    def test_five_examples_integration(self, mock_redundancy, mock_self_check, mock_classify):
        """Test evaluate_with_confidence on 5 examples (mocked Ollama)."""
        # Setup mocks to return realistic responses
        mock_classify.return_value = "позитивный"
        mock_self_check.return_value = {
            "explanation": "Positive words detected: отличный, удобный",
            "latency_ms": 100
        }
        mock_redundancy.return_value = {
            "votes": {"позитивный": 3},
            "consensus": "позитивный",
            "status": "OK",
            "latency_ms": 150
        }

        # Load 5 examples
        eval_path = Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl"
        if not eval_path.exists():
            pytest.skip("eval.jsonl not found")

        examples = load_examples(eval_path)[:5]

        results = []
        for example in examples:
            _system, user_content, actual = extract_fields(example)
            result = evaluate_with_confidence(user_content, "qwen3:14b", use_confidence=True)
            results.append(result)

        # Verify all 5 results have confidence fields
        assert len(results) == 5
        for i, result in enumerate(results):
            assert "answer" in result, f"Example {i} missing 'answer'"
            assert "confidence_status" in result, f"Example {i} missing 'confidence_status'"
            assert "explanation" in result, f"Example {i} missing 'explanation'"
            assert "redundancy_votes" in result, f"Example {i} missing 'redundancy_votes'"
            assert "constraint_passed" in result, f"Example {i} missing 'constraint_passed'"
            assert "latency_ms" in result, f"Example {i} missing 'latency_ms'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])