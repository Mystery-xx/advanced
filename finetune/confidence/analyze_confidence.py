#!/usr/bin/env python3
"""
Analyze confidence evaluation metrics.

Reads confidence_results.json and computes:
- unsure_rate: % of samples with confidence_status != "HIGH"
- fail_rate: % of samples where constraint_passed == false
- latency_overhead: avg latency (confidence vs baseline)
- token_overhead: estimated token cost (len(text)/4 per token)

Compares with baseline if baseline_results.json exists.
"""

import json
import os
from pathlib import Path


def load_json(path: str) -> dict | None:
    """Load JSON file if exists, else return None."""
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_metrics(confidence_data: dict, baseline_data: dict | None = None) -> dict:
    """
    Compute confidence metrics.
    
    Args:
        confidence_data: Loaded confidence_results.json
        baseline_data: Optional loaded baseline_results.json
    
    Returns:
        dict with computed metrics
    """
    predictions = confidence_data.get('predictions', [])
    total_samples = len(predictions)
    
    if total_samples == 0:
        return {
            'total_samples': 0,
            'unsure_rate': 0.0,
            'fail_rate': 0.0,
            'avg_latency_ms': 0.0,
            'token_overhead': 0,
            'baseline_comparison': None
        }
    
    # unsure_rate: % of non-HIGH confidence
    unsure_count = sum(1 for p in predictions if p.get('confidence_status') != 'HIGH')
    unsure_rate = unsure_count / total_samples
    
    # fail_rate: % where constraint failed
    fail_count = sum(1 for p in predictions if not p.get('constraint_passed', True))
    fail_rate = fail_count / total_samples
    
    # avg latency
    total_latency = sum(p.get('latency_ms', 0) for p in predictions)
    avg_latency_ms = total_latency / total_samples
    
    # token_overhead: estimate tokens per sample (len(text)/4)
    total_tokens = 0
    for p in predictions:
        user_content_len = len(p.get('user_content', ''))
        explanation_len = len(p.get('explanation', ''))
        total_tokens += (user_content_len + explanation_len) // 4
    
    token_overhead = total_tokens
    
    # Baseline comparison
    baseline_comparison = None
    if baseline_data:
        baseline_predictions = baseline_data.get('predictions', [])
        baseline_accuracy = baseline_data.get('accuracy', 0.0)
        confidence_accuracy = confidence_data.get('accuracy', 0.0)
        
        # Compute baseline avg latency (if available)
        baseline_latencies = [p.get('latency_ms', 0) for p in baseline_predictions if 'latency_ms' in p]
        baseline_avg_latency = sum(baseline_latencies) / len(baseline_latencies) if baseline_latencies else None
        
        latency_overhead = None
        if baseline_avg_latency is not None:
            latency_overhead = avg_latency_ms - baseline_avg_latency
        
        baseline_comparison = {
            'baseline_accuracy': baseline_accuracy,
            'confidence_accuracy': confidence_accuracy,
            'accuracy_difference': confidence_accuracy - baseline_accuracy,
            'baseline_avg_latency_ms': baseline_avg_latency,
            'confidence_avg_latency_ms': avg_latency_ms,
            'latency_overhead_ms': latency_overhead,
            'baseline_samples': len(baseline_predictions),
            'confidence_samples': total_samples
        }
    
    return {
        'total_samples': total_samples,
        'unsure_rate': unsure_rate,
        'fail_rate': fail_rate,
        'avg_latency_ms': avg_latency_ms,
        'token_overhead': token_overhead,
        'baseline_comparison': baseline_comparison
    }


def print_summary(metrics: dict, confidence_data: dict) -> None:
    """Print console summary of metrics."""
    print("\n" + "=" * 60)
    print("Confidence Metrics Summary")
    print("=" * 60)
    
    total = metrics['total_samples']
    print(f"Total samples: {total}")
    
    unsure_count = int(metrics['unsure_rate'] * total)
    print(f"Unsure rate: {metrics['unsure_rate']*100:.1f}% ({unsure_count}/{total})")
    
    fail_count = int(metrics['fail_rate'] * total)
    print(f"Fail rate: {metrics['fail_rate']*100:.1f}% ({fail_count}/{total})")
    
    print(f"Avg latency: {metrics['avg_latency_ms']/1000:.2f}s per sample")
    
    avg_tokens = metrics['token_overhead'] / total if total > 0 else 0
    print(f"Token overhead: ~{int(avg_tokens)} tokens per sample")
    
    # Confidence distribution
    conf_stats = confidence_data.get('confidence_statistics', {}).get('counts', {})
    if conf_stats:
        print(f"\nConfidence distribution:")
        for status, count in sorted(conf_stats.items()):
            print(f"  {status}: {count} ({count/total*100:.1f}%)")
    
    # Baseline comparison
    baseline_comp = metrics.get('baseline_comparison')
    if baseline_comp:
        print(f"\nComparison with baseline:")
        print(f"  Baseline accuracy: {baseline_comp['baseline_accuracy']:.2f}")
        print(f"  Confidence accuracy: {baseline_comp['confidence_accuracy']:.2f}")
        print(f"  Accuracy difference: {baseline_comp['accuracy_difference']:+.2f}")
        
        if baseline_comp['latency_overhead_ms'] is not None:
            overhead_sec = baseline_comp['latency_overhead_ms'] / 1000
            print(f"  Latency overhead: {overhead_sec:+.2f}s per sample")
        else:
            print(f"  Latency overhead: N/A (baseline has no latency data)")
    
    print("=" * 60 + "\n")


def main():
    """Main entry point."""
    # Paths
    script_dir = Path(__file__).parent
    confidence_path = script_dir / 'confidence_results.json'
    baseline_path = script_dir.parent / 'baseline' / 'baseline_results.json'
    output_path = script_dir / 'confidence_metrics.json'
    
    # Load data
    print(f"Loading confidence results from: {confidence_path}")
    confidence_data = load_json(str(confidence_path))
    
    if not confidence_data:
        print(f"ERROR: Cannot load {confidence_path}")
        return 1
    
    print(f"Loading baseline results from: {baseline_path}")
    baseline_data = load_json(str(baseline_path))
    
    if not baseline_data:
        print(f"WARNING: Baseline not found at {baseline_path}, skipping comparison")
    
    # Compute metrics
    metrics = compute_metrics(confidence_data, baseline_data)
    
    # Print summary
    print_summary(metrics, confidence_data)
    
    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    print(f"Metrics saved to: {output_path}")
    return 0


if __name__ == '__main__':
    exit(main())