#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "aiohttp",
# ]
# ///

"""
Redundancy Confidence Evaluator.

Implements redundancy approach: 3 parallel requests to Ollama API,
majority vote to determine consensus confidence.

Usage:
    uv run redundancy_check.py "Товар отличный, рекомендую!"
"""

from __future__ import annotations

import asyncio
import time
from typing import Final

import aiohttp

OLLAMA_URL: Final[str] = "http://localhost:11434"
SYSTEM_PROMPT: Final[str] = (
    "Ты — классификатор тональности отзывов. Определи категорию отзыва.\n"
    "Категории: крайне негативный, негативный, нейтральный, позитивный.\n"
    "Отвечай только названием категории."
)


async def _single_request(
    session: aiohttp.ClientSession,
    user_content: str,
    model: str,
    request_id: int,
) -> tuple[int, str, float]:
    """
    Send single classification request to Ollama.

    Args:
        session: aiohttp ClientSession for connection pooling
        user_content: Review text to classify
        model: Ollama model name (e.g., "qwen3:14b")
        request_id: Unique ID for this request (for logging)

    Returns:
        Tuple of (request_id, response_text, latency_seconds)
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.0,
        "stream": False,
    }

    start_time = time.perf_counter()
    async with session.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=aiohttp.ClientTimeout(total=300),
    ) as response:
        response.raise_for_status()
        data = await response.json()
        latency = time.perf_counter() - start_time

        content = data.get("message", {}).get("content", "").strip()
        return (request_id, content, latency)


async def _make_parallel_requests(
    user_content: str,
    model: str,
    n_requests: int,
) -> list[tuple[int, str, float]]:
    """
    Execute n_requests in parallel using asyncio.gather().

    Args:
        user_content: Review text to classify
        model: Ollama model name
        n_requests: Number of parallel requests (default: 3)

    Returns:
        List of (request_id, response_text, latency_seconds) tuples
    """
    async with aiohttp.ClientSession() as session:
        tasks = [
            _single_request(session, user_content, model, i)
            for i in range(n_requests)
        ]
        return await asyncio.gather(*tasks)


def _compute_majority_vote(
    responses: list[str],
) -> tuple[dict[str, int], str | None]:
    """
    Compute majority vote from responses.

    Args:
        responses: List of response strings from Ollama

    Returns:
        Tuple of (votes_dict, consensus_or_None)
        - votes_dict: Mapping of answer -> count
        - consensus: Winning answer if count > n/2, else None
    """
    votes: dict[str, int] = {}
    for response in responses:
        votes[response] = votes.get(response, 0) + 1

    # Majority means > 50% of votes
    majority_threshold = len(responses) / 2
    consensus = None
    for answer, count in votes.items():
        if count > majority_threshold:
            consensus = answer
            break

    return votes, consensus


async def redundancy_check_async(
    user_content: str,
    model: str = "qwen3:14b",
    n_requests: int = 3,
) -> dict:
    """
    Perform redundancy confidence evaluation.

    Sends n_requests in parallel to Ollama API, computes majority vote
    to determine consensus confidence.

    Args:
        user_content: Review text to classify
        model: Ollama model name (default: "qwen3:14b")
        n_requests: Number of parallel requests (default: 3)

    Returns:
        Dictionary containing:
        - votes: dict mapping answer -> count
        - consensus: str or None (winning answer if majority exists)
        - status: "OK" if consensus found, "UNSURE" otherwise
        - latency_ms: Total execution time in milliseconds
        - raw_responses: list of all response strings (for debugging)
    """
    start_time = time.perf_counter()

    # Execute parallel requests
    results = await _make_parallel_requests(user_content, model, n_requests)

    # Extract responses and compute latency
    responses = [result[1] for result in results]
    latencies = [result[2] for result in results]
    total_latency_ms = (time.perf_counter() - start_time) * 1000

    # Compute majority vote
    votes, consensus = _compute_majority_vote(responses)

    # Determine status
    status = "OK" if consensus is not None else "UNSURE"

    return {
        "votes": votes,
        "consensus": consensus,
        "status": status,
        "latency_ms": round(total_latency_ms, 2),
        "avg_latency_ms": round(sum(latencies) / len(latencies) * 1000, 2),
        "raw_responses": responses,
    }


def redundancy_check(
    user_content: str,
    model: str = "qwen3:14b",
    n_requests: int = 3,
) -> dict:
    """
    Synchronous wrapper for redundancy_check_async.

    Perform redundancy confidence evaluation with 3 parallel requests
    to Ollama API, using majority vote to determine consensus.

    Args:
        user_content: Review text to classify
        model: Ollama model name (default: "qwen3:14b")
        n_requests: Number of parallel requests (default: 3)

    Returns:
        Dictionary containing:
        - votes: dict mapping answer -> count
        - consensus: str or None (winning answer if majority exists)
        - status: "OK" if consensus found, "UNSURE" otherwise
        - latency_ms: Total execution time in milliseconds

    Example:
        >>> result = redundancy_check("Товар отличный, рекомендую!")
        >>> print(f"Status: {result['status']}, Consensus: {result['consensus']}")
        Status: OK, Consensus: позитивный
    """
    return asyncio.run(
        redundancy_check_async(user_content, model, n_requests)
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python redundancy_check.py <review_text>")
        sys.exit(1)

    review_text = " ".join(sys.argv[1:])

    print(f"Running redundancy check for: {review_text!r}")
    print(f"Model: qwen3:14b, Requests: 3\n")

    result = redundancy_check(review_text)

    print(f"Votes: {result['votes']}")
    print(f"Consensus: {result['consensus']}")
    print(f"Status: {result['status']}")
    print(f"Latency: {result['latency_ms']} ms (avg: {result['avg_latency_ms']} ms)")
    print(f"Raw responses: {result['raw_responses']}")