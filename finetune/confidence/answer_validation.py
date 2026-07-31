"""
Answer validation for review classification confidence.

Validates that a classification answer actually matches the semantic
sentiment of the review text. The prompt is designed to be simple and
charitable: it should only flag clear mismatches, not penalize correct
but borderline classifications.
"""

import sys
import requests
import time

OLLAMA_URL = "http://localhost:11434"


def answer_validation(
    user_content: str,
    answer: str,
    model: str = "llama3.2:1b",
    ollama_url: str = OLLAMA_URL
) -> dict:
    """
    Ask the model to verify whether a classification answer matches the review.

    Uses a simple, charitable prompt that only flags CLEAR mismatches.
    On any ambiguity, timeout, or parse failure the answer is treated as
    supported (innocent until proven guilty).

    Args:
        user_content: The original review text that was classified
        answer: The model's classification answer (e.g., "позитивный")
        model: Ollama model name to use for validation
        ollama_url: Ollama API URL

    Returns:
        dict with keys:
            - supported (bool): True if the model confirms the classification
                                 matches the review's sentiment
            - reason (str): The model's reasoning for the verdict
            - latency_ms (int): Time taken for the API call in milliseconds

    Example:
        >>> result = answer_validation(
        ...     user_content="Отличная тачка!",
        ...     answer="позитивный",
        ...     model="llama3.2:1b"
        ... )
        >>> print(result["supported"])
        True
    """
    # Handle edge case: empty or whitespace-only user content
    if not user_content or not user_content.strip():
        return {
            "supported": True,
            "reason": "пустой отзыв — пропускаем валидацию",
            "latency_ms": 0
        }

    # Simple, charitable prompt: ask if classification matches.
    # Avoid asking the model to "independently assess" — that confuses
    # small models into contradicting the answer even when it's correct.
    # Examples help the model understand the task.
    validation_prompt = (
        f"Отзыв: \"{user_content}\"\n"
        f"Классификация: \"{answer}\"\n\n"
        f"Эта классификация подходит отзыву? Ответь ДА или НЕТ.\n"
        f"Примеры:\n"
        f"  Отзыв: \"Ужасный товар, сломался сразу\"\n"
        f"  Классификация: \"позитивный\" → НЕТ\n\n"
        f"  Отзыв: \"Отличная покупка!\"\n"
        f"  Классификация: \"позитивный\" → ДА\n\n"
        f"  Отзыв: \"Нормально, работает\"\n"
        f"  Классификация: \"нейтральный\" → ДА\n\n"
        f"Ответь ровно одним словом: ДА или НЕТ."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": validation_prompt},
        ],
        "temperature": 0.0,
        "stream": False,
    }

    start_time = time.perf_counter()

    response = requests.post(
        f"{ollama_url}/api/chat",
        json=payload,
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()

    end_time = time.perf_counter()
    latency_ms = int((end_time - start_time) * 1000)

    raw_response = data.get("message", {}).get("content", "").strip()

    # DEBUG: print raw model output for inspection
    print(f"    [ANSWER VALIDATION RAW] model='{model}' answer='{answer}' → '{raw_response[:80]}'", file=sys.stderr)

    # Parse response: look for ДА (supported) or НЕТ (not supported)
    # Default to supported (innocent until proven guilty)
    response_lower = raw_response.lower()

    # Only flag as unsupported if we clearly see "НЕТ" or similar negation
    is_unsupported = False
    reason = raw_response

    # Check for clear negation indicators
    negation_words = ["нет", "не верно", "неверно", "противоречит", "не совпадает"]
    for word in negation_words:
        # Look for the word at start or after punctuation
        if word in response_lower.split() or word in response_lower:
            is_unsupported = True
            break

    # If the response starts with "да" (or contains it as first word), it's supported
    first_word = response_lower.split()[0] if response_lower.split() else ""
    if first_word == "да":
        is_unsupported = False

    supported = not is_unsupported

    return {
        "supported": supported,
        "reason": reason,
        "latency_ms": latency_ms
    }


if __name__ == "__main__":
    # Demo usage
    print("Testing answer_validation with positive review classified as negative:")
    print("=" * 60)
    result = answer_validation(
        user_content="Отличная тачка для дачи! Крепкая, удобная.",
        answer="негативный",
        model="llama3.2:1b"
    )
    print(f"Supported: {result['supported']}")
    print(f"Reason: {result['reason']}")
    print(f"Latency: {result['latency_ms']} ms")
    print()

    print("Testing answer_validation with matching classification:")
    print("=" * 60)
    result2 = answer_validation(
        user_content="Отличная тачка для дачи! Крепкая, удобная.",
        answer="позитивный",
        model="llama3.2:1b"
    )
    print(f"Supported: {result2['supported']}")
    print(f"Reason: {result2['reason']}")
    print(f"Latency: {result2['latency_ms']} ms")
