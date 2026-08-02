"""
MicroModel Router — Confidence-based routing with LLM fallback.

This module provides a lightweight ML-based router that classifies queries
using a TF-IDF + LogisticRegression micro-model. When the model's confidence
falls below a configurable threshold, it falls back to an LLM (via Ollama)
for more reliable classification.

Architecture::

    Query -> TF-IDF -> LogisticRegression -> predict_proba() -> max() = confidence
                                                   |
                                            confidence >= threshold?
                                                   |
                              +--------------------+--------------------+
                              |                                         |
                             YES                                        NO
                              |                                         |
                      Return prediction                       Fallback to LLM
                      (<10ms)                                 (~1500ms)

Usage:
    >>> from micromodel_router import MicroModelRouter
    >>> router = MicroModelRouter()
    >>> result = router.route("Отличная тачка для дачи")
    >>> print(result.model_used)
    'micromodel'
    >>> print(result.answer)
    'позитивный'
"""

from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import joblib
import numpy as np
import requests

from finetune.confidence.constraint_check import LABELED_CATEGORIES, constraint_check

# ─── Constants ────────────────────────────────────────────────

DEFAULT_CONFIDENCE_THRESHOLD: Final[float] = 0.30
DEFAULT_LLM_MODEL: Final[str] = "qwen3:14b"
DEFAULT_OLLAMA_URL: Final[str] = "http://localhost:11434"

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL_DIR: Final[Path] = HERE / "models"

DEFAULT_MODEL_PATHS: Final[dict[str, str]] = {
    "vectorizer": str(DEFAULT_MODEL_DIR / "vectorizer.pkl"),
    "classifier": str(DEFAULT_MODEL_DIR / "classifier.pkl"),
    "label_encoder": str(DEFAULT_MODEL_DIR / "label_encoder.pkl"),
}

# ─── Data models ──────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class MicroModelConfig:
    """Configuration for the micro-model router.

    Attributes:
        confidence_threshold: Minimum confidence (max probability) required to
            accept the micro-model's prediction without falling back to the LLM.
            Default 0.30 is tuned for small datasets (~80 samples); increase to
            0.50+ only with larger training data (500+ samples).
        llm_model: Ollama model name used for fallback classification.
        ollama_url: Base URL of the Ollama API server.
        model_paths: Dictionary mapping model component keys (``vectorizer``,
            ``classifier``, ``label_encoder``) to filesystem paths of saved
            ``.pkl`` files.
    """

    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    llm_model: str = DEFAULT_LLM_MODEL
    ollama_url: str = DEFAULT_OLLAMA_URL
    model_paths: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_MODEL_PATHS))


@dataclass(frozen=True, slots=True)
class RouterResult:
    """Result from routing a single request through the micro-model or LLM.

    Attributes:
        answer: The final classification answer.
        model_used: Which model produced the answer (``"micromodel"`` or
            the LLM model name).
        confidence_status: Human-readable confidence label — ``"HIGH"``,
            ``"LOW"``, or ``"ERROR"``.
        explanation: Any additional explanation from the routing process
            (e.g. probability values or error messages).
        constraint_passed: Whether the answer passed basic constraint checks.
        escalated: Whether the request was escalated to the LLM fallback.
        cheap_answer: The micro-model's raw prediction (empty if not used).
        cheap_confidence: The micro-model's confidence score as a formatted
            string, or ``"ERROR"`` if inference failed.
        latency_ms: Total routing latency in milliseconds.
        cost_units: Relative cost units spent (1 for micro-model, 3 for LLM).
    """

    answer: str
    model_used: str
    confidence_status: str  # "HIGH", "LOW", or "ERROR"
    explanation: str
    constraint_passed: bool
    escalated: bool
    cheap_answer: str
    cheap_confidence: str
    latency_ms: int
    cost_units: int


# ─── Core logic ───────────────────────────────────────────────


# Lazy-loaded globals for the TF-IDF pipeline (loaded once, reused across calls).
_vectorizer = None
_classifier = None
_label_encoder = None


