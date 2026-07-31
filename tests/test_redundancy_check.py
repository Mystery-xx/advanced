#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pytest",
#     "pytest-asyncio",
# ]
# ///

"""
Tests for redundancy_check.py

Test scenarios:
1. 3 identical answers → consensus found, status=OK
2. 3 different answers → no consensus, status=UNSURE
"""

import asyncio
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "finetune" / "confidence"))

from redundancy_check import _compute_majority_vote, redundancy_check_async


def test_majority_vote_identical():
    """Test majority vote with 3 identical answers."""
    responses = ["позитивный", "позитивный", "позитивный"]
    votes, consensus = _compute_majority_vote(responses)

    assert votes == {"позитивный": 3}, f"Expected 3 votes for 'позитивный', got {votes}"
    assert consensus == "позитивный", f"Expected consensus 'позитивный', got {consensus}"
    print("✓ Test 1 PASSED: 3 identical answers → consensus='позитивный'")


def test_majority_vote_two_same():
    """Test majority vote with 2 same, 1 different (majority exists)."""
    responses = ["негативный", "негативный", "нейтральный"]
    votes, consensus = _compute_majority_vote(responses)

    assert votes == {"негативный": 2, "нейтральный": 1}, f"Unexpected votes: {votes}"
    assert consensus == "негативный", f"Expected consensus 'негативный', got {consensus}"
    print("✓ Test 2 PASSED: 2 same + 1 different → consensus='негативный'")


def test_majority_vote_all_different():
    """Test majority vote with 3 different answers (no majority)."""
    responses = ["позитивный", "негативный", "нейтральный"]
    votes, consensus = _compute_majority_vote(responses)

    assert votes == {
        "позитивный": 1,
        "негативный": 1,
        "нейтральный": 1,
    }, f"Unexpected votes: {votes}"
    assert consensus is None, f"Expected no consensus, got {consensus}"
    print("✓ Test 3 PASSED: 3 different answers → consensus=None")


def test_majority_vote_four_requests():
    """Test majority vote with 4 requests (edge case: 2-2 split)."""
    responses = ["позитивный", "позитивный", "негативный", "негативный"]
    votes, consensus = _compute_majority_vote(responses)

    assert votes == {"позитивный": 2, "негативный": 2}, f"Unexpected votes: {votes}"
    # 2 is not > 4/2 (2), so no majority
    assert consensus is None, f"Expected no consensus for 2-2 split, got {consensus}"
    print("✓ Test 4 PASSED: 2-2 split (4 requests) → consensus=None")


def test_majority_vote_four_with_majority():
    """Test majority vote with 4 requests where one has 3 votes."""
    responses = ["крайне негативный", "крайне негативный", "крайне негативный", "нейтральный"]
    votes, consensus = _compute_majority_vote(responses)

    assert votes == {"крайне негативный": 3, "нейтральный": 1}, f"Unexpected votes: {votes}"
    assert consensus == "крайне негативный", f"Expected consensus, got {consensus}"
    print("✓ Test 5 PASSED: 3-1 split (4 requests) → consensus='крайне негативный'")


@pytest.mark.asyncio
async def test_async_redundancy_check_structure():
    """Test that async function returns correct structure (mock test)."""
    # This test verifies the structure without requiring Ollama running
    # We mock the _make_parallel_requests function
    from redundancy_check import _make_parallel_requests

    # Store original function
    import redundancy_check

    original_make_requests = redundancy_check._make_parallel_requests

    # Mock function that returns predetermined responses
    async def mock_make_requests(user_content, model, n_requests):
        # Simulate 3 identical responses with latencies
        return [
            (0, "позитивный", 0.5),
            (1, "позитивный", 0.6),
            (2, "позитивный", 0.55),
        ]

    # Replace with mock
    redundancy_check._make_parallel_requests = mock_make_requests

    try:
        result = await redundancy_check_async("Товар отличный!")

        assert "votes" in result, "Missing 'votes' key"
        assert "consensus" in result, "Missing 'consensus' key"
        assert "status" in result, "Missing 'status' key"
        assert "latency_ms" in result, "Missing 'latency_ms' key"
        assert "raw_responses" in result, "Missing 'raw_responses' key"

        assert result["status"] == "OK", f"Expected status 'OK', got {result['status']}"
        assert result["consensus"] == "позитивный", f"Expected consensus 'позитивный', got {result['consensus']}"
        assert result["votes"] == {"позитивный": 3}, f"Unexpected votes: {result['votes']}"

        print("✓ Test 6 PASSED: Async function returns correct structure")
    finally:
        # Restore original function
        redundancy_check._make_parallel_requests = original_make_requests


@pytest.mark.asyncio
async def test_async_redundancy_check_unsure():
    """Test that async function returns UNSURE when no consensus."""
    from redundancy_check import _make_parallel_requests

    import redundancy_check

    original_make_requests = redundancy_check._make_parallel_requests

    # Mock function that returns different responses
    async def mock_make_requests(user_content, model, n_requests):
        return [
            (0, "позитивный", 0.5),
            (1, "негативный", 0.6),
            (2, "нейтральный", 0.55),
        ]

    redundancy_check._make_parallel_requests = mock_make_requests

    try:
        result = await redundancy_check_async("Товар так себе.")

        assert result["status"] == "UNSURE", f"Expected status 'UNSURE', got {result['status']}"
        assert result["consensus"] is None, f"Expected no consensus, got {result['consensus']}"
        assert len(result["votes"]) == 3, f"Expected 3 different votes, got {result['votes']}"

        print("✓ Test 7 PASSED: 3 different answers → status='UNSURE'")
    finally:
        redundancy_check._make_parallel_requests = original_make_requests


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running redundancy_check tests")
    print("=" * 60)

    # Synchronous tests
    test_majority_vote_identical()
    test_majority_vote_two_same()
    test_majority_vote_all_different()
    test_majority_vote_four_requests()
    test_majority_vote_four_with_majority()

    # Async tests
    asyncio.run(test_async_redundancy_check_structure())
    asyncio.run(test_async_redundancy_check_unsure())

    print("=" * 60)
    print("All 7 tests PASSED ✓")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()