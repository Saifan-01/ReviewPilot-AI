# Reusable Strands Decider 2B Pattern Guide

> **Pattern Tag:** `#policy` (Primary) & `#guardrails` (Secondary)  
> **Target Frameworks:** AWS Strands Agents SDK, LangChain, LlamaIndex, or vanilla Python agents.

This guide explains how other builders can adopt the **Policy Triage & Uncertainty Gating Pattern** demonstrated in ReviewPilot AI for their own applications.

---

## 1. Why Use This Pattern?

Most AI agents rely on general-purpose LLMs to make routing and categorization decisions. This introduces three problems:
1. **High Latency:** Waiting 2–4 seconds for an LLM to output a single word (`"billing"`, `"security"`, or `"approve"`).
2. **High Cost:** Incurring token input charges on large context payloads for binary or categorical decisions.
3. **Uncalibrated Confidence:** Generative models do not output mathematically calibrated probabilities, making reliable confidence-based escalation impossible.

**Strands Decider 2B** solves this by outputting calibrated probabilities over predefined choices in **~115 ms**.

---

## 2. The Decision Pattern Contract

### The Typed Question
```python
QUESTION = "Which triage policy category best classifies this pull request code change?"
```

### The Category & Criteria Mapping
```python
CRITERIA = {
    "auto_approve": (
        "Non-functional documentation, formatting, comments, or trivial typo fixes "
        "with zero business logic impact and zero security risk."
    ),
    "standard_review": (
        "Standard application code changes, bugfixes, UI updates, and incremental feature additions "
        "requiring standard automated tests and generative code review."
    ),
    "security_escalation": (
        "Changes touching authentication, authorization, cryptographic keys, secret management, "
        "session tokens, permissions, or raw database queries."
    ),
    "breaking_change": (
        "Changes modifying public API signatures, removing endpoints, altering database schemas, "
        "or changing serialization contracts that could break downstream consumers."
    ),
}
```

---

## 3. How to Wire the Pattern into Your Agent

### Step 1: Install Dependencies
```bash
pip install strands-decider strands-agents httpx pydantic
```

### Step 2: Import and Call the Policy Gatekeeper
```python
from decision_patterns.policy_gatekeeper import PolicyGatekeeperPattern
from reviewpilot.models import PRPayload

# Initialize gatekeeper with a calibrated confidence threshold (e.g. 0.80)
gatekeeper = PolicyGatekeeperPattern(confidence_threshold=0.80)

# Create or receive your task payload
pr = PRPayload(
    id="PR-101",
    title="fix: handle null pointer in session handler",
    diff_content="...",
    files_changed=["auth/session.py"]
)

# Evaluate decision
verdict = gatekeeper.evaluate(pr)

print(f"Action: {verdict.action}")               # e.g., RoutingAction.SECURITY_ESCALATION
print(f"Confidence: {verdict.confidence:.2f}")    # e.g., 0.94
print(f"Escalated to Human: {verdict.escalated_to_human}")
```

### Step 3: Wire into Execution Flow
```python
if verdict.action == RoutingAction.AUTO_APPROVE:
    # Bypass heavy LLM entirely!
    merge_pull_request(pr.id)

elif verdict.action == RoutingAction.HUMAN_REVIEW:
    # Halt autonomous actions and alert a human
    notify_tech_lead(pr.id, rationale=verdict.rationale)

elif verdict.action == RoutingAction.SECURITY_ESCALATION:
    # Trigger specialized Bedrock DevSecOps prompt
    run_bedrock_security_audit(pr)

else:
    # Standard code review
    run_bedrock_standard_review(pr)
```

---

## 4. Native Strands Guardrail Handler (#guardrails)

You can also use Strands Decider 2B as a tool-call intervention handler:

```python
from strands import Agent
from decision_patterns.guardrails_intervention import DeciderGuardrailHandler

guardrail = DeciderGuardrailHandler(
    critical_tools=["merge_pr", "delete_database", "execute_bash"]
)

agent = Agent(
    model="anthropic.claude-3-haiku-20240307-v1:0",
    tools=[merge_pr, run_tests],
    interventions=[guardrail]  # Intercepts every tool call before execution!
)
```

If the agent tries to call `merge_pr` when tests are failing or security vulnerabilities exist, Decider 2B intercepts the tool call and returns `Deny(reason=...)`.

---

## 5. Adaptation for Other Domains

This pattern is immediately transferable to other domains:

| Domain | Typed Question | Options |
| :--- | :--- | :--- |
| **Customer Support** | "Which department should handle this ticket?" | `billing`, `tech_support`, `account_access`, `escalate` |
| **FinTech Transactions** | "What is the fraud risk tier of this transaction?" | `low_risk_approve`, `standard_verify`, `high_risk_block` |
| **Infrastructure Alerting**| "What severity level does this system alert represent?" | `info_ignore`, `warning_log`, `critical_page_oncall` |
| **Model Routing** | "What model capacity is required for this user query?" | `fast_small_model`, `heavy_reasoning_model` |
