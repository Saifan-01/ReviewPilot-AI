"""Data schemas for ReviewPilot AI."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TriageCategory(str, Enum):
    """Allowed policy categories evaluated by Strands Decider 2B."""
    AUTO_APPROVE = "auto_approve"
    STANDARD_REVIEW = "standard_review"
    SECURITY_ESCALATION = "security_escalation"
    BREAKING_CHANGE = "breaking_change"


class RoutingAction(str, Enum):
    """Enforced routing actions following calibrated confidence thresholding."""
    AUTO_APPROVE = "auto_approve"
    STANDARD_REVIEW = "standard_review"
    SECURITY_ESCALATION = "security_escalation"
    BREAKING_CHANGE = "breaking_change"
    HUMAN_REVIEW = "human_review"


class PRPayload(BaseModel):
    """Normalized pull request payload representing code changes."""
    id: str = Field(default="PR-101", description="Pull request identifier")
    title: str = Field(..., description="PR title summarizing intent")
    description: str = Field(default="", description="PR description and context")
    author: str = Field(default="developer", description="PR author username")
    target_branch: str = Field(default="main", description="Target base branch")
    files_changed: List[str] = Field(default_factory=list, description="List of modified file paths")
    additions: int = Field(default=0, description="Number of added lines")
    deletions: int = Field(default=0, description="Number of deleted lines")
    diff_content: str = Field(..., description="Unified diff string of the changes")


class DeciderDecision(BaseModel):
    """Raw structured decision output returned by Strands Decider 2B."""
    category: str
    confidence: float
    probabilities: Dict[str, float] = Field(default_factory=dict)
    latency_ms: float = 0.0
    model_name: str = "strands-decider-2B"


class TriageVerdict(BaseModel):
    """The routed verdict after applying confidence thresholds and policy rules."""
    pr_id: str
    action: RoutingAction
    category: str
    confidence: float
    threshold: float
    escalated_to_human: bool
    rationale: str
    decision_latency_ms: float


class CodeReviewFinding(BaseModel):
    """Actionable code review finding produced by Amazon Bedrock."""
    file: str
    line: Optional[int] = None
    severity: str = "info"  # info, warning, critical
    message: str
    suggestion: Optional[str] = None


class ReviewResult(BaseModel):
    """End-to-end outcome combining Decider 2B decision and Bedrock generative review."""
    verdict: TriageVerdict
    findings: List[CodeReviewFinding] = Field(default_factory=list)
    summary_markdown: str = ""
    generative_model_used: Optional[str] = None
    generative_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    guardrails_passed: bool = True
