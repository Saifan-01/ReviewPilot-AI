"""ReviewPilot AI Agent - Hybrid Strands Decider 2B + Amazon Bedrock Agent.

Orchestrates the complete pull request triage and review lifecycle:
1. Fast System One Decision: Strands Decider 2B classifies the PR into a policy category.
2. Calibrated Confidence Gating: High confidence triggers targeted actions; low confidence escalates to human review.
3. Fast-Track Bypass: Non-functional PRs (auto_approve) skip expensive LLM calls, saving latency and money.
4. Deep System Two Review: Amazon Bedrock performs generative code analysis, security auditing, and AST feedback.
5. Guardrail Protection: Strands InterventionHandler gates any destructive tool calls.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from strands import Agent, tool
from strands.models import BedrockModel

from decision_patterns.guardrails_intervention import DeciderGuardrailHandler
from decision_patterns.policy_gatekeeper import PolicyGatekeeperPattern
from reviewpilot.bedrock_reviewer import BedrockReviewer
from reviewpilot.decider_client import DeciderClient
from reviewpilot.models import PRPayload, ReviewResult, RoutingAction, TriageVerdict

logger = logging.getLogger(__name__)


# Native Strands Agent tools with simulated CI/CD actions
@tool
def post_pr_comment(pr_id: str, comment: str) -> str:
    """Post an automated review comment to the GitHub pull request."""
    return f"Successfully posted review comment on PR #{pr_id}."


@tool
def merge_pr(pr_id: str, commit_message: str) -> str:
    """Merge an approved pull request into the target branch. (High-risk action protected by Decider guardrails)."""
    return f"Successfully merged PR #{pr_id} with commit: '{commit_message}'."


@tool
def trigger_security_alert(pr_id: str, severity: str, details: str) -> str:
    """Notify the DevSecOps team regarding high-risk code changes."""
    return f"DevSecOps alert triggered for PR #{pr_id} [Severity: {severity}]."


class ReviewPilotAgent:
    """Production-grade Strands Agent combining Decider 2B and Amazon Bedrock."""

    def __init__(
        self,
        confidence_threshold: float = 0.80,
        decider_client: Optional[DeciderClient] = None,
        bedrock_reviewer: Optional[BedrockReviewer] = None,
        enable_strands_runtime: bool = True,
    ):
        self.confidence_threshold = confidence_threshold
        self.decider = decider_client or DeciderClient()
        self.bedrock = bedrock_reviewer or BedrockReviewer()
        self.gatekeeper = PolicyGatekeeperPattern(
            confidence_threshold=confidence_threshold,
            decider_client=self.decider,
        )

        self.enable_strands_runtime = enable_strands_runtime
        self.strands_agent: Optional[Agent] = None

        if self.enable_strands_runtime:
            self._init_strands_agent()

    def _init_strands_agent(self) -> None:
        """Initialize the underlying Strands Agent with native intervention handlers."""
        guardrail = DeciderGuardrailHandler(
            name="decider-tool-guardrail",
            decider_client=self.decider,
        )

        try:
            # Check if Bedrock credentials are ready
            if self.bedrock.is_available():
                model = BedrockModel(model_id=self.bedrock.model_id)
            else:
                model = None  # Agent runs in tool/interventions mode

            self.strands_agent = Agent(
                model=model,
                tools=[post_pr_comment, merge_pr, trigger_security_alert],
                interventions=[guardrail],
                system_prompt=(
                    "You are ReviewPilot AI, an autonomous DevSecOps and code review assistant. "
                    "You evaluate code changes and coordinate PR actions safely."
                ),
            )
        except Exception as e:
            logger.warning("Could not initialize full Strands Agent runtime: %s", e)
            self.strands_agent = None

    def review_pull_request(self, pr: PRPayload) -> ReviewResult:
        """Execute end-to-end pull request evaluation workflow."""
        total_start = time.perf_counter()

        # Step 1: Hand the decision to Strands Decider 2B
        verdict: TriageVerdict = self.gatekeeper.evaluate(pr)

        findings = []
        summary = ""
        gen_latency = 0.0
        cost = 0.0
        used_model = None

        # Step 2: Act based on calibrated policy verdict
        if verdict.action == RoutingAction.AUTO_APPROVE:
            # Optimization: Fast-track approval. Bypass heavy LLM call!
            summary = (
                f"### Fast-Track Approval: Non-Functional Change\n\n"
                f"- **Decision:** Auto-Approved by **Strands Decider 2B**\n"
                f"- **Calibrated Confidence:** {verdict.confidence * 100:.1f}%\n"
                f"- **Decision Latency:** {verdict.decision_latency_ms:.1f} ms\n"
                f"- **Cost Savings:** Bypassed heavy Bedrock LLM inspection ($0.00 spent)\n\n"
                f"PR #{pr.id} consists strictly of documentation, formatting, or trivial fixes. "
                f"Ready for automatic merge."
            )
            used_model = "bypassed (Decider 2B fast-track)"

        elif verdict.action == RoutingAction.HUMAN_REVIEW:
            # Uncertainty-aware safety: Escalate low-confidence cases to engineering leads
            summary = (
                f"### Human Lead Escalation: Low Confidence Triage\n\n"
                f"Strands Decider 2B evaluated this PR as `{verdict.category}`, but its "
                f"calibrated confidence (**{verdict.confidence * 100:.1f}%**) fell below "
                f"the required safety threshold of **{verdict.threshold * 100:.1f}%**.\n\n"
                f"**Rationale:** {verdict.rationale}\n\n"
                f"**Action:** Automated tools halted. Flagged for review by the Tech Lead."
            )
            used_model = "escalated (human review required)"

        else:
            # Step 3: High-confidence standard, security, or breaking change -> Amazon Bedrock review
            findings, summary, gen_latency, cost = self.bedrock.review_code_change(
                pr=pr, verdict=verdict
            )
            used_model = self.bedrock.model_id

        total_latency = (time.perf_counter() - total_start) * 1000

        return ReviewResult(
            verdict=verdict,
            findings=findings,
            summary_markdown=summary,
            generative_model_used=used_model,
            generative_latency_ms=gen_latency,
            total_latency_ms=round(total_latency, 1),
            estimated_cost_usd=cost,
            guardrails_passed=not verdict.escalated_to_human,
        )
