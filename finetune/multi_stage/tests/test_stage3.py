#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pytest",
# ]
# ///

"""
Test suite for Stage3Formatter.

Tests:
1. Valid categories are accepted (4 categories)
2. Invalid categories are rejected
3. Confidence validation (0.0-1.0 range)
4. Output format structure
5. Stage execute() method integration
"""

import pytest
import sys
from pathlib import Path

# Add finetune directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from finetune.multi_stage.base import StageInput, StageOutput
from finetune.multi_stage.stage3_formatter import Stage3Formatter, VALID_CATEGORIES


class TestValidCategories:
    """Test that all 4 valid categories are accepted."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Stage3Formatter()

    def test_valid_category_kraine_negativny(self):
        """Test 'крайне негативный' is validated as True."""
        result = self.formatter.format("крайне негативный", {})
        
        assert result["validated"] is True
        assert result["category"] == "крайне негативный"
        assert result["errors"] == []

    def test_valid_category_negativny(self):
        """Test 'негативный' is validated as True."""
        result = self.formatter.format("негативный", {})
        
        assert result["validated"] is True
        assert result["category"] == "негативный"
        assert result["errors"] == []

    def test_valid_category_neutralny(self):
        """Test 'нейтральный' is validated as True."""
        result = self.formatter.format("нейтральный", {})
        
        assert result["validated"] is True
        assert result["category"] == "нейтральный"
        assert result["errors"] == []

    def test_valid_category_pozitivny(self):
        """Test 'позитивный' is validated as True."""
        result = self.formatter.format("позитивный", {})
        
        assert result["validated"] is True
        assert result["category"] == "позитивный"
        assert result["errors"] == []


class TestInvalidCategories:
    """Test that invalid categories are rejected."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Stage3Formatter()

    def test_invalid_category_random_text(self):
        """Test random text is rejected."""
        result = self.formatter.format("отлично!", {})
        
        assert result["validated"] is False
        assert result["category"] == "отлично!"
        assert len(result["errors"]) > 0
        assert "Invalid category" in result["errors"][0]

    def test_invalid_category_empty_string(self):
        """Test empty string is rejected."""
        result = self.formatter.format("", {})
        
        assert result["validated"] is False
        assert len(result["errors"]) > 0

    def test_invalid_category_similar_but_wrong(self):
        """Test similar but incorrect category is rejected."""
        result = self.formatter.format("положительный", {})
        
        assert result["validated"] is False
        assert "Invalid category" in result["errors"][0]