def _load_models(config: MicroModelConfig) -> None:
    """Load the TF-IDF vectorizer, classifier, and label encoder from disk.

    This function populates the module-level globals ``_vectorizer``,
    ``_classifier``, and ``_label_encoder``.  It is safe to call multiple
    times — already-loaded models are not reloaded.

    Args:
        config: Configuration containing model file paths.

    Raises:
        FileNotFoundError: If any model file is missing.
        Exception: Any error raised by ``joblib.load``.
    """
    global _vectorizer, _classifier, _label_encoder  # noqa: PLW0603

    paths = config.model_paths

    if _vectorizer is None:
        v_path = paths.get("vectorizer", str(DEFAULT_MODEL_DIR / "vectorizer.pkl"))
        if not os.path.isfile(v_path):
            raise FileNotFoundError(f"Vectorizer not found: {v_path}")
        _vectorizer = joblib.load(v_path)

    if _classifier is None:
        c_path = paths.get("classifier", str(DEFAULT_MODEL_DIR / "classifier.pkl"))
        if not os.path.isfile(c_path):
            raise FileNotFoundError(f"Classifier not found: {c_path}")
        _classifier = joblib.load(c_path)

    if _label_encoder is None:
        le_path = paths.get("label_encoder", str(DEFAULT_MODEL_DIR / "label_encoder.pkl"))
        if not os.path.isfile(le_path):
            raise FileNotFoundError(f"Label encoder not found: {le_path}")
        _label_encoder = joblib.load(le_path)


def get_confidence(text: str, config: MicroModelConfig | None = None) -> dict:
    """Compute the micro-model's confidence for a given text.

    The function:
    1. Loads the TF-IDF vectorizer, classifier, and label encoder (if not
       already loaded).
    2. Transforms ``text`` into the TF-IDF feature space.
    3. Calls ``predict_proba`` to obtain class probabilities.
    4. Returns the maximum probability as the confidence score.

    Args:
        text: The input query string to classify.
        config: MicroModelConfig (defaults to ``MicroModelConfig()``).

    Returns:
        Dictionary with keys:

        - ``"prediction"`` (str): The predicted class label.
        - ``"confidence"`` (float): Maximum probability score (0.0 – 1.0).
        - ``"probabilities"`` (dict): Per-class probability mapping.

    Raises:
        Exception: Propagates any model loading or inference error.
    """
    if config is None:
        config = MicroModelConfig()

    _load_models(config)

    # TF-IDF transform
    X = _vectorizer.transform([text])  # noqa: N806

    # Predict probabilities
    proba = _classifier.predict_proba(X)[0]  # shape: (n_classes,)

    # Predicted class index
    pred_idx = int(np.argmax(proba))
    confidence = float(proba[pred_idx])

    # Decode label
    prediction = _label_encoder.inverse_transform([pred_idx])[0]

    # Build per-class probabilities
    classes = _label_encoder.classes_
    probabilities: dict[str, float] = {
        str(classes[i]): float(proba[i]) for i in range(len(classes))
    }

    return {
        "prediction": prediction,
        "confidence": confidence,
        "probabilities": probabilities,
    }


def fallback_to_llm(text: str, config: MicroModelConfig | None = None) -> dict:
    """Classify text using the LLM (Ollama) as a fallback.

    Sends the text to the configured Ollama model for sentiment classification
    and returns the raw answer.

    Args:
        text: The input query string to classify.
        config: MicroModelConfig (defaults to ``MicroModelConfig()``).

    Returns:
        Dictionary with keys:

        - ``"answer"`` (str): The LLM's classification answer.
        - ``"latency_ms"`` (int): Time taken for the LLM call.

    Raises:
        requests.ConnectionError: If Ollama is unreachable.
        requests.HTTPError: If Ollama returns a non-2xx response.
    """
    if config is None:
        config = MicroModelConfig()

    system_prompt = (
        "Ты — классификатор тональности отзывов. Определи категорию отзыва.\n"
        "Категории: крайне негативный, негативный, нейтральный, позитивный.\n"
        "Отвечай только названием категории."
    )

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "temperature": 0.0,
        "stream": False,
    }

    start = time.perf_counter()
    response = requests.post(
        f"{config.ollama_url}/api/chat",
        json=payload,
        timeout=300,
    )
    response.raise_for_status()
    latency_ms = int((time.perf_counter() - start) * 1000)

    data = response.json()
    answer = data.get("message", {}).get("content", "").strip()

    return {"answer": answer, "latency_ms": latency_ms}


