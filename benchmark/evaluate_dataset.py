"""Empirical Evaluation & Calibration Analysis on 20 Diverse PR Workloads.

Measures:
1. Classification Accuracy, Precision, Recall, and F1 per category
2. Expected Calibration Error (ECE) comparing confidence bins vs true accuracy
3. Latency distribution (P50, P90, P99)
4. Escalation effectiveness for ambiguous high-churn PRs

Usage:
    python benchmark/evaluate_dataset.py
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from typing import Dict, List

# Ensure parent directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from reviewpilot.agent import ReviewPilotAgent
from reviewpilot.decider_client import DeciderClient
from reviewpilot.models import PRPayload, RoutingAction


def run_statistical_evaluation():
    dataset_path = Path(__file__).parent.parent / "examples" / "evaluation_dataset.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print("=" * 80)
    print(" 🔬 ReviewPilot AI: Empirical Calibration & Accuracy Evaluation")
    print("    Dataset: 20 Real-World Pull Requests (Docs, Security, Breaking, Apps)")
    print("=" * 80)

    decider_client = DeciderClient()
    agent = ReviewPilotAgent(confidence_threshold=0.80, decider_client=decider_client)

    correct_predictions = 0
    total = len(dataset)
    latencies: List[float] = []

    # Category counters for metrics
    categories = ["auto_approve", "security_escalation", "breaking_change", "standard_review"]
    tp = {c: 0 for c in categories}
    fp = {c: 0 for c in categories}
    fn = {c: 0 for c in categories}

    # Calibration buckets (0.5-0.6, 0.6-0.7, 0.7-0.8, 0.8-0.9, 0.9-1.0)
    bins = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    bin_counts = [0] * (len(bins) - 1)
    bin_correct = [0] * (len(bins) - 1)
    bin_conf_sums = [0.0] * (len(bins) - 1)

    print(f"{'PR ID':<7} | {'True Intent':<20} | {'Decider Choice':<20} | {'Conf':<6} | {'Action':<15} | {'Latency'}")
    print("-" * 80)

    for item in dataset:
        true_cat = item["true_category"]
        pr = PRPayload(
            id=item["id"],
            title=item["title"],
            author=item["author"],
            files_changed=item["files_changed"],
            additions=item["additions"],
            deletions=item["deletions"],
            diff_content=item["diff_content"],
        )

        res = agent.review_pull_request(pr)
        pred_cat = res.verdict.category
        conf = res.verdict.confidence
        lat = res.verdict.decision_latency_ms
        latencies.append(lat)

        is_match = False
        if true_cat == "ambiguous_escalation":
            # Success means it escalated to human lead review!
            is_match = res.verdict.escalated_to_human
        else:
            is_match = (pred_cat == true_cat)

        if is_match:
            correct_predictions += 1
            if pred_cat in tp:
                tp[pred_cat] += 1
        else:
            if pred_cat in fp:
                fp[pred_cat] += 1
            if true_cat in fn:
                fn[true_cat] += 1

        # Calibration binning
        for b_idx in range(len(bins) - 1):
            if bins[b_idx] <= conf <= bins[b_idx + 1]:
                bin_counts[b_idx] += 1
                bin_conf_sums[b_idx] += conf
                if is_match:
                    bin_correct[b_idx] += 1
                break

        print(f"{pr.id:<7} | {true_cat:<20} | {pred_cat:<20} | {conf * 100:.0f}%  | {res.verdict.action.value:<15} | {lat:.1f}ms")

    accuracy = (correct_predictions / total) * 100
    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p90 = latencies[int(len(latencies) * 0.9)]
    p99 = latencies[-1]

    # Calculate Expected Calibration Error (ECE)
    ece = 0.0
    for b_idx in range(len(bins) - 1):
        if bin_counts[b_idx] > 0:
            bin_acc = bin_correct[b_idx] / bin_counts[b_idx]
            bin_avg_conf = bin_conf_sums[b_idx] / bin_counts[b_idx]
            bin_weight = bin_counts[b_idx] / total
            ece += bin_weight * abs(bin_acc - bin_avg_conf)

    print("=" * 80)
    print(" 📊 EMPIRICAL PERFORMANCE & CALIBRATION METRICS")
    print("=" * 80)
    print(f"  • Overall Routing Accuracy    : {accuracy:.1f}% ({correct_predictions}/{total} pull requests)")
    print(f"  • Expected Calibration Error  : {ece * 100:.2f}% (ECE < 5% signifies calibrated reliability)")
    print(f"  • Median Latency (P50)        : {p50:.1f} ms")
    print(f"  • 90th Percentile (P90)       : {p90:.1f} ms")
    print(f"  • 99th Percentile (P99)       : {p99:.1f} ms")
    print("-" * 80)
    print(f"{'Category':<22} | {'Precision':<10} | {'Recall':<10} | {'F1-Score'}")
    print("-" * 80)
    for c in categories:
        precision = tp[c] / (tp[c] + fp[c]) if (tp[c] + fp[c]) > 0 else 0.0
        recall = tp[c] / (tp[c] + fn[c]) if (tp[c] + fn[c]) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        print(f"{c:<22} | {precision * 100:<9.1f}% | {recall * 100:<9.1f}% | {f1:.3f}")
    print("=" * 80)


if __name__ == "__main__":
    run_statistical_evaluation()
