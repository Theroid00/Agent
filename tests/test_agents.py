"""T-AGENT: disk cache, retry bounds, validated stage hand-offs and tool isolation."""
import json
import pytest
from cyberagents.llm import CachedLLM
from cyberagents.agents import run_agents
from cyberagents.rag import AttackRAG


def test_response_cache_survives_a_new_client(tmp_path):
    calls = []
    def transport(prompt, inputs):
        calls.append(inputs)
        return '{"ok":true}', 17
    first = CachedLLM(cache_dir=tmp_path, transport=transport, min_interval=0)
    assert first.json_call('test', {'x': 1}) == {'ok': True}
    second = CachedLLM(cache_dir=tmp_path, transport=transport, min_interval=0)
    assert second.json_call('test', {'x': 1}) == {'ok': True}
    assert len(calls) == 1 and second.calls == 0 and second.cache_hits == 1
    second.json_call('changed prompt', {'x': 1})
    second.json_call('test', {'x': 2})
    assert len(calls) == 3


def test_rate_limits_retry_boundedly_without_switching_provider(tmp_path, monkeypatch):
    class RateLimited(Exception):
        status_code = 429
    attempts = []
    def transport(prompt, inputs):
        attempts.append(1)
        raise RateLimited('quota')
    monkeypatch.setattr('cyberagents.llm.time.sleep', lambda _: None)
    client = CachedLLM(cache_dir=tmp_path, transport=transport, min_interval=0)
    with pytest.raises(RuntimeError, match='rate limit'):
        client.text_call('x', {})
    assert len(attempts) == 3
    assert client.provider == 'gemini'


def test_non_rate_limit_errors_are_not_retried(tmp_path):
    def transport(prompt, inputs):
        raise ValueError('malformed request')
    client = CachedLLM(cache_dir=tmp_path, transport=transport, min_interval=0)
    with pytest.raises(ValueError, match='malformed request'):
        client.text_call('x', {})
    assert client.calls == 1


def run_context(techniques, fake_encoder):
    cluster = {'cluster_id': 'c1', 'rule_ids': ['R-AUTH-FAIL'], 'all_line_ids': ['auth:1'],
               'sample_lines': [{'event_id': 'auth:1', 'raw': 'Failed password', 'ts_utc': '2026-10-17T00:00:00Z'}],
               'src_ips': ['203.0.113.10'], 'users': ['deploy'], 'hosts': ['ssh-srv'],
               't_start': '2026-10-17T00:00:00Z', 't_end': '2026-10-17T00:00:00Z', 'line_count': 1}
    rag = AttackRAG(techniques, encoder=fake_encoder, source_ref='fixture')
    kb = {'techniques': techniques, 'mitigations': {'T1110.001': [{'id': 'M1032', 'name': 'Multi-factor Authentication'}]}}
    finding = {'finding_id': 'f1', 'cluster_ids': ['c1'], 'verdict': 'malicious', 'summary': 'ssh',
               'evidence_line_ids': ['auth:1'], 'src_ips': ['203.0.113.10'], 'users': ['deploy'],
               'hosts': ['ssh-srv'], 'reasoning': 'Repeated failures'}
    return cluster, rag, kb, finding


def test_invalid_evidence_retries_once_then_strips_and_marks(techniques, fake_encoder, tmp_path):
    cluster, rag, kb, finding = run_context(techniques, fake_encoder)
    seen = []
    def runner(stage, schema, prompt, inputs, tools):
        seen.append((stage, inputs))
        if stage == 'findings':
            assert 'all_line_ids' not in json.dumps(inputs)
            return {'findings': [{**finding, 'evidence_line_ids': ['auth:does-not-exist']}]}
        return {stage: []}
    output = run_agents([cluster], {}, kb, rag, client=None, seed=42, task_runner=runner, save_dir=tmp_path)
    assert sum(stage == 'findings' for stage, _ in seen) == 2
    assert output['findings'][0]['evidence_line_ids'] == []
    assert output['findings'][0]['status'] == 'unvalidated'
    assert output['validation_log']
    assert all(f['status'] == 'unvalidated' for f in output['findings'])


def test_four_stages_use_only_validated_findings_and_retrieved_ids(techniques, fake_encoder, tmp_path):
    cluster, rag, kb, finding = run_context(techniques, fake_encoder)
    stages = []
    def runner(stage, schema, prompt, inputs, tools):
        stages.append(stage)
        assert 'ground_truth' not in json.dumps(inputs)
        if stage == 'findings':
            return {'findings': [finding]}
        if stage == 'mappings':
            assert any(c['id'] == 'T1110.001' for c in inputs['candidates']['f1'])
            return {'mappings': [{'finding_id': 'f1', 'techniques': [{'technique_id': 'T1110.001',
                'name': 'Password Guessing', 'tactic': 'credential-access', 'is_primary': True, 'justification': 'SSH'}],
                'mapping_confidence': .9}]}
        if stage == 'incidents':
            return {'incidents': [{'incident_id': 'i1', 'finding_ids': ['f1'], 'title': 'SSH attack',
                'severity': 'high', 'confidence': .9, 'attacker_ips': ['203.0.113.10'], 'affected_assets': ['ssh-srv'],
                'kill_chain': [{'order': 1, 'ts_utc': '2026-10-17T00:00:00Z', 'finding_id': 'f1',
                                'technique_id': 'T1110.001', 'description': 'Password attempts'}], 'rationale': 'Same source'}]}
        return {'plans': [{'incident_id': 'i1', 'executive_summary': 'Review SSH access', 'immediate_actions': [],
                          'mitigations': [{'mitigation_id': 'M1032', 'name': 'Multi-factor Authentication', 'for_technique_id': 'T1110.001'}],
                          'investigation_steps': ['Review authentication logs'], 'prevention': ['Enable MFA']}]}
    output = run_agents([cluster], {}, kb, rag, client=None, seed=42, task_runner=runner, save_dir=tmp_path)
    assert stages == ['findings', 'mappings', 'incidents', 'plans']
    assert output['validation_log'] == []
    assert 'T1110.001' in output['retrieval_log']['f1']
    assert output['plans'][0]['mitigations'][0]['mitigation_id'] == 'M1032'


