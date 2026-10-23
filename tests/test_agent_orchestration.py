"""End-to-end tests for the hybrid ReviewPilotAgent."""

import json
from pathlib import Path
import pytest

from reviewpilot.agent import ReviewPilotAgent
from reviewpilot.models import PRPayload, RoutingAction, TriageCategory


@pytest.fixture
def sample_prs_data():
    examples_path = Path(__file__).parent.parent / "examples" / "sample_prs.json"
    with open(examples_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestReviewPilotAgentOrchestration:
    def test_auto_approve_pr_bypasses_generative_bedrock(self, sample_prs_data):
        agent = ReviewPilotAgent(confidence_threshold=0.80)
        pr = PRPayload(**sample_prs_data["doc_typo_fix"])
        result = agent.review_pull_request(pr)

        assert result.verdict.action == RoutingAction.AUTO_APPROVE
        assert result.verdict.category == TriageCategory.AUTO_APPROVE.value
        assert not result.verdict.escalated_to_human
        # Generative model was bypassed!
        assert "bypassed" in (result.generative_model_used or "").lower()
        assert result.estimated_cost_usd == 0.0

    def test_security_pr_triggers_bedrock_security_findings(self, sample_prs_data):
        agent = ReviewPilotAgent(confidence_threshold=0.80)
        pr = PRPayload(**sample_prs_data["auth_oauth_security"])
        result = agent.review_pull_request(pr)

        assert result.verdict.action == RoutingAction.SECURITY_ESCALATION
        assert result.verdict.confidence >= 0.80
        assert not result.verdict.escalated_to_human
        assert len(result.findings) > 0
        assert any(f.severity == "critical" for f in result.findings)

    def test_breaking_change_pr_triggers_warning_findings(self, sample_prs_data):
        agent = ReviewPilotAgent(confidence_threshold=0.80)
        pr = PRPayload(**sample_prs_data["db_migration_breaking"])
        result = agent.review_pull_request(pr)

        assert result.verdict.action == RoutingAction.BREAKING_CHANGE
        assert result.verdict.confidence >= 0.80
        assert not result.verdict.escalated_to_human
        assert len(result.findings) > 0
        assert any("breaking" in f.message.lower() for f in result.findings)

    def test_ambiguous_pr_escalates_to_human_lead(self, sample_prs_data):
        agent = ReviewPilotAgent(confidence_threshold=0.80)
        pr = PRPayload(**sample_prs_data["ambiguous_low_confidence"])
        result = agent.review_pull_request(pr)

        assert result.verdict.action == RoutingAction.HUMAN_REVIEW
        assert result.verdict.escalated_to_human is True
        assert "Human Lead Escalation" in result.summary_markdown

    def test_standard_bugfix_generates_code_review(self, sample_prs_data):
        agent = ReviewPilotAgent(confidence_threshold=0.80)
        pr = PRPayload(**sample_prs_data["standard_bugfix"])
        result = agent.review_pull_request(pr)

        assert result.verdict.action == RoutingAction.STANDARD_REVIEW
        assert not result.verdict.escalated_to_human
        assert result.generative_latency_ms > 0
