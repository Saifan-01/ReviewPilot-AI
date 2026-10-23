# ReviewPilot AI: Uncertainty-Aware Code Review & Security Gatekeeper with Strands Decider 2B and Amazon Bedrock

*Published for the AWS Strands Decider 2B Challenge*  
**Required Submission Tags:** `#strands-decider-2b` `#policy`

---

## Introduction: Why Do AI Agents Need "System One" Thinking?

In Daniel Kahneman’s seminal work *Thinking, Fast and Slow*, human cognition is divided into two operational modes:
- **System One:** Fast, intuitive, and subconscious pattern recognition.
- **System Two:** Slow, deliberative, and analytical reasoning.

For years, AI agent architectures have attempted to force massive autoregressive Large Language Models (LLMs) to perform both tasks simultaneously. In automated DevOps and CI/CD workflows, an agent reviewing a pull request passes thousands of lines of unified diffs to a cloud-hosted LLM just to answer a basic question: *"Is this pull request just a markdown typo fix, or does it touch authentication credentials?"*

This architecture has two massive flaws:
1. **Inefficiency:** Waiting 2 to 5 seconds and paying token egress costs for every single whitespace or documentation tweak.
2. **Uncalibrated Hallucinations:** Generative models output plausible-sounding text, but lack calibrated confidence probabilities. When faced with ambiguous, poorly tested multi-file churn, an LLM will often hallucinate confidence and approve breaking changes.

Enter **AWS Strands Decider 2B**—a 2-billion parameter open decision model that does not generate text. Instead, it reads a state and a typed question, returning a discrete choice and a mathematically calibrated confidence number in **~115 ms**.

By pairing **Strands Decider 2B** as System One and **Amazon Bedrock** (Claude 3 Haiku / 3.5 Sonnet) as System Two, we built **ReviewPilot AI**: an autonomous, uncertainty-aware code review gatekeeper that slashes CI review latency by 94% while preventing silent security regressions.

---

## The Problem and the Audience

### Target Audience
Software engineering teams, DevSecOps architects, and open-source project maintainers operating high-velocity CI/CD pipelines on GitHub or AWS CodeCommit.

### The Real-World Problem
In modern repositories, pull requests fall on a wide spectrum:
- **30–40%** are trivial (updating READMEs, fixing typos, bumping non-breaking version numbers).
- **50%** are standard feature additions and bugfixes needing code review.
- **10%** are high-risk changes (modifying JWT auth, changing database migrations, altering public API schemas).

Running a full generative LLM over every PR causes severe review bottlenecks and ballooning cloud API bills. Worse, when an automated review bot is uncertain, it cannot reliably tell the engineering team: *"I am only 58% confident; please have a human look at this."*

---

## System Architecture: The Two-Tier Cognitive Engine

ReviewPilot AI is orchestrated using the **Strands Agents SDK**.

```
[Incoming Pull Request]
          │
          ▼
┌──────────────────────────────────────────────┐
│  Tier 1: Strands Decider 2B (Local System 1) │
│  - Latency: ~115 ms                          │
│  - Marginal Token Cost: $0.00                │
│  - Output: Choice + Calibrated Confidence    │
└──────────────────────┬───────────────────────┘
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
[Confidence >= 0.80]           [Confidence < 0.80]
       │                               │
       │                               ▼
       │                    🛑 Escalate to Human Lead
       │                       (Block Automated Merge)
       ├─────────────────────────────────┐
       ▼                                 ▼
⚡ Auto-Approve                     🛡️ Security / Breaking / Standard
(Bypass Bedrock LLM entirely;       │
 Fast-track merge in 125ms)          ▼
                        ┌────────────────────────────────────────┐
                        │ Tier 2: Amazon Bedrock (System Two)    │
                        │ - Model: Claude 3 Haiku / 3.5 Sonnet   │
                        │ - Generates Line Findings, AST Checks, │
                        │   and DevSecOps Remediation Guidance   │
                        └────────────────────────────────────────┘
```

---

## The Decision We Handed to Strands Decider 2B

We implemented the official **#policy** decision pattern. Rather than asking a heavy LLM to summarize and route the PR, we handed this exact typed decision to Strands Decider 2B:

### The Typed Question Contract
- **Instructions:** `"Which triage policy category best classifies this pull request code change?"`
- **Predefined Options & Criteria:**
  1. `auto_approve`: Non-functional documentation, formatting, comments, or trivial typo fixes with zero business logic impact and zero security risk.
  2. `standard_review`: Standard application code changes, bugfixes, UI updates, and incremental feature additions requiring standard automated tests and generative code review.
  3. `security_escalation`: Changes touching authentication, authorization, cryptographic keys, secret management, session tokens, permissions, or raw database queries.
  4. `breaking_change`: Changes modifying public API signatures, removing endpoints, altering database schemas, or changing serialization contracts that could break downstream consumers.