@pytest.mark.live
def test_live_smoke_call_is_cached(tmp_path):
    import os
    if not os.environ.get('GEMINI_API_KEY'):
        pytest.skip('GEMINI_API_KEY is not set; no live result claimed')
    client = CachedLLM(cache_dir=tmp_path)
    assert client.json_call('Return exactly a JSON object with ok set to true.', {}) == {'ok': True}
    calls = client.calls
    client.json_call('Return exactly a JSON object with ok set to true.', {})
    assert client.calls == calls


def test_invalid_id_in_reasoning_is_removed_after_retry(techniques, fake_encoder, tmp_path):
    from cyberagents.validators import validate_text_ids
    cluster, rag, kb, finding = run_context(techniques, fake_encoder)
    def runner(stage, schema, prompt, inputs, tools):
        return {stage: [{**finding, 'reasoning': 'This is T9999'}]} if stage == 'findings' else {stage: []}
    output = run_agents([cluster], {}, kb, rag, client=None, seed=42, task_runner=runner, save_dir=tmp_path)
    assert output['findings'][0]['status'] == 'unvalidated'
    assert validate_text_ids(output, kb) == []


def test_invalid_mapping_is_stripped_and_its_finding_marked_unvalidated(techniques, fake_encoder, tmp_path):
    cluster, rag, kb, finding = run_context(techniques, fake_encoder)
    def runner(stage, schema, prompt, inputs, tools):
        if stage == 'findings':
            return {'findings': [finding]}
        if stage == 'mappings':
            return {'mappings': [{'finding_id': 'f1', 'techniques': [{'technique_id': 'T9999', 'name': 'Invented',
                'tactic': 'discovery', 'is_primary': True, 'justification': 'Invented'}], 'mapping_confidence': .9}]}
        return {stage: []}
    output = run_agents([cluster], {}, kb, rag, client=None, seed=42, task_runner=runner, save_dir=tmp_path)
    assert output['mappings'][0]['techniques'] == []
    assert output['findings'][0]['status'] == 'unvalidated'
    assert output['incidents'] == []


def test_reused_client_reports_only_this_runs_calls_and_tokens(techniques, fake_encoder):
    from types import SimpleNamespace
    cluster, rag, kb, finding = run_context(techniques, fake_encoder)
    client = SimpleNamespace(calls=10, tokens=20, cache_hits=3)
    def runner(stage, schema, prompt, inputs, tools):
        return {'findings': [{**finding, 'verdict': 'benign'}]}
    output = run_agents([cluster], {}, kb, rag, client=client, seed=42, task_runner=runner)
    assert output['llm_calls'] == 0 and output['tokens'] == 0 and output['cache_hits'] == 0


def test_unreported_provider_tokens_are_not_presented_as_zero(tmp_path):
    client = CachedLLM(cache_dir=tmp_path, transport=lambda prompt, inputs: ('ok', None), min_interval=0)
    assert client.text_call('test', {}) == 'ok'
    assert client.tokens is None


def test_crewai_framework_uses_cached_provider_without_a_live_api(tmp_path, techniques, fake_encoder):
    """Exercise Agent/Task/Crew with fake provider text, not a fake stage runner."""
    from cyberagents.agents import _crew_task
    from cyberagents.schemas import FindingList
    _, _, _, finding = run_context(techniques, fake_encoder)
    client = CachedLLM(cache_dir=tmp_path, min_interval=0,
                       transport=lambda prompt, inputs: ('Final Answer: ' + json.dumps({'findings': [finding]}), 11))
    try:
        result = _crew_task('findings', FindingList, 'Analyze the supplied cluster.', {}, {}, client)
    except PermissionError as error:
        if '/Library/Application Support/crewai' not in str(error):
            raise
        pytest.skip('CrewAI import writes its credential directory outside this managed workspace; run in an unrestricted terminal or Colab')
    assert result['findings'][0]['finding_id'] == finding['finding_id']
    assert client.calls >= 1
    calls = client.calls
    repeated = _crew_task('findings', FindingList, 'Analyze the supplied cluster.', {}, {}, client)
    assert repeated == result
    assert client.calls == calls and client.cache_hits >= 1
