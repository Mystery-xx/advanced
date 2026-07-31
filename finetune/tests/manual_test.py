#!/usr/bin/env python3
"""
Manual test for confidence_evaluator.py
Tests structure and logic without requiring pytest or Ollama.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add confidence directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "confidence"))

from confidence_evaluator import (
    evaluate_with_confidence,
    parse_args,
    load_examples,
    extract_fields,
    LABELED_CATEGORIES,
)


def test_evaluate_with_confidence_structure():
    """Test that evaluate_with_confidence returns dict with all required fields."""
    print("\n" + "="*80)
    print("Test 1: evaluate_with_confidence() structure")
    print("="*80)
    
    with patch('confidence_evaluator.classify') as mock_classify, \
         patch('confidence_evaluator.self_check') as mock_self_check, \
         patch('confidence_evaluator.redundancy_check') as mock_redundancy, \
         patch('confidence_evaluator.constraint_check') as mock_constraint:
        
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
        required_fields = [
            "answer", "confidence_status", "explanation",
            "redundancy_votes", "constraint_passed", "latency_ms"
        ]
        
        missing = [f for f in required_fields if f not in result]
        if missing:
            print(f"❌ FAIL: Missing fields: {missing}")
            return False
        
        # Verify values
        assert result["answer"] == "позитивный"
        assert result["confidence_status"] == "HIGH"  # All checks passed
        assert result["explanation"] == "Model chose positive because..."
        assert result["redundancy_votes"] == {"позитивный": 3}
        assert result["constraint_passed"] is True
        assert isinstance(result["latency_ms"], int)
        
        print("✓ All required fields present")
        print(f"  - answer: {result['answer']}")
        print(f"  - confidence_status: {result['confidence_status']}")
        print(f"  - explanation: {result['explanation'][:50]}...")
        print(f"  - redundancy_votes: {result['redundancy_votes']}")
        print(f"  - constraint_passed: {result['constraint_passed']}")
        print(f"  - latency_ms: {result['latency_ms']}")
        print("✓ PASS")
        return True


def test_without_confidence():
    """Test that use_confidence=False skips confidence evaluators."""
    print("\n" + "="*80)
    print("Test 2: use_confidence=False")
    print("="*80)
    
    with patch('confidence_evaluator.classify') as mock_classify:
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
        
        print("✓ Confidence evaluators skipped")
        print(f"  - answer: {result['answer']}")
        print(f"  - confidence_status: {result['confidence_status']}")
        print("✓ PASS")
        return True


def test_constraint_failed():
    """Test that constraint failure results in LOW confidence."""
    print("\n" + "="*80)
    print("Test 3: Constraint failure → LOW confidence")
    print("="*80)
    
    with patch('confidence_evaluator.classify') as mock_classify, \
         patch('confidence_evaluator.constraint_check') as mock_constraint:
        
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
        
        print("✓ Constraint failure detected")
        print(f"  - constraint_passed: {result['constraint_passed']}")
        print(f"  - confidence_status: {result['confidence_status']}")
        print("✓ PASS")
        return True


def test_parse_args():
    """Test CLI argument parsing."""
    print("\n" + "="*80)
    print("Test 4: CLI argument parsing")
    print("="*80)
    
    # Test defaults
    eval_path, model, use_confidence = parse_args([])
    assert eval_path == Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl"
    assert model == "qwen3:14b"
    assert use_confidence is True
    print("✓ Default args correct")
    
    # Test --eval-path
    eval_path, model, use_confidence = parse_args(["--eval-path", "/custom/eval.jsonl"])
    assert eval_path == Path("/custom/eval.jsonl")
    print("✓ --eval-path works")
    
    # Test --model
    eval_path, model, use_confidence = parse_args(["--model", "llama3.1"])
    assert model == "llama3.1"
    print("✓ --model works")
    
    # Test --confidence false
    eval_path, model, use_confidence = parse_args(["--confidence", "false"])
    assert use_confidence is False
    print("✓ --confidence false works")
    
    # Test --no-confidence
    eval_path, model, use_confidence = parse_args(["--no-confidence"])
    assert use_confidence is False
    print("✓ --no-confidence works")
    
    print("✓ PASS")
    return True


def test_load_examples():
    """Test loading eval.jsonl."""
    print("\n" + "="*80)
    print("Test 5: Load eval.jsonl")
    print("="*80)
    
    eval_path = Path(__file__).resolve().parent.parent / "dataset" / "eval.jsonl"
    
    if not eval_path.exists():
        print(f"⚠ SKIP: eval.jsonl not found at {eval_path}")
        return True
    
    examples = load_examples(eval_path)
    assert len(examples) == 20
    assert "messages" in examples[0]
    
    print(f"✓ Loaded {len(examples)} examples")
    print("✓ PASS")
    return True


def test_ollama_unavailable():
    """Test graceful error handling when Ollama is unavailable."""
    print("\n" + "="*80)
    print("Test 6: Ollama unavailable → graceful error")
    print("="*80)
    
    import requests
    from unittest.mock import patch
    
    with patch('confidence_evaluator.requests.post') as mock_post:
        mock_post.side_effect = requests.ConnectionError("Connection refused")
        
        try:
            evaluate_with_confidence(
                user_content="Test review",
                model="qwen3:14b",
                use_confidence=True
            )
            print("❌ FAIL: Should have raised EnvironmentError")
            return False
        except EnvironmentError as e:
            assert "Cannot connect to Ollama" in str(e)
            assert "ollama serve" in str(e)
            print(f"✓ EnvironmentError raised with clear message")
            print(f"  Message: {str(e)[:80]}...")
            print("✓ PASS")
            return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("CONFIDENCE EVALUATOR - MANUAL TEST SUITE")
    print("="*80)
    
    tests = [
        ("Structure test", test_evaluate_with_confidence_structure),
        ("Without confidence", test_without_confidence),
        ("Constraint failure", test_constraint_failed),
        ("CLI args", test_parse_args),
        ("Load examples", test_load_examples),
        ("Ollama error handling", test_ollama_unavailable),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")
        sys.exit(1)