def route_with_fallback(text: str, config: MicroModelConfig | None = None) -> RouterResult:
    """Route a query through the micro-model with LLM fallback.

    The routing logic:

    1. Attempts micro-model inference via ``get_confidence()``.
    2. If confidence >= ``config.confidence_threshold`` → return micro-model
       prediction directly.
    3. If confidence < threshold or micro-model errors → fall back to LLM.
    4. If LLM also fails → return an ``ERROR`` status result.

    Args:
        text: The input query string to classify.
        config: MicroModelConfig (defaults to ``MicroModelConfig()``).

    Returns:
        RouterResult with routing metadata.

    Example:
        >>> router = MicroModelRouter()
        >>> result = router.route("Отличная тачка для дачи")
        >>> result.confidence_status
        'HIGH'
    """
    if config is None:
        config = MicroModelConfig()

    start_time = time.perf_counter()

    # ── Step 1: Micro-model inference ──────────────────────────
    micromodel_succeeded = False
    cheap_answer = ""
    cheap_confidence_str = ""
    confidence_score = 0.0
    constraint_passed = True

    try:
        confidence_result = get_confidence(text, config)
        prediction = confidence_result["prediction"]
        confidence_score = confidence_result["confidence"]
        micromodel_succeeded = True

        cheap_answer = prediction
        cheap_confidence_str = f"{confidence_score:.4f}"

        constraint_result = constraint_check(prediction)
        constraint_passed = constraint_result["passed"]
        if not constraint_passed:
            explanation = (
                f"Micro-model prediction '{prediction}' failed constraint check: "
                f"not in {constraint_result['expected']}"
            )
    except Exception as exc:
        cheap_answer = ""
        cheap_confidence_str = "ERROR"
        explanation = f"Micro-model error: {exc}"
        constraint_passed = False
        # Will continue to fallback below

    # ── Step 2: Decide: keep micro-model prediction or fallback ─
    keep_micromodel = (
        micromodel_succeeded
        and confidence_score >= config.confidence_threshold
        and constraint_passed
    )
    if keep_micromodel:
        # HIGH confidence + constraint passed — return micro-model answer directly
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return RouterResult(
            answer=prediction,
            model_used="micromodel",
            confidence_status="HIGH",
            explanation=(
                f"Micro-model confidence {confidence_score:.4f} "
                f">= threshold {config.confidence_threshold}"
            ),
            constraint_passed=True,
            escalated=False,
            cheap_answer=prediction,
            cheap_confidence=cheap_confidence_str,
            latency_ms=elapsed,
            cost_units=1,
        )

    # ── Step 3: Fallback to LLM ────────────────────────────────
    escalated = micromodel_succeeded  # True = low confidence/constraint fail; False = error
    explanation_parts: list[str] = []

    if micromodel_succeeded:
        if not constraint_passed:
            explanation_parts.append(explanation)
        else:
            explanation_parts.append(
                f"Micro-model confidence {confidence_score:.4f} "
                f"< threshold {config.confidence_threshold}"
            )
    else:
        explanation_parts.append(explanation)  # from except block above

    try:
        llm_result = fallback_to_llm(text, config)
        llm_answer = llm_result["answer"]
        llm_latency = llm_result["latency_ms"]
        model_used = config.llm_model
        explanation_parts.append(f"Fallback to {config.llm_model} succeeded.")
    except requests.ConnectionError as exc:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return RouterResult(
            answer="ERROR",
            model_used="",
            confidence_status="ERROR",
            explanation=(
                f"{' / '.join(explanation_parts)} "
                f"LLM fallback failed — cannot connect to Ollama at {config.ollama_url}: {exc}"
            ),
            constraint_passed=False,
            escalated=escalated,
            cheap_answer=cheap_answer,
            cheap_confidence=cheap_confidence_str,
            latency_ms=elapsed,
            cost_units=0,
        )
    except requests.HTTPError as exc:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return RouterResult(
            answer="ERROR",
            model_used="",
            confidence_status="ERROR",
            explanation=(
                f"{' / '.join(explanation_parts)} "
                f"LLM fallback failed — Ollama HTTP error: {exc}"
            ),
            constraint_passed=False,
            escalated=escalated,
            cheap_answer=cheap_answer,
            cheap_confidence=cheap_confidence_str,
            latency_ms=elapsed,
            cost_units=0,
        )
    except Exception as exc:
        elapsed = int((time.perf_counter() - start_time) * 1000)
        return RouterResult(
            answer="ERROR",
            model_used="",
            confidence_status="ERROR",
            explanation=(
                f"{' / '.join(explanation_parts)} "
                f"LLM fallback failed unexpectedly: {exc}"
            ),
            constraint_passed=False,
            escalated=escalated,
            cheap_answer=cheap_answer,
            cheap_confidence=cheap_confidence_str,
            latency_ms=elapsed,
            cost_units=0,
        )

    elapsed = int((time.perf_counter() - start_time) * 1000)

    llm_constraint_result = constraint_check(llm_answer)
    llm_constraint_passed = llm_constraint_result["passed"]

    return RouterResult(
        answer=llm_answer,
        model_used=model_used,
        confidence_status="LOW",
        explanation=" / ".join(explanation_parts),
        constraint_passed=llm_constraint_passed,
        escalated=True,
        cheap_answer=cheap_answer,
        cheap_confidence=cheap_confidence_str,
        latency_ms=elapsed,
        cost_units=3,
    )


