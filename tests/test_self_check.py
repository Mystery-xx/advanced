"""
Test script for self_check confidence evaluator.

Tests:
1. Example #4 from eval.jsonl (позитивный отзыв "Отличная тачка для дачи")
   - Expected: explanation contains arguments from the review
2. Edge case: empty text
   - Expected: explanation contains "недостаточно данных"
"""

import sys
sys.path.insert(0, "/mnt/f/git/advanced/finetune")

from confidence.self_check import self_check


def test_example_4_positive_review():
    """Test self_check with example #4 from eval.jsonl - positive review."""
    example_4_content = (
        "Отличная тачка для дачи – крепкая, удобная и очень выносливая. "
        "Брал для дачи: возил землю, камни, мусор – справляется на ура. "
        "Усиленная рама не гнётся даже под 200 кг, удобные прорезиненные ручки. "
        "Собирается за 15 минут, стоит устойчиво. За эти деньги – один из лучших вариантов."
    )
    
    print("Test 1: Example #4 (позитивный отзыв)")
    print("=" * 70)
    print(f"Input: {example_4_content[:100]}...")
    print()
    
    # Use llama3.1:8b as default test model (qwen3:14b may not be available)
    import os
    test_model = os.environ.get("TEST_MODEL", "llama3.1:8b")
    result = self_check(example_4_content, "позитивный", model=test_model)
    
    print(f"Explanation: {result['explanation']}")
    print(f"Latency: {result['latency_ms']} ms")
    print()
    
    # Verify explanation contains arguments
    explanation_lower = result['explanation'].lower()
    
    # Check for key positive indicators from the review
    has_arguments = any([
        'отличн' in explanation_lower,  # отличная
        'крепк' in explanation_lower,   # крепкая
        'удобн' in explanation_lower,   # удобная
        'вынослив' in explanation_lower,  # выносливая
        'лучш' in explanation_lower,    # лучший
        'справля' in explanation_lower,  # справляется
        'положительн' in explanation_lower,  # положительный
        'превосход' in explanation_lower,  # превосходный
    ])
    
    assert has_arguments, (
        f"Explanation should contain arguments from the review. "
        f"Got: {result['explanation']}"
    )
    
    # Verify latency is reasonable (should be > 0 and < 60000ms)
    assert 0 < result['latency_ms'] < 60000, (
        f"Latency should be reasonable. Got: {result['latency_ms']} ms"
    )
    
    print("✓ Test 1 PASSED: explanation contains arguments\n")


def test_empty_text_edge_case():
    """Test self_check with empty user content."""
    print("Test 2: Edge case - empty text")
    print("=" * 70)
    print("Input: (empty string)")
    print()
    
    result = self_check("", "позитивный")
    
    print(f"Explanation: {result['explanation']}")
    print(f"Latency: {result['latency_ms']} ms")
    print()
    
    # Verify explanation contains "недостаточно данных"
    assert "недостаточно данных" in result['explanation'], (
        f"Explanation should contain 'недостаточно данных'. "
        f"Got: {result['explanation']}"
    )
    
    # Verify latency is 0 for edge case (no API call made)
    assert result['latency_ms'] == 0, (
        f"Latency should be 0 for empty input. Got: {result['latency_ms']} ms"
    )
    
    print("✓ Test 2 PASSED: explanation contains 'недостаточно данных'\n")


def test_whitespace_only_edge_case():
    """Test self_check with whitespace-only user content."""
    print("Test 3: Edge case - whitespace only")
    print("=" * 70)
    print("Input: '   ' (whitespace only)")
    print()
    
    result = self_check("   ", "позитивный")
    
    print(f"Explanation: {result['explanation']}")
    print(f"Latency: {result['latency_ms']} ms")
    print()
    
    # Verify explanation contains "недостаточно данных"
    assert "недостаточно данных" in result['explanation'], (
        f"Explanation should contain 'недостаточно данных'. "
        f"Got: {result['explanation']}"
    )
    
    # Verify latency is 0 for edge case (no API call made)
    assert result['latency_ms'] == 0, (
        f"Latency should be 0 for whitespace input. Got: {result['latency_ms']} ms"
    )
    
    print("✓ Test 3 PASSED: explanation contains 'недостаточно данных'\n")


if __name__ == "__main__":
    print("Running self_check tests...")
    print("=" * 70)
    print()
    
    all_passed = True
    
    try:
        test_example_4_positive_review()
    except Exception as e:
        print(f"✗ Test 1 FAILED: {e}\n")
        all_passed = False
    
    try:
        test_empty_text_edge_case()
    except Exception as e:
        print(f"✗ Test 2 FAILED: {e}\n")
        all_passed = False
    
    try:
        test_whitespace_only_edge_case()
    except Exception as e:
        print(f"✗ Test 3 FAILED: {e}\n")
        all_passed = False
    
    print("=" * 70)
    if all_passed:
        print("ALL TESTS PASSED ✓")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED ✗")
        sys.exit(1)