"""T-SCHEMA: structured output limits and rejection of malformed contracts."""
import pytest
from pydantic import ValidationError
from cyberagents.schemas import Finding, Incident, TechniqueChoice


def test_finding_requires_known_verdict_and_bounded_evidence():
    base = dict(finding_id='f1', cluster_ids=['c1'], verdict='malicious', summary='SSH failures',
                evidence_line_ids=['auth:1'], src_ips=[], users=[], hosts=[], reasoning='Repeated failures')
    assert Finding(**base).verdict == 'malicious'
    with pytest.raises(ValidationError):
        Finding(**{**base, 'verdict': 'maybe'})
    with pytest.raises(ValidationError):
        Finding(**{**base, 'evidence_line_ids': ['x'] * 11})
    with pytest.raises(ValidationError):
        Finding(**base, hidden_label='A1')


def test_confidence_and_technique_id_shape_are_validated():
    with pytest.raises(ValidationError):
        TechniqueChoice(technique_id='not-an-id', name='x', tactic='discovery', is_primary=True, justification='x')
    with pytest.raises(ValidationError):
        Incident(incident_id='i1', finding_ids=['f1'], title='x', severity='high', confidence=1.1,
                 attacker_ips=[], affected_assets=[], kill_chain=[], rationale='x')


def test_chain_timestamp_must_have_a_timezone():
    from cyberagents.schemas import KillChainStep
    with pytest.raises(ValidationError):
        KillChainStep(order=1, ts_utc='tomorrow', finding_id='f1', technique_id='T1046', description='scan')
    with pytest.raises(ValidationError):
        KillChainStep(order=1, ts_utc='2026-10-17T01:00:00', finding_id='f1', technique_id='T1046', description='scan')