# ─── Convenience class ────────────────────────────────────────


class MicroModelRouter:
    """Convenience wrapper around the micro-model routing functions.

    Encapsulates a ``MicroModelConfig`` and provides a single-method
    interface for routing queries.

    Args:
        config: MicroModelConfig (defaults to ``MicroModelConfig()``).

    Example:
        >>> router = MicroModelRouter(confidence_threshold=0.8)
        >>> result = router.route("Нормальный товар, но могло быть лучше")
        >>> result.model_used
        'micromodel'
    """

    def __init__(self, **kwargs: object) -> None:
        self.config = MicroModelConfig(**kwargs)  # type: ignore[arg-type]

    def route(self, text: str) -> RouterResult:
        """Route a single query through the micro-model with fallback.

        Args:
            text: The input query string to classify.

        Returns:
            RouterResult with routing metadata.
        """
        return route_with_fallback(text, self.config)


# ─── CLI ────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Micro-model router — confidence-based routing with LLM fallback.\n\n"
        "Classifies queries using a TF-IDF + LogisticRegression micro-model. "
        "When confidence falls below the threshold, falls back to an LLM via Ollama.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s                                         # defaults\n"
            "  %(prog)s --confidence-threshold 0.65             # lower bar\n"
            "  %(prog)s --llm-model qwen2.5:14b                 # different LLM\n"
            "  %(prog)s --ollama-url http://remote:11434        # remote Ollama\n"
        ),
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=DEFAULT_CONFIDENCE_THRESHOLD,
        help=f"Minimum confidence to accept micro-model prediction (default: {DEFAULT_CONFIDENCE_THRESHOLD})",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default=DEFAULT_LLM_MODEL,
        help=f"Ollama model for fallback classification (default: {DEFAULT_LLM_MODEL})",
    )
    parser.add_argument(
        "--ollama-url",
        type=str,
        default=DEFAULT_OLLAMA_URL,
        help=f"Ollama API base URL (default: {DEFAULT_OLLAMA_URL})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config = MicroModelConfig(
        confidence_threshold=args.confidence_threshold,
        llm_model=args.llm_model,
        ollama_url=args.ollama_url,
    )

    print(f"MicroModel Router")
    print(f"  confidence_threshold={config.confidence_threshold}")
    print(f"  llm_model={config.llm_model}")
    print(f"  ollama_url={config.ollama_url}")
    print()

    sample = "Отличная тачка для дачи"
    print(f"Routing sample: {sample!r}")
    print()

    router = MicroModelRouter(config=config)
    result = router.route(sample)

    print(f"Answer:     {result.answer}")
    print(f"Model used: {result.model_used}")
    print(f"Confidence: {result.confidence_status}")
    print(f"Latency:    {result.latency_ms}ms")
    print(f"Cost units: {result.cost_units}")


if __name__ == "__main__":
    main()
