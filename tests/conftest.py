"""Small deterministic fixtures; no credentials or benchmark ground truth."""

import copy
import pytest


@pytest.fixture
def attack_bundle():
    """Hand-authored STIX subset for parser contracts, not retrieval quality."""
    technique = {
        "type": "attack-pattern", "id": "attack-pattern--password",
        "name": "Password Guessing", "description": "Repeated SSH password attempts.",
        "external_references": [{"source_name": "other", "external_id": "ignore"},
                                {"source_name": "mitre-attack", "external_id": "T1110.001"}],
        "kill_chain_phases": [{"kill_chain_name": "mitre-attack", "phase_name": "credential-access"}],
        "x_mitre_platforms": ["Linux"],
    }
    mitigation = {"type": "course-of-action", "id": "course-of-action--mfa",
                  "name": "Multi-factor Authentication",
                  "external_references": [{"source_name": "mitre-attack", "external_id": "M1032"}]}
    relation = {"type": "relationship", "id": "relationship--mfa", "relationship_type": "mitigates",
                "source_ref": mitigation["id"], "target_ref": technique["id"]}
    return {"type": "bundle", "objects": [technique, mitigation, relation]}


@pytest.fixture
def techniques(attack_bundle):
    return {
        "T1110.001": {"id": "T1110.001", "name": "Password Guessing", "description": "SSH passwords",
                      "tactics": ["credential-access"], "platforms": ["Linux"]},
        "T1046": {"id": "T1046", "name": "Network Service Discovery", "description": "Port scan",
                  "tactics": ["discovery"], "platforms": ["Linux"]},
        "T1190": {"id": "T1190", "name": "Exploit Public-Facing Application", "description": "Web SQL injection",
                  "tactics": ["initial-access"], "platforms": ["Linux"]},
    }


@pytest.fixture
def fake_encoder():
    """Known vectors exercise normalization; they do not model semantic quality."""
    def encode(texts):
        vectors = []
        for text in texts:
            if text.startswith("T1110.001 ") or text == "ssh":
                vectors.append([1.0, 0.0, 0.0])
            elif text.startswith("T1046 ") or text == "scan":
                vectors.append([0.0, 10.0, 0.0])
            else:
                vectors.append([100.0, 100.0, 0.0])
        return vectors
    return encode
