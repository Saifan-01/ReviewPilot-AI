"""Reusable Strands Decider 2B Pattern: Policy Triage & Uncertainty Gating.

Pattern Tag: #policy
Secondary Tag: #strands-decider-2b

Description:
This reusable pattern uses AWS Strands Decider 2B to evaluate pull requests
or task requests against strict organizational policies, returning a discrete
classification with calibrated confidence. High-confidence decisions proceed
automatically, while uncertain decisions (< threshold) are deterministically
escalated to human review.

Typed Question Contract:
    Question: "Which triage policy category best classifies this pull request code change?"
    Options:
        - auto_approve: Trivial docs, comments, or non-functional edits.
        - standard_review: Normal application logic and feature additions.
        - security_escalation: Auth, cryptographic, or secret modifications.
        - breaking_change: API signatures, database migrations, or contract modifications.

Usage Example:
    >>> from decision_patterns.policy_gatekeeper import PolicyGatekeeperPattern
    >>> gatekeeper = PolicyGatekeeperPattern(confidence_threshold=0.80)
    >>> verdict = gatekeeper.evaluate(pr_payload)
    >>> print(verdict.action)
    RoutingAction.SECURITY_ESCALATION
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from reviewpilot.models import (
    DeciderDecision,
    PRPayload,
    RoutingAction,
    TriageCategory,
    TriageVerdict,
)
from reviewpilot.decider_client import DeciderClient

logger = logging.getLogger(__name__)

# Allowed policy category set
ALLOWED_CATEGORIES = {cat.value for cat in TriageCategory}

DEFAULT_CONFIDENCE_THRESHOLD = 0.80


def resolve_routing_action(
    category: str,
    confidence: float,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> Tuple[RoutingAction, bool, str]:
    """Convert raw Strands Decider 2B decision into an enforced routing action.

    Args:
        category: The category string returned by Decider 2B.
        confidence: The calibrated confidence float in [0.0, 1.0].
        threshold: The minimal confidence required to automate the decision.

    Returns:
        Tuple of (RoutingAction, escalated_to_human, rationale)
    """
    # 1. Integrity check: Valid category
    if category not in ALLOWED_CATEGORIES:
        return (
            RoutingAction.HUMAN_REVIEW,
            True,
            f"Unrecognized policy category '{category}' returned by decision model. Escalating to human.",
        )

    # 2. Integrity check: Calibrated confidence bounds
    if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
        return (
            RoutingAction.HUMAN_REVIEW,
            True,
            f"Invalid confidence value {confidence} (must be between 0.0 and 1.0). Escalating to human.",
        )

    # 3. Uncertainty check: Below confidence threshold
    if confidence < threshold:
        return (
            RoutingAction.HUMAN_REVIEW,
            True,
            (
                f"Confidence {confidence:.2f} is below policy safety threshold {threshold:.2f} "
                f"for category '{category}'. Escalated to engineering lead review."
            ),
        )

    # 4. Confident decision mapping
    if category == TriageCategory.AUTO_APPROVE.value:
        return (
            RoutingAction.AUTO_APPROVE,
            False,
            f"High confidence ({confidence:.2f}) auto-approve: non-functional or documentation change.",
        )
    elif category == TriageCategory.SECURITY_ESCALATION.value:
        return (
            RoutingAction.SECURITY_ESCALATION,
            False,
            f"High confidence ({confidence:.2f}) security escalation: sensitive credentials, crypto, or auth.",
        )
    elif category == TriageCategory.BREAKING_CHANGE.value:
        return (
            RoutingAction.BREAKING_CHANGE,
            False,
            f"High confidence ({confidence:.2f}) breaking change: API or schema modifications.",
        )
    elif category == TriageCategory.STANDARD_REVIEW.value:
        return (
            RoutingAction.STANDARD_REVIEW,
            False,
            f"High confidence ({confidence:.2f}) standard review: normal application logic.",
        )

    return (RoutingAction.HUMAN_REVIEW, True, "Fallback escalation.")


class PolicyGatekeeperPattern:
    """Reusable policy gating pattern integrating Strands Decider 2B."""

    def __init__(
        self,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        decider_client: Optional[DeciderClient] = None,
    ):
        self.confidence_threshold = confidence_threshold
        self.decider = decider_client or DeciderClient()

    def evaluate(self, pr: PRPayload) -> TriageVerdict:
        """Execute the complete policy decision and confidence triage on a PR."""
        decision: DeciderDecision = self.decider.evaluate_triage_policy(pr)
        action, escalated, rationale = resolve_routing_action(
            category=decision.category,
            confidence=decision.confidence,
            threshold=self.confidence_threshold,
        )

        return TriageVerdict(
            pr_id=pr.id,
            action=action,
            category=decision.category,
            confidence=decision.confidence,
            threshold=self.confidence_threshold,
            escalated_to_human=escalated,
            rationale=rationale,
            decision_latency_ms=decision.latency_ms,
        )


def evaluate_policy_triage(
    pr: PRPayload,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    decider_client: Optional[DeciderClient] = None,
) -> TriageVerdict:
    """Functional convenience wrapper for the policy triage pattern."""
    pattern = PolicyGatekeeperPattern(confidence_threshold=threshold, decider_client=decider_client)
    return pattern.evaluate(pr)
