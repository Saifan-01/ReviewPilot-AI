# 🛡️ ReviewPilot AI
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

## 📌 Submission Overview

ReviewPilot AI is an original AI agent developed for the **AWS Strands Decider 2B Challenge**. It introduces a two-tier cognitive architecture:
- **System One (Fast & Instinctive):** **AWS Strands Decider 2B** acts as a local ~115ms decision gatekeeper (\$0 marginal token cost) evaluating pull requests against strict organizational policies with mathematically calibrated confidence numbers.
- **System Two (Deliberative & Generative):** **Amazon Bedrock** (Anthropic Claude 3 Haiku / 3.5 Sonnet) is invoked selectively for deep code analysis, AST syntax verification, and DevSecOps remediation only when changes require generative reasoning.

### Submission Deliverables Checklist
- [x] **Working Agent:** Hybrid Strands Agent combining Decider 2B and Amazon Bedrock.
- [x] **Demonstrated Decision Pattern:** **`#policy`** (Primary) and **`#guardrails`** (Secondary).
- [x] **Reusable Decision Pattern:** Self-contained module in [`decision_patterns/policy_gatekeeper.py`](decision_patterns/policy_gatekeeper.py).
- [x] **Open Source Public Repository:** OSI-approved [MIT License](LICENSE), setup instructions, configuration templates, and 21 unit tests.
- [x] **Builder Center Article:** Comprehensive technical deep-dive in [`docs/builder_center_article.md`](docs/builder_center_article.md).
- [x] **Demo Video (< 3 min):** Exact timestamped storyboard and script in [`docs/demo_video_script.md`](docs/demo_video_script.md).
- [x] **Quantitative Measurement:** 94.3% triage latency reduction and 70.7% cloud cost savings benchmarked in [`benchmark/benchmark_comparison.py`](benchmark/benchmark_comparison.py).

---

## 🚀 Key Innovations & Architecture

```
[Developer Submits Pull Request]
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

1. **⚡ Fast-Track Auto-Approve:** Non-functional PRs (documentation, typos, comments) bypass the heavy generative LLM entirely, cutting review time to **125ms** and costing **$0.00**.
2. **🛑 Uncertainty-Aware Human Escalation:** Unlike traditional LLMs that hallucinate confident approvals, if Decider 2B's calibrated confidence drops below threshold ($\tau = 0.80$), ReviewPilot AI **blocks automated actions and escalates directly to engineering leads**.
3. **🛡️ Tool-Call Intervention Guardrails:** Uses Strands Agents SDK's native `InterventionHandler` to intercept destructive tool calls (like `merge_pr` or `delete_branch`) and verify repository guardrails via Decider 2B.

---

## 📊 Benchmark Results: Decider 2B vs Pure Bedrock LLM

Benchmarked across 5 representative pull request workloads ([`benchmark/benchmark_comparison.py`](benchmark/benchmark_comparison.py)):

| Metric | Legacy Bedrock LLM Agent | ReviewPilot AI (Hybrid) | Improvement |
| :--- | :--- | :--- | :--- |
| **Average Triage Latency** | 2,200.0 ms | **125.2 ms** | **94.3% FASTER** 🚀 |
| **Documentation PR Cost** | \$0.0220 | **\$0.0000** | **100% FREE** |
| **Total Test Suite Cost** | \$0.1230 | **\$0.0360** | **70.7% SAVINGS** 💰 |
| **Uncertainty Gating** | Silent Hallucination | **Calibrated Escalation** | **Zero Silent Failures** |

---

## 🧩 The Reusable Decision Pattern (`#policy`)

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

gatekeeper = PolicyGatekeeperPattern(confidence_threshold=0.80)
verdict = gatekeeper.evaluate(pr_payload)

print(f"Action: {verdict.action}")               # e.g., RoutingAction.SECURITY_ESCALATION
print(f"Confidence: {verdict.confidence:.2f}")    # e.g., 0.94
```

See [`docs/reusable_pattern_guide.md`](docs/reusable_pattern_guide.md) for full instructions and adaptation to other domains.

---

## 🛠️ Installation & Quickstart

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

### Step 4: Launch the Streamlit Interactive Dashboard
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

### Step 6: Run Quantitative Benchmark
```bash
python benchmark/benchmark_comparison.py
```

### Step 7: (Optional) Launch Local Strands Decider 2B Server
If you have a local GPU or want to run the real Decider 2B model weights:
```bash
strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8000
```
ReviewPilot AI automatically detects port 8000 when active!

---

## 📁 Repository Structure

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
    └── benchmark_comparison.py         # Measures 94.3% latency reduction & 70.7% savings
```

---

## 🏆 Hackathon Submission Metadata
- **Project Name:** ReviewPilot AI
- **Repository:** [https://github.com/Saifan-01/ReviewPilot-AI](https://github.com/Saifan-01/ReviewPilot-AI)
- **Primary Hackathon Tag:** `#strands-decider-2b`
- **Pattern Tags:** `#policy` (Primary), `#guardrails` (Secondary)
- **Model Pairing:** AWS Strands Decider 2B + Amazon Bedrock (Claude 3 Haiku / 3.5 Sonnet)
- **Submission Article:** [`docs/builder_center_article.md`](docs/builder_center_article.md)
- **Demo Script:** [`docs/demo_video_script.md`](docs/demo_video_script.md)
- **Open Source License:** [MIT License](LICENSE)
- **Author:** [Saifan-01](https://github.com/Saifan-01)
