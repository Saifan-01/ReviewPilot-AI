"""ReviewPilot AI - Command Line Interface.

Usage:
    python cli.py --sample auth_security
    python cli.py --sample doc_typo
    python cli.py --sample ambiguous
    python cli.py --file examples/01_doc_typo_fix.json --threshold 0.85
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from reviewpilot.agent import ReviewPilotAgent
from reviewpilot.decider_client import DeciderClient
from reviewpilot.models import PRPayload, RoutingAction, TriageCategory

SAMPLE_MAPPING = {
    "doc_typo": "01_doc_typo_fix.json",
    "auth_security": "02_feature_auth_oauth.json",
    "db_breaking": "03_db_migration.json",
    "ambiguous": "04_ambiguous_refactor.json",
    "standard_bugfix": "05_standard_bugfix.json",
}


def load_pr_from_file(file_path: str) -> PRPayload:
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return PRPayload(**data)


def main():
    parser = argparse.ArgumentParser(
        description="ReviewPilot AI: Strands Decider 2B + Amazon Bedrock Code Review & Gatekeeper CLI"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--file", "-f", type=str, help="Path to pull request JSON file"
    )
    group.add_argument(
        "--sample", "-s", choices=list(SAMPLE_MAPPING.keys()),
        help="Select a built-in sample PR to evaluate"
    )
    parser.add_argument(
        "--threshold", "-t", type=float, default=0.80,
        help="Calibrated confidence safety threshold (default: 0.80)"
    )
    parser.add_argument(
        "--decider-url", type=str, default="http://127.0.0.1:8000",
        help="Strands Decider 2B local server endpoint (default: http://127.0.0.1:8000)"
    )

    args = parser.parse_args()

    # Load PR
    if args.sample:
        example_file = Path(__file__).parent / "examples" / SAMPLE_MAPPING[args.sample]
        pr = load_pr_from_file(str(example_file))
    else:
        pr = load_pr_from_file(args.file)

    print("=" * 70)
    print(" 🚀 ReviewPilot AI: Code Review Gatekeeper")
    print("    Strands Decider 2B (#policy) + Amazon Bedrock (System Two)")
    print("=" * 70)
    print(f"Evaluating Pull Request: #{pr.id} - {pr.title}")
    print(f"Author: {pr.author} | Target: {pr.target_branch} | Files: {len(pr.files_changed)}")
    print("-" * 70)

    # Initialize agent
    decider = DeciderClient(base_url=args.decider_url)
    agent = ReviewPilotAgent(
        confidence_threshold=args.threshold,
        decider_client=decider,
    )

    result = agent.review_pull_request(pr)
    verdict = result.verdict

    # Pretty-print results
    print(f"\n[Strands Decider 2B Decision]")
    print(f"  • Category Selected  : {verdict.category}")
    print(f"  • Calibrated Conf.   : {verdict.confidence * 100:.1f}% (Threshold: {verdict.threshold * 100:.1f}%)")
    print(f"  • Decision Latency   : {verdict.decision_latency_ms:.1f} ms")
    print(f"  • Enforced Action    : {verdict.action.value.upper()}")

    if verdict.escalated_to_human:
        print(f"\n[🚨 HUMAN ESCALATION REQUIRED]")
        print(f"  Reason: {verdict.rationale}")
        print(f"  Automated merge and tool calls blocked.")
        sys.exit(1)

    print(f"\n[Amazon Bedrock Execution]")
    print(f"  • Model Provider     : {result.generative_model_used}")
    print(f"  • Generative Latency : {result.generative_latency_ms:.1f} ms")
    print(f"  • Est. Cost (USD)    : ${result.estimated_cost_usd:.4f}")

    if result.findings:
        print(f"\n[Findings ({len(result.findings)})]")
        for f in result.findings:
            icon = "🔴" if f.severity == "critical" else ("🟡" if f.severity == "warning" else "🔵")
            print(f"  {icon} [{f.severity.upper()}] {f.file}:{f.line or '?'}")
            print(f"     Message   : {f.message}")
            if f.suggestion:
                print(f"     Suggestion: {f.suggestion}")

    print("\n[Summary & Recommendation]")
    print(result.summary_markdown)
    print("=" * 70)


if __name__ == "__main__":
    main()
