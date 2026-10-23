"""Unit tests for reusable Strands Decider decision patterns (#policy, #guardrails)."""

import pytest

from decision_patterns.policy_gatekeeper import (
    PolicyGatekeeperPattern,
    resolve_routing_action,
)
from decision_patterns.guardrails_intervention import DeciderGuardrailHandler
from reviewpilot.models import (
    PRPayload,
    RoutingAction,
    TriageCategory,
)
from strands.interventions import Deny, Proceed


class DummyEvent:
    def __init__(self, tool_name: str, arguments: dict, context: str = ""):
        self.tool_name = tool_name
        self.arguments = arguments
        self.context = context


class TestPolicyTriagePattern:
    """Tests for the #policy decision pattern and confidence gating."""

    def test_high_confidence_auto_approve(self):
        action, escalated, rationale = resolve_routing_action(
            category=TriageCategory.AUTO_APPROVE.value,
            confidence=0.95,
            threshold=0.80,
        )
        assert action == RoutingAction.AUTO_APPROVE
        assert not escalated
        assert "auto-approve" in rationale.lower()

    def test_high_confidence_security_escalation(self):
        action, escalated, rationale = resolve_routing_action(
            category=TriageCategory.SECURITY_ESCALATION.value,
            confidence=0.92,
            threshold=0.80,
        )
        assert action == RoutingAction.SECURITY_ESCALATION
        assert not escalated
        assert "security" in rationale.lower()

    def test_high_confidence_breaking_change(self):
        action, escalated, rationale = resolve_routing_action(
            category=TriageCategory.BREAKING_CHANGE.value,
            confidence=0.85,
            threshold=0.80,
        )
        assert action == RoutingAction.BREAKING_CHANGE
        assert not escalated
        assert "breaking change" in rationale.lower()

    def test_high_confidence_standard_review(self):
        action, escalated, rationale = resolve_routing_action(
            category=TriageCategory.STANDARD_REVIEW.value,
            confidence=0.88,
            threshold=0.80,
        )
        assert action == RoutingAction.STANDARD_REVIEW
        assert not escalated
        assert "standard review" in rationale.lower()

    def test_low_confidence_triggers_human_review(self):
        # Even if category is standard_review, low confidence MUST escalate!
        action, escalated, rationale = resolve_routing_action(
            category=TriageCategory.STANDARD_REVIEW.value,
            confidence=0.62,
            threshold=0.80,
        )
        assert action == RoutingAction.HUMAN_REVIEW
        assert escalated is True
        assert "below policy safety threshold" in rationale

    def test_threshold_boundary_cases(self):
        # Exactly equal to threshold -> proceeds
        action_eq, escalated_eq, _ = resolve_routing_action(
            category=TriageCategory.STANDARD_REVIEW.value,
            confidence=0.80,
            threshold=0.80,
        )
        assert action_eq == RoutingAction.STANDARD_REVIEW
        assert not escalated_eq

        # Just below threshold -> escalates
        action_below, escalated_below, _ = resolve_routing_action(
            category=TriageCategory.STANDARD_REVIEW.value,
            confidence=0.799,
            threshold=0.80,
        )
        assert action_below == RoutingAction.HUMAN_REVIEW
        assert escalated_below is True

    def test_unrecognized_category_escalates(self):
        action, escalated, rationale = resolve_routing_action(
            category="random_hallucinated_category",
            confidence=0.99,
            threshold=0.80,
        )
        assert action == RoutingAction.HUMAN_REVIEW
        assert escalated is True
        assert "Unrecognized policy category" in rationale

    def test_invalid_confidence_values_escalate(self):
        # Confidence > 1.0
        action, escalated, _ = resolve_routing_action(
            category=TriageCategory.STANDARD_REVIEW.value,
            confidence=1.5,
            threshold=0.80,
        )
        assert action == RoutingAction.HUMAN_REVIEW
        assert escalated is True

        # Negative confidence
        action_neg, escalated_neg, _ = resolve_routing_action(
            category=TriageCategory.STANDARD_REVIEW.value,
            confidence=-0.1,
            threshold=0.80,
        )
        assert action_neg == RoutingAction.HUMAN_REVIEW
        assert escalated_neg is True


class TestGuardrailsInterventionPattern:
    """Tests for the #guardrails native Strands intervention handler."""

    def test_safe_non_critical_tool_proceeds(self):
        handler = DeciderGuardrailHandler()
        event = DummyEvent(tool_name="post_pr_comment", arguments={"pr_id": "PR-101", "comment": "LGTM"})
        action = handler.before_tool_call(event)
        assert isinstance(action, Proceed)

    def test_dangerous_tool_triggers_guardrail_denial(self):
        handler = DeciderGuardrailHandler()
        event = DummyEvent(
            tool_name="merge_pr",
            arguments={"pr_id": "PR-101", "commit_message": "Force merge untested code"},
            context="High-risk security PR with failing tests",
        )
        action = handler.before_tool_call(event)
        assert isinstance(action, Deny)
        assert "guardrail rejected" in action.reason.lower()
