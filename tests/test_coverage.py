"""Revision regression contracts: no silent omission or unrelated correlation."""
import copy
import pytest
from cyberagents import validators


def case():
    clusters, findings, mappings, incidents = [], [], [], []
    for n in range(3):
        cid, fid, line = f'c{n}', f'f{n}', f'auth:{n}'
        clusters.append(dict(cluster_id=cid, all_line_ids=[line],
            sample_lines=[dict(event_id=line)], src_ips=[f'203.0.113.{n+10}'],
            users=['deploy'], hosts=['ssh-srv'], t_start='2026-10-17T00:00:00Z',
            t_end='2026-10-17T00:01:00Z'))
        findings.append(dict(finding_id=fid, cluster_ids=[cid], evidence_line_ids=[line],
                             verdict='benign' if n == 2 else 'malicious', status='validated'))
        if n < 2:
            mappings.append(dict(finding_id=fid, status='validated', techniques=[dict(technique_id='T1110.001')]))
            incidents.append(dict(incident_id=f'i{n}', finding_ids=[fid],
                kill_chain=[dict(finding_id=fid, technique_id='T1110.001')]))
    return clusters, findings, mappings, incidents


def check(stage, items, context=None):
    clusters, findings, mappings, incidents = context or case()
    return validators.validate_stage_coverage(stage, items, clusters=clusters, findings=findings,
        mappings=mappings, incidents=incidents, inventory={'internal_network': '10.0.0.0/24'})


@pytest.mark.parametrize('stage', ['findings', 'mappings', 'incidents', 'plans'])
def test_empty_stage_cannot_discard_nonempty_inputs(stage):
    assert check(stage, [])


def test_complete_independent_attacks_and_benign_dismissal_pass():
    clusters, findings, mappings, incidents = case()
    assert check('findings', findings) == []
    assert check('mappings', mappings) == []
    assert check('incidents', incidents) == []
    assert check('plans', [dict(incident_id='i0'), dict(incident_id='i1')]) == []


def test_partial_incident_list_reports_the_missing_finding():
    errors = check('incidents', case()[3][:1])
    assert any('f1' in error and 'missing' in error.lower() for error in errors)


def test_every_referenced_cluster_needs_its_own_evidence():
    _, findings, _, _ = case()
    findings[0]['cluster_ids'].append('c1')
    errors = check('findings', findings)
    assert any('c1' in error and 'evidence' in error.lower() for error in errors)


def test_one_finding_cannot_collapse_distinct_clusters():
    _, findings, _, _ = case()
    findings[0]['cluster_ids'].append('c1')
    findings[0]['evidence_line_ids'].append('auth:1')
    assert any('one cluster' in error.lower() for error in check('findings', findings))


def test_unrelated_external_actors_cannot_be_hidden_in_one_incident():
    incident = dict(incident_id='merged', finding_ids=['f0', 'f1'], kill_chain=[
        dict(finding_id='f0'), dict(finding_id='f1')])
    assert any('actor' in error.lower() for error in check('incidents', [incident]))


def test_same_actor_chain_can_be_one_incident():
    context = case()
    context[0][1]['src_ips'] = context[0][0]['src_ips']
    incident = dict(incident_id='chain', finding_ids=['f0', 'f1'], kill_chain=[
        dict(finding_id='f0'), dict(finding_id='f1')])
    assert check('incidents', [incident], context) == []


def test_shared_actor_hours_apart_does_not_imply_one_incident():
    context = case()
    context[0][1].update(src_ips=context[0][0]['src_ips'],
                          t_start='2026-10-17T08:00:00Z', t_end='2026-10-17T08:01:00Z')
    incident = dict(incident_id='merged', finding_ids=['f0', 'f1'], kill_chain=[
        dict(finding_id='f0'), dict(finding_id='f1')])
    assert any('time' in error.lower() for error in check('incidents', [incident], context))


def test_duplicate_assignment_and_missing_kill_chain_step_are_rejected():
    incidents = case()[3]
    incidents.append(copy.deepcopy(incidents[0]))
    assert any('multiple' in error.lower() for error in check('incidents', incidents))
    incidents = case()[3]
    incidents[0]['kill_chain'] = []
    assert any('step' in error.lower() for error in check('incidents', incidents))


def agent_case(techniques, fake_encoder):
    from cyberagents.rag import AttackRAG
    clusters, findings, mappings, incidents = case()
    for cluster, finding in zip(clusters, findings):
        cluster.update(rule_ids=['R-AUTH-FAIL'], line_count=1)
        cluster['sample_lines'][0].update(raw='Failed password', ts_utc=cluster['t_start'])
        finding.update(summary='ssh', reasoning='Password attempts',
                       src_ips=cluster['src_ips'], users=cluster['users'], hosts=cluster['hosts'])
    for mapping in mappings:
        mapping.update(mapping_confidence=.9)
        mapping['techniques'][0].update(name='Password Guessing', tactic='credential-access',
                                       is_primary=True, justification='Repeated failed passwords')
    for incident in incidents:
        incident.update(title='SSH attack', severity='high', confidence=.9,
            attacker_ips=[], affected_assets=['ssh-srv'], rationale='Independent malicious activity')
        incident['kill_chain'][0].update(order=1, ts_utc='2026-10-17T00:00:00Z', description='Password attempts')
    plans = [dict(incident_id=item['incident_id'], executive_summary='Review attack',
                  immediate_actions=[], mitigations=[], investigation_steps=['Review logs'], prevention=['MFA'])
             for item in incidents]
    rag = AttackRAG(techniques, encoder=fake_encoder, source_ref='fixture')
    return clusters, rag, {'techniques': techniques, 'mitigations': {}}, dict(
        findings=findings, mappings=mappings, incidents=incidents, plans=plans)


