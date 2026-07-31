"""
Self-check confidence evaluator for review classification.

This module implements a self-check approach where the model explains its own answer.
The explanation can be used to assess confidence in the classification.
"""

import requests
import time

OLLAMA_URL = "http://localhost:11434"


def self_check(user_content: str, answer: str, model: str = "qwen3:14b") -> dict:
    """
    Send a self-check request to Ollama asking the model to explain its answer.
    
    Args:
        user_content: The original user review text that was classified
        answer: The model's classification answer (e.g., "позитивный")
        model: Ollama model name to use (default: "qwen3:14b")
    
    Returns:
        dict with keys:
            - explanation (str): The model's explanation for why it chose this answer
            - latency_ms (int): Time taken for the API call in milliseconds
    
    Example:
        >>> result = self_check(
        ...     user_content="Отличная тачка для дачи",
        ...     answer="позитивный",
        ...     model="qwen3:14b"
        ... )
        >>> print(result["explanation"])
        "Модель выбрала категорию 'позитивный', потому что..."
        >>> print(result["latency_ms"])
        1234
    """
    # Handle edge case: empty or whitespace-only user content
    if not user_content or not user_content.strip():
        return {
            "explanation": "недостаточно данных для анализа — текст отзыва пуст",
            "latency_ms": 0
        }
    
    # Build self-check prompt asking model to explain its classification
    explanation_prompt = (
        f"Пользователь оставил отзыв: \"{user_content}\"\n\n"
        f"Вы классифицировали этот отзыв как \"{answer}\".\n\n"
        f"Объясните, почему вы выбрали именно эту категорию? "
        f"Какие слова или фразы в отзыве повлияли на ваше решение?"
    )
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": explanation_prompt},
        ],
        "temperature": 0.0,
        "stream": False,
    }
    
    start_time = time.perf_counter()
    
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()
    
    end_time = time.perf_counter()
    latency_ms = int((end_time - start_time) * 1000)
    
    explanation = data.get("message", {}).get("content", "").strip()
    
    return {
        "explanation": explanation,
        "latency_ms": latency_ms
    }


if __name__ == "__main__":
    # Demo usage
    import json
    
    # Test with example #4 from eval.jsonl
    example_4_content = (
        "Отличная тачка для дачи – крепкая, удобная и очень выносливая. "
        "Брал для дачи: возил землю, камни, мусор – справляется на ура. "
        "Усиленная рама не гнётся даже под 200 кг, удобные прорезиненные ручки. "
        "Собирается за 15 минут, стоит устойчиво. За эти деньги – один из лучших вариантов."
    )
    
    print("Testing self_check with example #4 (позитивный отзыв):")
    print("=" * 60)
    result = self_check(example_4_content, "позитивный")
    print(f"Explanation: {result['explanation']}")
    print(f"Latency: {result['latency_ms']} ms")
    print()
    
    # Test edge case: empty text
    print("Testing self_check with empty text:")
    print("=" * 60)
    result_empty = self_check("", "позитивный")
    print(f"Explanation: {result_empty['explanation']}")
    print(f"Latency: {result_empty['latency_ms']} ms")