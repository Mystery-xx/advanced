#!/usr/bin/env python3
"""Training script for TF-IDF + LogisticRegression micro-model.

Loads a JSONL dataset in OpenAI messages format, extracts (text, label) pairs,
trains a TF-IDF vectorizer + LogisticRegression classifier, and saves the
pipeline to finetune/micromodel/models/.
"""

import json
import os
import sys
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline

# Paths
HERE = Path(__file__).resolve().parent
DATASET_PATH = HERE.parent / "dataset" / "train.jsonl"
MODELS_DIR = HERE / "models"

# Constants
MAX_FEATURES = 500
NGRAM_RANGE = (1, 2)
MIN_DF = 2
CLASSIFIER_MAX_ITER = 1000


def load_dataset(path: Path) -> list[dict]:
    """Load JSONL dataset from *path*.

    Args:
        path: Path to the JSONL file.

    Returns:
        List of parsed JSON objects (one per line).

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If a line contains invalid JSON.
    """
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    records: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                print(
                    f"Warning: skipping line {line_no} — invalid JSON: {exc}",
                    file=sys.stderr,
                )
    return records


def extract_text_label(records: list[dict]) -> tuple[list[str], list[str]]:
    """Extract (user_text, assistant_label) from OpenAI messages format.

    Args:
        records: List of parsed JSONL objects, each with a ``messages`` key.

    Returns:
        Tuple of (texts, labels) where ``texts[i]`` is the user message content
        and ``labels[i]`` is the assistant message content.
    """
    texts: list[str] = []
    labels: list[str] = []

    for idx, record in enumerate(records):
        messages = record.get("messages", [])
        user_content = None
        assistant_content = None

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                user_content = content
            elif role == "assistant":
                assistant_content = content

        if user_content is None or assistant_content is None:
            print(
                f"Warning: record {idx} missing user/assistant message — skipping",
                file=sys.stderr,
            )
            continue

        texts.append(user_content)
        labels.append(assistant_content)

    return texts, labels


def print_class_distribution(labels: list[str], name: str = "Dataset") -> None:
    """Print class distribution sorted alphabetically.

    Args:
        labels: List of class labels.
        name: Human-readable name for the dataset (printed in header).
    """
    from collections import Counter

    counts = Counter(labels)
    print(f"\n=== {name} class distribution ===")
    for cls in sorted(counts):
        print(f"  {cls}: {counts[cls]}")
    print(f"  Total: {len(labels)}")
    print()


def train_and_save(texts: list[str], labels: list[str]) -> None:
    """Train TF-IDF → LogisticRegression pipeline and save artifacts.

    Saves three files under ``models/``:
      - vectorizer.pkl (TfidfVectorizer)
      - classifier.pkl (LogisticRegression)
      - label_encoder.pkl (LabelEncoder)

    Args:
        texts: Input text samples.
        labels: Corresponding class labels.
    """
    # Encode string labels → integer labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)

    # TF-IDF vectoriser
    vectorizer = TfidfVectorizer(
        max_features=MAX_FEATURES,
        ngram_range=NGRAM_RANGE,
        min_df=MIN_DF,
    )
    X = vectorizer.fit_transform(texts)

    # Classifier
    classifier = LogisticRegression(
        max_iter=CLASSIFIER_MAX_ITER,
        class_weight="balanced",
    )
    classifier.fit(X, y)

    # Predict on training set
    y_pred = classifier.predict(X)
    acc = accuracy_score(y, y_pred)
    print(f"Training accuracy: {acc:.4f} ({acc * 100:.1f}%)\n")

    # Serialise models
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(vectorizer, MODELS_DIR / "vectorizer.pkl")
    joblib.dump(classifier, MODELS_DIR / "classifier.pkl")
    joblib.dump(label_encoder, MODELS_DIR / "label_encoder.pkl")

    print(f"Models saved to {MODELS_DIR}/")
    print(f"  - vectorizer.pkl   (TF-IDF: {X.shape[1]} features)")
    print(f"  - classifier.pkl   (LogisticRegression: {classifier.coef_.shape})")
    print(f"  - label_encoder.pkl (classes: {list(label_encoder.classes_)})\n")


def main() -> None:
    """Main entry point: load, extract, train, save."""
    print("=" * 60)
    print("Micro-Model Training — TF-IDF + LogisticRegression")
    print("=" * 60)

    # Step 1: load dataset
    print(f"\n[1/4] Loading dataset: {DATASET_PATH}")
    try:
        records = load_dataset(DATASET_PATH)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"  Loaded {len(records)} records")

    # Step 2: extract text + labels
    print("[2/4] Extracting text/label pairs")
    texts, labels = extract_text_label(records)
    print(f"  Extracted {len(texts)} samples")

    # Step 3: print distribution
    print("[3/4] Class distribution")
    print_class_distribution(labels, "Train")

    # Step 4: train and save
    print("[4/4] Training model")
    train_and_save(texts, labels)

    print("Done.")


if __name__ == "__main__":
    main()