class TestConfidenceValidation:
    """Test confidence score validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Stage3Formatter()

    def test_confidence_valid_range(self):
        """Test confidence in valid range [0.0, 1.0]."""
        result = self.formatter.format("позитивный", {}, confidence=0.85)
        
        assert result["confidence"] == 0.85
        assert isinstance(result["confidence"], float)

    def test_confidence_zero(self):
        """Test confidence = 0.0 is valid."""
        result = self.formatter.format("позитивный", {}, confidence=0.0)
        
        assert result["confidence"] == 0.0

    def test_confidence_one(self):
        """Test confidence = 1.0 is valid."""
        result = self.formatter.format("позитивный", {}, confidence=1.0)
        
        assert result["confidence"] == 1.0

    def test_confidence_above_range_clamped(self):
        """Test confidence > 1.0 is clamped to 1.0."""
        result = self.formatter.format("позитивный", {}, confidence=1.5)
        
        assert result["confidence"] == 1.0
        assert any("Confidence must be between" in err for err in result["errors"])

    def test_confidence_below_range_clamped(self):
        """Test confidence < 0.0 is clamped to 0.0."""
        result = self.formatter.format("позитивный", {}, confidence=-0.3)
        
        assert result["confidence"] == 0.0
        assert any("Confidence must be between" in err for err in result["errors"])

    def test_confidence_invalid_type_string(self):
        """Test invalid confidence type (string) defaults to 0.5."""
        result = self.formatter.format("позитивный", {}, confidence="high")
        
        assert result["confidence"] == 0.5
        assert any("Confidence must be a number" in err for err in result["errors"])

    def test_confidence_default_value(self):
        """Test default confidence is 0.5."""
        result = self.formatter.format("позитивный", {})
        
        assert result["confidence"] == 0.5


class TestOutputFormat:
    """Test output format structure."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Stage3Formatter()

    def test_output_has_required_keys(self):
        """Test output dict has all required keys."""
        result = self.formatter.format("позитивный", {}, confidence=0.9)
        
        assert "category" in result
        assert "confidence" in result
        assert "validated" in result
        assert "errors" in result

    def test_output_key_types(self):
        """Test output values have correct types."""
        result = self.formatter.format("позитивный", {}, confidence=0.9)
        
        assert isinstance(result["category"], str)
        assert isinstance(result["confidence"], float)
        assert isinstance(result["validated"], bool)
        assert isinstance(result["errors"], list)

    def test_output_errors_empty_when_valid(self):
        """Test errors list is empty when validated=True."""
        result = self.formatter.format("нейтральный", {}, confidence=0.7)
        
        assert result["validated"] is True
        assert result["errors"] == []

    def test_output_errors_populated_when_invalid(self):
        """Test errors list has items when validated=False."""
        result = self.formatter.format("invalid", {}, confidence=0.5)
        
        assert result["validated"] is False
        assert len(result["errors"]) > 0


class TestStageExecute:
    """Test Stage execute() method integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Stage3Formatter()

    def test_execute_valid_classification(self):
        """Test execute() with valid classification."""
        input_data = StageInput(
            data={
                "classification": "позитивный",
                "stage1_output": {"preprocessed": True},
                "confidence": 0.92
            }
        )
        
        output = self.formatter.execute(input_data)
        
        assert isinstance(output, StageOutput)
        assert output.success is True
        assert output.result["category"] == "позитивный"
        assert output.result["validated"] is True
        assert output.result["confidence"] == 0.92

    def test_execute_invalid_classification(self):
        """Test execute() with invalid classification."""
        input_data = StageInput(
            data={
                "classification": "супер!",
                "stage1_output": {},
                "confidence": 0.8
            }
        )
        
        output = self.formatter.execute(input_data)
        
        assert isinstance(output, StageOutput)
        assert output.success is False  # Should fail validation
        assert output.result["validated"] is False
        assert len(output.result["errors"]) > 0

    def test_execute_missing_confidence(self):
        """Test execute() uses default confidence when not provided."""
        input_data = StageInput(
            data={
                "classification": "негативный",
                "stage1_output": {}
                # confidence not provided
            }
        )
        
        output = self.formatter.execute(input_data)
        
        assert output.success is True
        assert output.result["confidence"] == 0.5

    def test_execute_stage_name(self):
        """Test stage name property."""
        assert self.formatter.name == "stage3_formatter"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Stage3Formatter()

    def test_category_with_whitespace(self):
        """Test category with leading/trailing whitespace."""
        result = self.formatter.format("  позитивный  ", {})
        
        # constraint_check normalizes whitespace
        assert result["validated"] is True

    def test_category_with_punctuation(self):
        """Test category with trailing punctuation."""
        result = self.formatter.format("позитивный!", {})
        
        # constraint_check strips punctuation
        assert result["validated"] is True

    def test_case_insensitive_category(self):
        """Test category matching is case-insensitive."""
        result = self.formatter.format("Позитивный", {})
        
        # constraint_check normalizes case
        assert result["validated"] is True

    def test_stage1_output_ignored(self):
        """Test that stage1_output doesn't affect validation."""
        result1 = self.formatter.format("позитивный", {"preprocessed": True})
        result2 = self.formatter.format("позитивный", {})
        
        assert result1["validated"] == result2["validated"]
        assert result1["category"] == result2["category"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])