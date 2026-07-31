#!/usr/bin/env python3
"""
validate.py — Validate the sentiment classification dataset.

Checks:
  - JSONL format (valid JSON on each line)
  - Structure: 3 messages per example (system, user, assistant)
  - Categories: only valid category names in assistant output
  - Word count: all reviews >= 20 words
  - Counts: train=80, eval=20
  - Balance: category distribution

Usage:
  python3 validate.py [dataset_dir]
"""

import json
import sys
import os
from collections import Counter

DATASET_DIR = os.environ.get(
    "DATASET_DIR", "/mnt/f/git/advanced/test-project/finetune/dataset"
)

CATEGORIES = {"крайне негативный", "негативный", "нейтральный", "позитивный"}
MIN_WORDS = 20
EXPECTED = {"train.jsonl": 80, "eval.jsonl": 20}


def validate_jsonl(path, expected_count):
    """Validate a JSONL file. Returns (errors, stats)."""
    errors = []
    stats = {
        "total": 0,
        "categories": Counter(),
        "short_reviews": 0,
        "bad_json": 0,
        "bad_structure": 0,
    }

    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            stats["total"] += 1

            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"L{line_num}: invalid JSON — {e}")
                stats["bad_json"] += 1
                continue

            msgs = entry.get("messages", [])
            if not isinstance(msgs, list) or len(msgs) != 3:
                errors.append(f"L{line_num}: expected 3 messages, got {len(msgs)}")
                stats["bad_structure"] += 1
                continue

            roles = [m.get("role") for m in msgs]
            if roles != ["system", "user", "assistant"]:
                errors.append(f"L{line_num}: wrong roles — {roles}")
                stats["bad_structure"] += 1

            user_content = msgs[1].get("content", "")
            assistant_content = msgs[2].get("content", "")

            if not user_content.strip():
                errors.append(f"L{line_num}: empty user content")
            if not assistant_content.strip():
                errors.append(f"L{line_num}: empty assistant content")

            if assistant_content not in CATEGORIES:
                errors.append(f"L{line_num}: invalid category '{assistant_content}'")

            stats["categories"][assistant_content] += 1

            wc = len(user_content.split())
            if wc < MIN_WORDS:
                errors.append(f"L{line_num}: too short ({wc} words, min={MIN_WORDS})")
                stats["short_reviews"] += 1

    if stats["total"] != expected_count:
        errors.append(f"count mismatch: {stats['total']} vs {expected_count}")

    return errors, stats


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else DATASET_DIR

    if not os.path.isdir(d):
        print(f"ERROR: not a directory: {d}", file=sys.stderr)
        return 1

    all_good = True

    for fname, expected in EXPECTED.items():
        fpath = os.path.join(d, fname)
        print(f"\n{'='*60}")
        print(f"  {fname}")
        print(f"{'='*60}")

        if not os.path.isfile(fpath):
            print(f"  ❌ File not found: {fpath}")
            all_good = False
            continue

        errs, stats = validate_jsonl(fpath, expected)

        print(f"  Total: {stats['total']} (expected {expected})")
        print(f"  Categories:")
        for cat in sorted(CATEGORIES):
            print(f"    {cat}: {stats['categories'][cat]}")
        print(f"  Bad JSON:      {stats['bad_json']}")
        print(f"  Bad structure: {stats['bad_structure']}")
        print(f"  Short reviews: {stats['short_reviews']}")

        if errs:
            all_good = False
            print(f"\n  ❌ {len(errs)} errors:")
            for e in errs[:10]:
                print(f"    - {e}")
            if len(errs) > 10:
                print(f"    ... +{len(errs) - 10} more")
        else:
            print(f"  ✅ All checks passed")

    print(f"\n{'='*60}")
    if all_good:
        print("✅ ALL VALIDATIONS PASSED")
        return 0
    else:
        print("❌ VALIDATION FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
