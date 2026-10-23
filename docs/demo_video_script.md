# ReviewPilot AI: Demo Video Script (< 3 Minutes)

> **Total Target Duration:** 2 minutes 30 seconds  
> **Hard Limit:** 3 minutes 00 seconds  
> **Platform Target:** YouTube / Vimeo (Public Link)  
> **Submission Tags:** `#strands-decider-2b` `#policy`

---

## Storyboard & Timestamp Breakdown

| Timestamp | Screen Visual | Voiceover Audio | Key Highlight |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:20** | Title slide: **ReviewPilot AI** logo, then switch to messy GitHub PR list with dozens of pending reviews. | *"Every day, software engineering teams waste valuable time and cloud budget waiting for heavy AI review bots to inspect simple documentation typos—or worse, relying on uncalibrated LLMs that hallucinate safe verdicts on security-sensitive code. Welcome to **ReviewPilot AI**, an uncertainty-aware code review gatekeeper powered by AWS Strands Decider 2B and Amazon Bedrock."* | Problem & Audience Hook |
| **0:20 – 0:50** | Screen recording of the **Streamlit Dashboard** (`app.py`). Select **Sample 1: Docs Typo Fix**. Click **Evaluate Pull Request**. | *"Here is our web dashboard. First, let's test a simple documentation typo fix. When we submit this PR, ReviewPilot hands the policy decision to Strands Decider 2B. Look at that: in just 124 milliseconds, Decider 2B classifies this as `auto_approve` with 96% calibrated confidence. Because this is purely non-functional, the agent fast-tracks approval and completely bypasses the expensive generative LLM, costing zero dollars."* | Fast-track auto-approve (124ms, $0.00) |
| **0:50 – 1:30** | Select **Sample 2: OAuth & JWT Auth**. Click **Evaluate Pull Request**. Show the probability distribution bar chart and the Bedrock findings appearing. | *"Now let's test a high-risk change: an OAuth2 session handler. Immediately, Decider 2B flags this as `security_escalation` with 94% confidence. Because it’s high risk, the agent calls Amazon Bedrock Claude 3 Haiku for deep analysis. Bedrock performs an automated DevSecOps audit, pinpointing a hardcoded token parameter at line 24 and recommending AWS Secrets Manager remediation."* | Security triage + Bedrock deep audit |
| **1:30 – 1:55** | Select **Sample 4: Untested WIP Churn**. Click **Evaluate Pull Request**. Red banner appears: **🚨 HUMAN ESCALATION REQUIRED**. | *"Now watch what happens when an ambiguous, untested multi-file refactor is submitted. A typical LLM would guess or hallucinate. But Decider 2B returns a calibrated confidence of only 58%, falling below our 80% safety threshold! ReviewPilot halts autonomous tools and immediately escalates the PR to the engineering lead queue. Zero silent failures."* | Calibrated uncertainty & human escalation |
| **1:55 – 2:15** | Split screen showing `decision_patterns/policy_gatekeeper.py` and benchmark terminal output (`python benchmark/benchmark_comparison.py`). | *"Our project demonstrates the official `#policy` pattern, and we’ve packaged it as a reusable, open-source module that any agent builder can drop into their own pipeline. In our quantitative benchmarks across diverse PRs, offloading triage to Decider 2B made routing 94% faster and reduced overall cloud evaluation costs by 70.7%."* | Reusable pattern + benchmark results |
| **2:15 – 2:30** | GitHub repository page (https://github.com/Saifan-01/ReviewPilot-AI) showing MIT License, 21 passing unit tests, and Builder Center article link. | *"All source code, 21 passing unit tests, documentation, and the full Builder Center article are public on our GitHub repository at github.com/Saifan-01/ReviewPilot-AI. Thank you for watching, and see you on the AWS Builder Center!"* | Call to action & submission links |

---

## Recording Tips for the Presenter:
1. **Screen Resolution:** Record at 1080p (1920x1080) at 60fps using OBS Studio or Windows Game Bar (`Win + G`).
2. **Audio:** Use a clean USB microphone or headset.
3. **Execution Command:** Have the dashboard running locally before you start:
   ```bash
   streamlit run app.py
   ```
4. **Pacing:** Keep energy crisp and concise. Don't rush, but don't pause unnecessarily between clicks.
