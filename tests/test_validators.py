"""T-VALID: catalog membership, retrieval isolation and evidence ownership."""
from cyberagents.validators import validate_findings, validate_mappings, validate_incidents, validate_plans


def test_evidence_must_belong_to_the_named_cluster():
    clusters = [{'cluster_id': 'c1', 'all_line_ids': ['auth:1']},
                {'cluster_id': 'c2', 'all_line_ids': ['auth:2']}]
    finding = {'finding_id': 'f1', 'cluster_ids': ['c1'], 'evidence_line_ids': ['auth:2'], 'verdict': 'malicious'}
    assert validate_findings([finding], clusters)
    finding['evidence_line_ids'] = ['auth:1']
    assert validate_findings([finding], clusters) == []


def test_existing_but_unretrieved_technique_is_rejected(techniques):
    mapping = {'finding_id': 'f1', 'techniques': [{'technique_id': 'T1046', 'name': 'Network Service Discovery',
               'tactic': 'discovery', 'is_primary': True, 'justification': 'ports'}]}
    kb = {'techniques': techniques, 'mitigations': {}}
    assert validate_mappings([mapping], [{'finding_id': 'f1'}], kb, {'f1': ['T1110.001']})
    assert validate_mappings([mapping], [{'finding_id': 'f1'}], kb, {'f1': ['T1046']}) == []


def test_incident_cannot_use_another_findings_technique():
    incident = {'incident_id': 'i1', 'finding_ids': ['f1'], 'kill_chain': [
        {'finding_id': 'f1', 'technique_id': 'T1046'}]}
    findings = [{'finding_id': 'f1', 'verdict': 'malicious'}]
    mappings = [{'finding_id': 'f1', 'techniques': [{'technique_id': 'T1110.001'}]}]
    assert validate_incidents([incident], findings, mappings)


def test_mitigation_must_link_to_a_technique_in_its_incident():
    plans = [{'incident_id': 'i1', 'mitigations': [{'mitigation_id': 'M1032', 'for_technique_id': 'T1110.001'}]}]
    kb = {'techniques': {}, 'mitigations': {'T1110.001': [{'id': 'M1032', 'name': 'MFA'}]}}
    incidents = [{'incident_id': 'i1', 'kill_chain': [{'technique_id': 'T1046'}]}]
    assert validate_plans(plans, incidents, kb)
    incidents[0]['kill_chain'][0]['technique_id'] = 'T1110.001'
    assert validate_plans(plans, incidents, kb) == []
