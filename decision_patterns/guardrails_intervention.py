"""Reusable Strands Decider 2B Pattern: Guardrails Intervention Handler.

Pattern Tag: #guardrails
Secondary Tag: #strands-decider-2b

Description:
Hooks directly into the Strands Agents SDK native InterventionHandler system.
Before an agent executes any external or dangerous tool (e.g., merging a PR,
modifying git history, or running arbitrary shell commands), this handler
queries Strands Decider 2B with a binary or choice safety question.
If the proposed action is deemed unsafe or violates repository guardrails,
the handler halts execution via Deny() or requests manual authorization via Confirm().
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from strands.interventions import (
    Confirm,
    Deny,
    InterventionHandler,
    OnError,
    Proceed,
)
from reviewpilot.decider_client import DeciderClient

logger = logging.getLogger(__name__)


class DeciderGuardrailHandler(InterventionHandler):
    """Strands intervention handler powered by Strands Decider 2B."""

    def __init__(
        self,
        name: str = "decider-guardrails",
        decider_client: Optional[DeciderClient] = None,
        critical_tools: Optional[list[str]] = None,
        on_error: OnError = "throw",
    ):
        self._name = name
        self.decider = decider_client or DeciderClient()
        self.critical_tools = critical_tools or [
            "merge_pr",
            "push_to_main",
            "delete_branch",
            "execute_raw_sql",
            "disable_security_checks",
        ]
        self._on_error = on_error

    @property
    def name(self) -> str:
        return self._name

    @property
    def on_error(self) -> OnError:
        return self._on_error

    def before_tool_call(self, event: Any, **kwargs: Any) -> Proceed | Deny | Confirm:
        """Evaluate whether tool call is safe to proceed via Decider 2B."""
        tool_name = getattr(event, "tool_name", "") or getattr(event, "name", "")
        tool_args = getattr(event, "arguments", {}) or getattr(event, "args", {})
        context = str(getattr(event, "context", ""))

        # Check if the tool is in the high-risk guardrail list
        if tool_name in self.critical_tools:
            logger.info("Evaluating safety for critical tool '%s' via Decider 2B...", tool_name)
            result = self.decider.evaluate_tool_safety(
                tool_name=tool_name,
                arguments=tool_args,
                context=context,
            )

            if not result.get("is_safe", False):
                reason = (
                    f"Strands Decider 2B guardrail rejected execution of '{tool_name}' "
                    f"(safety score: {result.get('score', 0.0):.2f}). Policy violation prevented."
                )
                logger.warning(reason)
                return Deny(reason=reason)

        return Proceed()