@pytest.mark.parametrize('omitted_stage', ['findings', 'mappings', 'incidents', 'plans'])
def test_agent_retries_partial_stage_and_preserves_independent_attacks(techniques, fake_encoder, omitted_stage):
    from cyberagents.agents import run_agents
    clusters, rag, kb, stages = agent_case(techniques, fake_encoder)
    calls = []
    def runner(stage, schema, prompt, inputs, tools):
        calls.append(stage)
        if stage == omitted_stage and calls.count(stage) == 1:
            return {stage: copy.deepcopy(stages[stage][:1])}
        if stage == omitted_stage:
            assert 'missing required inputs' in prompt
        return {stage: copy.deepcopy(stages[stage])}
    output = run_agents(clusters, {'internal_network': '10.0.0.0/24'}, kb, rag,
                        client=None, seed=42, task_runner=runner)
    assert calls.count(omitted_stage) == 2
    assert output['coverage']['complete']
    assert {fid for item in output['incidents'] for fid in item['finding_ids']} == {'f0', 'f1'}
    assert all('f2' not in item['finding_ids'] for item in output['incidents'])


def test_exhausted_incident_retry_is_explicitly_incomplete_and_never_fabricated(techniques, fake_encoder):
    from cyberagents.agents import run_agents
    clusters, rag, kb, stages = agent_case(techniques, fake_encoder)
    def runner(stage, schema, prompt, inputs, tools):
        return {stage: copy.deepcopy(stages[stage][:1] if stage in {'incidents', 'plans'} else stages[stage])}
    output = run_agents(clusters, {'internal_network': '10.0.0.0/24'}, kb, rag,
                        client=None, seed=42, task_runner=runner)
    assert not output['coverage']['complete']
    assert any('f1' in error for error in output['coverage']['unresolved']['incidents'])
    assert all('f1' not in item['finding_ids'] for item in output['incidents'])


def test_revised_development_cannot_overwrite_a_frozen_output_directory(tmp_path, monkeypatch):
    import json
    from cyberagents import pipeline
    (tmp_path / 'system_freeze.json').write_text(json.dumps({'source_hash': 'old'}))
    monkeypatch.setattr(pipeline, 'source_hash', lambda: 'new')
    with pytest.raises(RuntimeError, match='separate output_dir'):
        pipeline._seed_allowed(42, tmp_path, force=True)


def test_successful_login_query_uses_cited_event_not_prior_brute_force():
    from cyberagents import agents
    cluster = dict(cluster_id='auth', sample_lines=[dict(event_id='auth:1', raw=
        'Oct 17 02:14:07 ssh-srv sshd[4123]: Accepted password for deploy from 203.0.113.10 port 51522 ssh2')])
    finding = dict(cluster_ids=['auth'], evidence_line_ids=['auth:1'],
        summary='Successful authentication after brute force', reasoning='Password guessing preceded session')
    query = agents._finding_query(finding, [cluster])
    assert 'SSH' in query and 'valid' in query and 'brute' not in query.lower()
    assert 'T1078' not in query  # Retrieval searches text; it never returns a hard-coded ID.


def test_invalid_mapping_does_not_invalidate_other_valid_mappings(techniques, fake_encoder):
    from cyberagents.agents import _strip_invalid
    clusters, rag, kb, stages = agent_case(techniques, fake_encoder)
    rag.retrieval_log = {'f0': {'T1110.001'}, 'f1': {'T1110.001'}}
    data = copy.deepcopy(stages['mappings'])
    data[1]['techniques'][0]['technique_id'] = 'T9999'
    result = _strip_invalid('mappings', {'mappings': data}, stages, clusters, kb, rag)
    assert result[0]['status'] == 'validated'
    assert result[1]['status'] == 'unvalidated'


def test_salvage_keeps_a_valid_external_to_internal_chain(techniques, fake_encoder):
    from cyberagents.agents import _strip_invalid
    clusters, rag, kb, stages = agent_case(techniques, fake_encoder)
    clusters[1]['src_ips'] = ['10.0.0.10']
    merged = copy.deepcopy(stages['incidents'][0])
    merged['finding_ids'].append('f1')
    merged['kill_chain'].append(copy.deepcopy(stages['incidents'][1]['kill_chain'][0]))
    result = _strip_invalid('incidents', {'incidents': [merged]}, stages, clusters, kb, rag,
                            inventory={'internal_network': '10.0.0.0/24'})
    assert result[0]['status'] == 'validated'
