"""
Tests for constraint-based confidence evaluator.

Tests verify that constraint_check() correctly validates model answers
against the set of allowed categories.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from finetune.confidence.constraint_check import constraint_check, LABELED_CATEGORIES


def test_valid_categories():
    """Test that all 4 valid categories pass the constraint check."""
    valid_categories = [
        "крайне негативный",
        "негативный",
        "нейтральный",
        "позитивный",
    ]

    print("Testing valid categories (should all pass)...")
    for category in valid_categories:
        result = constraint_check(category)
        assert result["passed"] is True, f"Expected {category} to pass"
        assert result["actual"] == category
        assert result["expected"] == LABELED_CATEGORIES
        print(f"  ✓ '{category}' → passed=True")

    print(f"All {len(valid_categories)} valid categories passed.\n")


def test_invalid_category():
    """Test that an invalid category fails the constraint check."""
    invalid_answer = "отлично!"

    print("Testing invalid category (should fail)...")
    result = constraint_check(invalid_answer)
    assert result["passed"] is False, f"Expected '{invalid_answer}' to fail"
    assert result["actual"] == invalid_answer
    assert result["expected"] == LABELED_CATEGORIES
    print(f"  ✓ '{invalid_answer}' → passed=False\n")


def test_custom_categories():
    """Test with custom expected_categories parameter."""
    custom_categories = ["good", "bad"]

    print("Testing custom categories...")
    result_good = constraint_check("good", expected_categories=custom_categories)
    assert result_good["passed"] is True
    assert result_good["expected"] == custom_categories
    print(f"  ✓ 'good' with custom categories → passed=True")

    result_bad = constraint_check("excellent", expected_categories=custom_categories)
    assert result_bad["passed"] is False
    print(f"  ✓ 'excellent' with custom categories → passed=False\n")


def test_case_sensitivity():
    """Test that category matching handles case via normalization."""
    print("Testing case sensitivity...")

    # Exact case match should pass
    result_exact = constraint_check("позитивный")
    assert result_exact["passed"] is True
    print(f"  ✓ 'позитивный' (exact) → passed=True")

    # Different case should also pass due to .lower() normalization
    result_upper = constraint_check("ПОЗИТИВНЫЙ")
    assert result_upper["passed"] is True
    print(f"  ✓ 'ПОЗИТИВНЫЙ' (uppercase, normalized) → passed=True")

    # Mixed case should pass too
    result_mixed = constraint_check("Позитивный")
    assert result_mixed["passed"] is True
    print(f"  ✓ 'Позитивный' (mixed case, normalized) → passed=True\n")


def test_whitespace_handling():
    """Test that whitespace is stripped during normalization."""
    print("Testing whitespace handling...")

    # Leading/trailing whitespace should pass due to .strip()
    result_with_space = constraint_check(" позитивный ")
    assert result_with_space["passed"] is True
    print(f"  ✓ ' позитивный ' (with spaces, stripped) → passed=True")

    result_exact = constraint_check("позитивный")
    assert result_exact["passed"] is True
    print(f"  ✓ 'позитивный' (no spaces) → passed=True\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Constraint Check Tests")
    print("=" * 60 + "\n")

    test_valid_categories()
    test_invalid_category()
    test_custom_categories()
    test_case_sensitivity()
    test_whitespace_handling()

    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)