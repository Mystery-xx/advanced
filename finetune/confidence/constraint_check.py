"""
Constraint-based confidence evaluator.

Validates that model answers belong to the set of allowed categories.
Pure synchronous function — no API calls.
"""

from typing import Final

# Default categories from finetune/baseline/run_baseline.py
LABELED_CATEGORIES: Final[list[str]] = [
    "крайне негативный",
    "негативный",
    "нейтральный",
    "позитивный",
]


def constraint_check(answer: str, expected_categories: list[str] = None) -> dict:
    """
    Check if the answer belongs to the set of allowed categories.

    Parameters
    ----------
    answer : str
        The model's predicted category string.
    expected_categories : list[str], optional
        List of valid category names. Defaults to LABELED_CATEGORIES.

    Returns
    -------
    dict
        Dictionary with keys:
        - passed (bool): True if answer is in expected_categories
        - expected (list[str]): The list of valid categories
        - actual (str): The actual answer provided

    Examples
    --------
    >>> constraint_check("позитивный")
    {'passed': True, 'expected': [...], 'actual': 'позитивный'}

    >>> constraint_check("отлично!")
    {'passed': False, 'expected': [...], 'actual': 'отлично!'}
    """
    if expected_categories is None:
        expected_categories = LABELED_CATEGORIES

    # Normalize both sides: lowercase + strip whitespace + strip trailing punctuation
    answer_normalized = answer.strip().lower().rstrip(".,!?;:")
    expected_normalized = [cat.strip().lower() for cat in expected_categories]
    passed = answer_normalized in expected_normalized

    return {
        "passed": passed,
        "expected": expected_categories,
        "actual": answer,
    }


if __name__ == "__main__":
    # Quick self-test
    test_cases = [
        ("крайне негативный", True),
        ("негативный", True),
        ("нейтральный", True),
        ("позитивный", True),
        ("отлично!", False),
    ]

    print("Running self-tests...")
    for answer, expected_pass in test_cases:
        result = constraint_check(answer)
        status = "✓" if result["passed"] == expected_pass else "✗"
        print(f"{status} constraint_check('{answer}') → passed={result['passed']} (expected {expected_pass})")