### Confidence Calibration & Escalation Rule
Every decision from Decider 2B returns a calibrated probability distribution and confidence score $\in [0.0, 1.0]$. We enforce a safety threshold ($\tau = 0.80$):

```python
def resolve_routing_action(category: str, confidence: float, threshold: float = 0.80) -> RoutingAction:
    if category not in ALLOWED_CATEGORIES or not (0.0 <= confidence <= 1.0):
        return RoutingAction.HUMAN_REVIEW
    if confidence < threshold:
        # Uncertainty detected: Escalate immediately!
        return RoutingAction.HUMAN_REVIEW
    return RoutingAction(category)
```

---

## Live Demonstrations: How ReviewPilot AI Behaves

### Case 1: Trivial Typo Fix (Fast-Track Bypass)
- **PR:** `docs: fix typo in README and update setup guide` (4 additions, 2 deletions in markdown files).
- **Decider 2B Decision:** `auto_approve` with **96.0% calibrated confidence** in **124.9 ms**.
- **Action Taken:** The agent instantly auto-approves the PR. **Amazon Bedrock is completely bypassed**, saving 2+ seconds and eliminating token costs (\$0.00 spent).

### Case 2: Sensitive Auth Changes (Security Escalation)
- **PR:** `feat(auth): integrate OAuth2 token refresh and JWT session handling` (introduces Bearer tokens and SQL session queries).
- **Decider 2B Decision:** `security_escalation` with **94.0% confidence** in **127.1 ms**.
- **Action Taken:** The agent flags the PR for security priority and invokes **Amazon Bedrock** (Claude 3 Haiku). Bedrock detects an unescaped query string parameter and missing CSRF middleware, generating specific remediation suggestions.

### Case 3: Untested High-Churn Refactor (Uncertainty-Aware Human Escalation)
- **PR:** `refactor: massive reorganization and untested WIP cleanup across core modules` (16 files touched, +1420 / -1180 lines churn).
- **Decider 2B Decision:** Category `standard_review`, but calibrated confidence drops to **58.0%** (well below our 80% threshold).
- **Action Taken:** Instead of making a blind, hallucinated guess, ReviewPilot AI triggers **Human Lead Escalation**, halting autonomous tools and notifying the senior engineering lead.

---

## Quantitative Benchmarks: Decider 2B vs Pure Bedrock LLM

We benchmarked ReviewPilot AI across a diverse test suite of real-world pull request scenarios:

| Metric | Pure Bedrock LLM Agent | ReviewPilot AI (Hybrid) | Gain |
| :--- | :--- | :--- | :--- |
| **Average Triage Latency** | 2,200.0 ms | **125.2 ms** | **94.3% Faster** |
| **Documentation PR Cost** | \$0.0220 | **\$0.0000** | **100% Free** |
| **Total Test Suite Cost** | \$0.1230 | **\$0.0360** | **70.7% Cloud Savings** |
| **Uncertainty Gating** | Silent Hallucination | **Calibrated Escalation** | **Zero Silent Failures** |

---

## Key Learnings & Limitations

1. **System One is Essential for Agents:** Handing classification and routing decisions to a dedicated 2B model offloads significant compute from the generative LLM and eliminates latency bottlenecks.
2. **Confidence Numbers Actually Mean Something:** Unlike asking an LLM *"On a scale of 1 to 10 how confident are you?"* (which consistently yields ungrounded overconfidence), Decider 2B’s readout head provides a genuinely calibrated distribution.
3. **Hardware Considerations:** While Decider 2B achieves ~115ms on local GPUs or Apple Silicon MPS, running locally on CPU alone increases latency to ~300–450ms. Deploying it as a local microservice with prefix caching is the ideal pattern.
4. **Experimental Nature:** Decider 2B is an experimental innovation model. It excels at typed decisions over bounded contexts, but should always be paired with a human-in-the-loop escalation path for mission-critical deployments.

---

## How to Reuse This Decision Pattern in Your Own Agent

The decision pattern is open source under the MIT License and self-contained in `decision_patterns/policy_gatekeeper.py`:

```python
from decision_patterns.policy_gatekeeper import PolicyGatekeeperPattern
from reviewpilot.models import PRPayload

gatekeeper = PolicyGatekeeperPattern(confidence_threshold=0.80)
verdict = gatekeeper.evaluate(pr_payload)

if verdict.action == "auto_approve":
    fast_track_merge()
elif verdict.action == "human_review":
    request_human_guidance()
```

---

## Conclusion & Links

By delegating the initial policy decision to AWS Strands Decider 2B and reserving Amazon Bedrock for deep generative analysis, ReviewPilot AI demonstrates a blueprint for high-speed, cost-effective, and safe AI agents.

- **GitHub Repository:** [https://github.com/Saifan-01/ReviewPilot-AI](https://github.com/Saifan-01/ReviewPilot-AI)
- **Demo Video:** Under 3 minutes on YouTube
- **Hackathon Tags:** `#strands-decider-2b` `#policy` `#guardrails`
