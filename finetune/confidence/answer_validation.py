"""
Answer validation for review classification confidence.

Validates that a classification answer actually matches the semantic
sentiment of the review text. Unlike constraint_check (which only verifies
the answer is a valid category), this asks the model to independently
assess whether the review supports or contradicts the classification.
"""

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

    This is a two-part prompt:
    1. Independently assess the review's sentiment
    2. Compare with the given classification

    If the model independently arrives at a different sentiment, it should
    flag the classification as unsupported.

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
            "supported": False,
            "reason": "недостаточно данных для валидации — текст отзыва пуст",
            "latency_ms": 0
        }

    validation_prompt = (
        f"Ниже приведён отзыв покупателя и классификация, которая была ему присвоена.\n\n"
        f"Отзыв: \"{user_content}\"\n\n"
        f"Классификация: \"{answer}\"\n\n"
        f"1. Прочитайте отзыв и определите его реальный тональный характер "
        f"(позитивный, негативный, нейтральный, или крайне негативный).\n\n"
        f"2. Сравните реальный характер отзыва с присвоенной классификацией.\n\n"
        f"Отвечайте строго в формате:\n"
        f"ВЕРДИКТ: подтверждено\n"
        f"или\n"
        f"ВЕРДИКТ: противоречит\n\n"
        f"А потом кратко объясните, почему классификация совпадает или "
        f"не совпадает с реальным настроением отзыва. Укажите 2-3 ключевые "
        f"фразы из отзыва, которые поддерживают вашу оценку."
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

    # Parse VERDICT from response
    # Look for "ВЕРДИКТ:" line
    verdict = ""
    reason = raw_response
    if "ВЕРДИКТ:" in raw_response:
        lines = raw_response.split("\n")
        for line in lines:
            if "ВЕРДИКТ:" in line.strip():
                verdict = line.strip().replace("ВЕРДИКТ:", "").strip().lower()
                break
        # Reason is everything after the verdict line
        idx = raw_response.index("ВЕРДИКТ:")
        reason = raw_response[idx:].split("\n", 1)
        if len(reason) > 1:
            reason = reason[1].strip()
        else:
            reason = raw_response

    supported = "подтвержд" in verdict and "противореч" not in verdict

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
