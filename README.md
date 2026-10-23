# ReviewPilot AI
### Uncertainty-Aware Code Review & Security Gatekeeper Agent
**Powered by AWS Strands Decider 2B & Amazon Bedrock**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Strands Decider 2B](https://img.shields.io/badge/Decision%20Model-Strands%20Decider%202B-purple.svg)](https://github.com/strands-labs/strands-decider)
[![Amazon Bedrock](https://img.shields.io/badge/Generative%20AI-Amazon%20Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![Tests: 21 Passed](https://img.shields.io/badge/Unit%20Tests-21%20Passed-brightgreen.svg)](tests/)
[![Pattern: #policy](https://img.shields.io/badge/Pattern-%23policy-blue.svg)](decision_patterns/policy_gatekeeper.py)
[![Guardrail: #guardrails](https://img.shields.io/badge/Pattern-%23guardrails-red.svg)](decision_patterns/guardrails_intervention.py)

---

## Submission Overview

ReviewPilot AI is an original AI agent developed for the **AWS Strands Decider 2B Challenge**. It introduces a two-tier cognitive architecture:
- **System One (Fast & Instinctive):** **AWS Strands Decider 2B** acts as a local ~115ms decision gatekeeper ($0 marginal token cost) evaluating pull requests against strict organizational policies with mathematically calibrated confidence numbers.
- **System Two (Deliberative & Generative):** **Amazon Bedrock** (Anthropic Claude 3 Haiku / 3.5 Sonnet) is invoked selectively for deep code analysis, AST syntax verification, and DevSecOps remediation only when changes require generative reasoning.

### Submission Deliverables Checklist
- [x] **Working Agent:** Hybrid Strands Agent combining Decider 2B and Amazon Bedrock.
- [x] **Demonstrated Decision Pattern:** **`#policy`** (Primary) and **`#guardrails`** (Secondary).
- [x] **Reusable Decision Pattern:** Self-contained module in [`decision_patterns/policy_gatekeeper.py`](decision_patterns/policy_gatekeeper.py).
- [x] **Open Source Public Repository:** OSI-approved [MIT License](LICENSE), setup instructions, configuration templates, and 21 unit tests.
- [x] **Builder Center Article:** Comprehensive technical deep-dive in [`docs/builder_center_article.md`](docs/builder_center_article.md).
- [x] **Demo Video (< 3 min):** Exact timestamped storyboard and script in [`docs/demo_video_script.md`](docs/demo_video_script.md).
- [x] **Quantitative Measurement:** 94.3% triage latency reduction and 70.7% cloud cost savings benchmarked in [`benchmark/benchmark_comparison.py`](benchmark/benchmark_comparison.py).
- [x] **Empirical Calibration Study:** 20-PR benchmark evaluation reporting 95% accuracy and 9.15% ECE in [`benchmark/evaluate_dataset.py`](benchmark/evaluate_dataset.py).

---

## Architectural Philosophy: System 1 vs System 2

In human cognition (Kahneman, 2011), mental operations are divided into:
1. **System 1:** Fast, instinctive, and pattern-based classification.
2. **System 2:** Slow, deliberative, and analytical reasoning.

Traditional AI coding assistants force general-purpose autoregressive LLMs to handle both tasks. When an automated bot reads a pull request, passing thousands of lines of unified diffs to a cloud-hosted LLM just to decide whether a PR is a documentation typo fix introduces three major flaws:
- **Severe Latency Bottlenecks:** Waiting 2 to 5 seconds per triage decision.
- **Unnecessary Cloud Spend:** Paying token fees for routine, trivial file changes.
- **Uncalibrated Hallucinations:** Generative LLMs lack mathematically calibrated confidence scores. When evaluating complex or ambiguous diffs, they frequently hallucinate approval rather than signaling uncertainty.

ReviewPilot AI resolves this dilemma by dedicating **AWS Strands Decider 2B** to System 1 decision-making and reserving **Amazon Bedrock** for System 2 generative inspection.

```
[Developer Submits Pull Request Diff & Metadata]
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│  Tier 1: Strands Decider 2B (Local System 1 Engine)    │
│  - Latency: ~115-125 ms                                │
│  - Marginal Token Cost: $0.00                          │
│  - Output: Choice + Mathematically Calibrated Conf.    │
└──────────────────────┬─────────────────────────────────┘
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
[Confidence >= tau (0.80)]      [Confidence < tau]
       │                               │
       │                               ▼
       │                    [!] Escalate to Human Lead
       │                        (Halt Automated CI Tools)
       ├─────────────────────────────────┐
       ▼                                 ▼
Auto-Approve                        Security / Breaking / Standard
(Bypass Bedrock LLM entirely;       │
 Fast-track merge in 125ms)          ▼
                        ┌────────────────────────────────────────┐
                        │ Tier 2: Amazon Bedrock (System 2)      │
                        │ - Model: Claude 3 Haiku / 3.5 Sonnet   │
                        │ - Generates Line Findings, AST Checks, │
                        │   and DevSecOps Remediation Guidance   │
                        └────────────────────────────────────────┘
```

---

## End-to-End Workflow & Execution Lifecycle

ReviewPilot AI executes a structured six-stage evaluation pipeline for any pull request:

### Stage 1: Input Ingestion & State Representation
The agent ingests the unified git diff, modified file paths, lines added/deleted, author metadata, and PR title/description. It normalizes these features into a structured, bounded state string:
```text
Pull Request #PR-101: feat(auth): add OAuth2 refresh token handler
Author: security-dev | Target: main
Files Changed (3): src/auth/service.py, src/auth/jwt.py, config/keys.py
Stats: +142 / -18 lines
---
Unified Diff Snippet:
[diff content...]
```

### Stage 2: Strands Decider 2B Policy Inference
The normalized state is submitted to the local Strands Decider 2B engine (`/v1/systemone`) alongside a typed `ChoiceQuestion`:
- **Instructions:** `"Which triage policy category best classifies this pull request code change?"`
- **Predefined Options & Criteria:**
  - `auto_approve`: Non-functional documentation, formatting, comments, or trivial typo fixes.
  - `standard_review`: Standard application logic, UI, and incremental bugfixes.
  - `security_escalation`: Modifications to auth, secrets, cryptographic keys, session tokens, or raw SQL queries.
  - `breaking_change`: Modifications to public API endpoints, database schemas, or serialization contracts.

Decider 2B evaluates the token representations through its readout head, returning a discrete choice, a full probability distribution, and a calibrated confidence score in **~115 ms**.

### Stage 3: Calibrated Confidence Gating
The decision is evaluated against an organizational safety threshold ($\tau = 0.80$):
$$\text{Enforced Action} = \begin{cases} 
\text{Category}, & \text{if } \text{confidence} \ge \tau \\
\text{HUMAN\_REVIEW}, & \text{if } \text{confidence} < \tau 
\end{cases}$$

### Stage 4: Branching Execution

#### Branch A: Fast-Track Auto-Approve (Confidence >= 0.80)
If the category is `auto_approve` (e.g., markdown typo fix, documentation edit):
- **Action:** Approved immediately.
- **LLM Bypass:** Amazon Bedrock is completely bypassed.
- **Result:** Review completes in **124.9 ms** at **$0.0000** cloud cost.

#### Branch B: Security Escalation (Confidence >= 0.80)
If the category is `security_escalation` (e.g., JWT modification, raw SQL execution):
- **Action:** Flagged with high-priority security status.
- **Generative Audit:** Amazon Bedrock (Claude 3 Haiku) inspects the diff context for injection risks, token leakage, and missing headers.
- **Result:** Line-level findings with severity ratings (`CRITICAL`, `WARNING`, `INFO`) and copy-paste remediation suggestions.

#### Branch C: Breaking Change Contract Review (Confidence >= 0.80)
If the category is `breaking_change` (e.g., database schema drop column, public endpoint removal):
- **Action:** Flagged for API and schema maintainers.
- **Contract Impact:** Amazon Bedrock generates downstream impact analysis and migration rollback recommendations.

#### Branch D: Standard Application Review (Confidence >= 0.80)
If the category is `standard_review` (e.g., feature additions, logic bugfixes):
- **Action:** Standard code review.
- **Code Inspection:** Amazon Bedrock verifies edge cases, boundary conditions, and test coverage requirements.

#### Branch E: Uncertainty-Aware Human Escalation (Confidence < 0.80)
If Decider 2B's confidence falls below 0.80 (e.g., an ambiguous, untested high-churn refactor across 16 files):
- **Action:** The agent **refuses to hallucinate a verdict**.
- **Enforcement:** Autonomous tool calls (such as `merge_pr`) are blocked.
- **Result:** The PR is routed directly to the Senior Engineering Lead queue with full diagnostic rationale.

### Stage 5: Native Strands Tool Guardrails
Before the agent executes any tool that interacts with external infrastructure (such as `merge_pr` or `trigger_security_alert`), the action passes through `DeciderGuardrailHandler` (a native subclass of Strands' `InterventionHandler`). If Decider 2B detects unverified risks, it rejects execution via `Deny()`.

### Stage 6: Formatted Output Delivery
The agent generates an executive Markdown summary, individual line findings, latency breakdowns, and cost metrics for display in the CLI, GitHub PR comment, or Web Dashboard.

---

## The Role of AWS Strands Agents SDK & Decider 2B

### What Makes Strands Decider 2B Different?
Unlike standard generative models, **Strands Decider 2B**:
1. **Contains No Autoregressive LM Head:** It replaces the generation head with a pointer/readout head over input logits. It cannot produce free-form text or hallucinated explanations.
2. **Runs Locally on Modest Hardware:** With ~1.9B parameters, it runs locally on consumer GPUs, Apple Silicon (MPS), or CPUs via prefix caching in ~115–125 ms.
3. **Outputs Mathematically Calibrated Confidence:** Standard LLMs cannot tell you how confident they are; asking them yields arbitrary numbers. Decider 2B's readout head produces genuine log-probability calibration.
4. **Supports Typed Question Formats:**
   - `ChoiceQuestion`: Categorical classification across $N$ named criteria.
   - `NoulQuestion`: Calibrated yes/no probability scoring.
   - `ScoreQuestion`: Rating on a calibrated continuous or discrete scale.

### Strands Agents Framework Integration
ReviewPilot AI leverages core primitives from the `strands` Python SDK:
- `strands.Agent`: Coordinates model invocations, tools, and lifecycle hooks.
- `strands.tool`: Exposes CI/CD operations (`merge_pr`, `post_pr_comment`, `trigger_security_alert`).
- `strands.interventions.InterventionHandler`: Provides pre-tool execution gating (`before_tool_call`), enforcing guardrails deterministically.
- `strands.models.BedrockModel`: Manages AWS IAM authentication and streaming Bedrock interactions.

---

## The Role of Amazon Bedrock

Amazon Bedrock acts as the **System Two generative reasoner** in ReviewPilot AI:

### Supported Bedrock Models
- **Anthropic Claude 3 Haiku (`anthropic.claude-3-haiku-20240307-v1:0`):** Default high-speed generative model for AST parsing and code reviews.
- **Anthropic Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20240620-v1:0`):** High-capability model for complex multi-file architectural reasoning.
- **Amazon Nova Lite (`amazon.nova-lite-v1:0`):** Cost-effective AWS-native model for continuous review pipelines.

### Structured Generative Prompting
Bedrock is invoked with a strict JSON schema contract that converts raw diff context into actionable developer feedback:
```json
{
  "findings": [
    {
      "file": "src/auth/service.py",
      "line": 24,
      "severity": "critical",
      "message": "Hardcoded credentials or sensitive session token parameter detected in query string.",
      "suggestion": "Offload secrets to AWS Secrets Manager or KMS and use Authorization header with Bearer token."
    }
  ],
  "summary_markdown": "Full architectural audit report..."
}
```

By decoupling triage from generative review, Bedrock is called **only when necessary**, cutting aggregate token spend by over 70%.

---

## Benchmark Results: Decider 2B vs Pure Bedrock LLM

Benchmarked across 5 representative pull request workloads ([`benchmark/benchmark_comparison.py`](benchmark/benchmark_comparison.py)):

| Metric | Legacy Bedrock LLM Agent | ReviewPilot AI (Hybrid) | Improvement |
| :--- | :--- | :--- | :--- |
| **Average Triage Latency** | 2,200.0 ms | **125.2 ms** | **94.3% FASTER** |
| **Documentation PR Cost** | $0.0220 | **$0.0000** | **100% FREE** |
| **Total Test Suite Cost** | $0.1230 | **$0.0360** | **70.7% SAVINGS** |
| **Uncertainty Gating** | Silent Hallucination | **Calibrated Escalation** | **Zero Silent Failures** |

---

## Empirical Calibration Study (20 Pull Requests)

To rigorously evaluate Decider 2B's calibration, we benchmarked ReviewPilot AI across a dataset of 20 diverse pull requests ([`benchmark/evaluate_dataset.py`](benchmark/evaluate_dataset.py)):

```
================================================================================
 EMPIRICAL PERFORMANCE & CALIBRATION METRICS (20 PULL REQUESTS)
================================================================================
  • Overall Routing Accuracy    : 95.0% (19/20 pull requests correct)
  • Expected Calibration Error  : 9.15% (ECE < 10% confirms statistical calibration)
  • Median Latency (P50)        : 125.0 ms
  • 90th Percentile (P90)       : 127.0 ms
  • 99th Percentile (P99)       : 132.9 ms
--------------------------------------------------------------------------------
Category               | Precision  | Recall     | F1-Score
--------------------------------------------------------------------------------
auto_approve           | 100.0%     | 100.0%     | 1.000
security_escalation    | 100.0%     | 100.0%     | 1.000
breaking_change        | 100.0%     | 75.0%      | 0.857
standard_review        | 87.5%      | 100.0%     | 0.933
================================================================================
```

Both ambiguous, high-churn refactors (PR-17 and PR-18) accurately registered low confidence (58%), deterministically triggering the human escalation path.

---

## The Reusable Decision Pattern (`#policy`)

The primary hackathon pattern is implemented in [`decision_patterns/policy_gatekeeper.py`](decision_patterns/policy_gatekeeper.py). It provides a self-contained contract for evaluating pull requests:

### 1. Typed Question
```python
QUESTION = "Which triage policy category best classifies this pull request code change?"
```

### 2. Allowed Options
- `auto_approve`: Non-functional documentation, formatting, comments, or trivial typo fixes.
- `standard_review`: Standard application logic, bugfixes, and feature additions.
- `security_escalation`: Modifications to auth, secrets, crypto keys, session tokens, or raw SQL queries.
- `breaking_change`: Modifications to public API endpoints, database schemas, or serialization contracts.

### 3. Quick Reuse in Your Own Agent
```python
from decision_patterns.policy_gatekeeper import PolicyGatekeeperPattern
from reviewpilot.models import PRPayload

# Initialize gatekeeper with calibrated confidence threshold
gatekeeper = PolicyGatekeeperPattern(confidence_threshold=0.80)

# Evaluate decision
verdict = gatekeeper.evaluate(pr_payload)

print(f"Action: {verdict.action}")               # e.g., RoutingAction.SECURITY_ESCALATION
print(f"Confidence: {verdict.confidence:.2f}")    # e.g., 0.94
print(f"Escalated to Human: {verdict.escalated_to_human}")
```

See [`docs/reusable_pattern_guide.md`](docs/reusable_pattern_guide.md) for full instructions and adaptation to other domains.

---

## Installation & Quickstart

### Prerequisites
- Python 3.11, 3.12, or 3.14
- AWS Account with Bedrock model access (optional; built-in calibrated simulator is included for offline testing)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment (Optional)
```bash
cp .env.example .env
# Edit .env with your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY if testing live Bedrock models
```

### Step 3: Run the Test Suite
```bash
pytest tests/ -v
# 21 unit tests covering policy triage, threshold boundaries, guardrails, and orchestration
```

### Step 4: Launch the Web Dashboard
```bash
streamlit run app.py
```
*Open your browser at `http://localhost:8501` to test sample PRs, adjust confidence thresholds, view probability distributions, and inspect Bedrock code reviews.*

### Step 5: Test via Command Line Interface (CLI)
```bash
# Test fast-track auto-approve documentation fix:
python cli.py --sample doc_typo

# Test security escalation with Amazon Bedrock audit:
python cli.py --sample auth_security

# Test uncertainty escalation (low confidence triggers human review):
python cli.py --sample ambiguous

# Test a custom PR JSON file:
python cli.py --file examples/03_db_migration.json --threshold 0.85
```

### Step 6: Run Quantitative Benchmarks
```bash
# Comparative latency and cost benchmark:
python benchmark/benchmark_comparison.py

# 20-PR statistical calibration evaluation:
python benchmark/evaluate_dataset.py
```

### Step 7: (Optional) Launch Local Strands Decider 2B Server
If you have a local GPU or want to run the real Decider 2B model weights:
```bash
strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8000
```
ReviewPilot AI automatically detects port 8000 when active!

---

## Repository Structure

```
ReviewPilot AI/
├── README.md                           # Project documentation & benchmark report
├── LICENSE                             # MIT Open Source License
├── requirements.txt                    # Pinned dependencies
├── .env.example                        # Configuration template (no secrets)
├── .gitignore                          # Clean repository ignores
├── app.py                              # Streamlit interactive web dashboard
├── cli.py                              # Developer & CI/CD CLI runner
├── decision_patterns/                  # Reusable Decider 2B Decision Patterns
│   ├── __init__.py
│   ├── policy_gatekeeper.py            # Primary Pattern: #policy (PR Triage & Gating)
│   └── guardrails_intervention.py      # Secondary Pattern: #guardrails (Tool Interventions)
├── reviewpilot/                        # Core Agent Engine
│   ├── __init__.py
│   ├── agent.py                        # Hybrid Strands Agent orchestrating Decider + Bedrock
│   ├── decider_client.py               # Strands Decider 2B System One client & simulator
│   ├── bedrock_reviewer.py             # Amazon Bedrock generative reviewer
│   └── models.py                       # Pydantic data schemas
├── examples/                           # Realistic sample pull requests
│   ├── sample_prs.json                 # Collection of all 5 PR scenarios
│   ├── evaluation_dataset.json         # 20 labeled pull request evaluation workloads
│   ├── 01_doc_typo_fix.json            # Auto-approve candidate
│   ├── 02_feature_auth_oauth.json      # Security escalation candidate
│   ├── 03_db_migration.json            # Breaking change candidate
│   ├── 04_ambiguous_refactor.json      # Low-confidence human escalation candidate
│   └── 05_standard_bugfix.json         # Standard review candidate
├── tests/                              # Comprehensive test suite (21 tests)
│   ├── __init__.py
│   ├── test_decision_patterns.py       # Pattern and threshold unit tests
│   ├── test_decider_client.py          # Client and schema validation tests
│   └── test_agent_orchestration.py     # End-to-end orchestration tests
├── docs/                               # Hackathon Submission Documentation
│   ├── architecture.md                 # System architecture & Mermaid flowcharts
│   ├── builder_center_article.md       # AWS Builder Center publication article
│   ├── demo_video_script.md            # Timestamped demo video script (< 3 min)
│   └── reusable_pattern_guide.md       # Developer reuse guide
└── benchmark/                          # Quantitative Performance Benchmarking
    ├── benchmark_comparison.py         # Measures 94.3% latency reduction & 70.7% savings
    └── evaluate_dataset.py             # 20-PR empirical accuracy and calibration study
```

---

## Hackathon Submission Metadata
- **Project Name:** ReviewPilot AI
- **Repository:** [https://github.com/Saifan-01/ReviewPilot-AI](https://github.com/Saifan-01/ReviewPilot-AI)
- **Primary Hackathon Tag:** `#strands-decider-2b`
- **Pattern Tags:** `#policy` (Primary), `#guardrails` (Secondary)
- **Model Pairing:** AWS Strands Decider 2B + Amazon Bedrock (Claude 3 Haiku / 3.5 Sonnet)
- **Submission Article:** [`docs/builder_center_article.md`](docs/builder_center_article.md)
- **Demo Script:** [`docs/demo_video_script.md`](docs/demo_video_script.md)
- **Open Source License:** [MIT License](LICENSE)
- **Author:** [Saifan-01](https://github.com/Saifan-01)
