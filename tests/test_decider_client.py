"""Unit tests for DeciderClient and System One schema interfacing."""

import pytest
from reviewpilot.decider_client import DeciderClient, POLICY_CRITERIA, POLICY_QUESTION
from reviewpilot.models import PRPayload, TriageCategory


@pytest.fixture
def sample_payload():
    return PRPayload(
        id="PR-999",
        title="fix(api): fix null pointer exception in auth header parser",
        description="Handles cases where Authorization header is absent",
        author="alice",
        target_branch="main",
        files_changed=["src/api/auth.py"],
        additions=12,
        deletions=4,
        diff_content="""--- a/src/api/auth.py
+++ b/src/api/auth.py
@@ -10,3 +10,6 @@
 def parse_auth(headers):
+    if not headers.get('Authorization'):
+        return None
     return headers['Authorization'].split(' ')[1]
""",
    )


class TestDeciderClient:
    def test_state_representation_construction(self, sample_payload):
        client = DeciderClient()
        state = client._build_state_representation(sample_payload)
        assert "PR-999" in state
        assert "fix(api): fix null pointer exception" in state
        assert "src/api/auth.py" in state
        assert "Unified Diff Snippet:" in state

    def test_simulated_security_detection(self):
        client = DeciderClient()
        pr = PRPayload(
            id="PR-SEC",
            title="feat: add password hashing with bcrypt",
            author="bob",
            files_changed=["auth/crypto.py"],
            additions=30,
            deletions=5,
            diff_content="+ def hash_password(password: str):\n+    return bcrypt.hashpw(password.encode())",
        )
        decision = client.evaluate_triage_policy(pr)
        assert decision.category == TriageCategory.SECURITY_ESCALATION.value
        assert decision.confidence >= 0.90
        assert decision.latency_ms > 0

    def test_simulated_auto_approve_detection(self):
        client = DeciderClient()
        pr = PRPayload(
            id="PR-DOCS",
            title="docs: update contributor readme",
            author="carol",
            files_changed=["README.md"],
            additions=2,
            deletions=1,
            diff_content="- old instructions\n+ new instructions",
        )
        decision = client.evaluate_triage_policy(pr)
        assert decision.category == TriageCategory.AUTO_APPROVE.value
        assert decision.confidence >= 0.90

    def test_simulated_ambiguous_escalation(self):
        client = DeciderClient()
        pr = PRPayload(
            id="PR-AMB",
            title="refactor: massive reorganization and untested WIP cleanup across core modules",
            author="intern",
            files_changed=[f"file_{i}.py" for i in range(20)],
            additions=1500,
            deletions=1200,
            diff_content="churn across 20 files with untested code",
        )
        decision = client.evaluate_triage_policy(pr)
        # Ambiguous change must have lower confidence
        assert decision.confidence < 0.75

    def test_parse_response_success(self):
        client = DeciderClient()
        mock_raw = {
            "model": "StrandsAgents/strands-decider-2B",
            "answers": [
                {
                    "type": "choice",
                    "choice": "security_escalation",
                    "confidence": 0.942,
                    "probabilities": {"security_escalation": 0.942, "standard_review": 0.058},
                }
            ],
            "latency_ms": 112.4,
        }
        dec = client._parse_response(mock_raw, latency_ms=115.0)
        assert dec.category == "security_escalation"
        assert dec.confidence == 0.942
        assert dec.latency_ms == 112.4

    def test_parse_response_malformed_raises(self):
        client = DeciderClient()
        with pytest.raises(ValueError, match="missing answers"):
            client._parse_response({"answers": []}, latency_ms=10.0)
