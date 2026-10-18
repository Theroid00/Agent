"""T-E2E: deterministic orchestration, cache provenance and held-out protection."""
import json
from pathlib import Path
import pytest
from cyberagents.pipeline import run_system
from cyberagents.generator import generate_logs
from cyberagents.rag import AttackRAG


def test_s0_saves_and_reuses_identical_output_without_reading_labels(tmp_path, monkeypatch):
    generate_logs(42, tmp_path / 'seed42', background={'auth': 30, 'web': 40, 'fw': 50})
    read = Path.read_text
    def guarded(path, *args, **kwargs):
        if path.name == 'ground_truth.json':
            raise AssertionError('Pipeline read ground truth')
        return read(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', guarded)
    result = run_system('S0', 42, output_dir=tmp_path)
    assert result['incidents'] and result['execution'] == 'deterministic'
    assert run_system('S0', 42, output_dir=tmp_path) == result
    inventory = json.loads((tmp_path / 'seed42/asset_inventory.json').read_text())
    inventory['admin_user'] = 'changed'
    (tmp_path / 'seed42/asset_inventory.json').write_text(json.dumps(inventory))
    with pytest.raises(ValueError, match='Cached run'):
        run_system('S0', 42, output_dir=tmp_path)


def test_mocked_pipeline_is_explicitly_labelled_and_persists_stage_artifacts(tmp_path, techniques, fake_encoder):
    generate_logs(42, tmp_path / 'seed42', background={'auth': 30, 'web': 40, 'fw': 50})
    def runner(stage, schema, prompt, inputs, tools):
        assert stage == 'findings'
        return {'findings': [dict(finding_id=c['cluster_id'], cluster_ids=[c['cluster_id']], verdict='benign',
            summary='Test-only benign output', evidence_line_ids=[c['sample_lines'][0]['event_id']],
            src_ips=[], users=[], hosts=[], reasoning='Mock contract test, not detection measurement')
            for c in inputs['clusters']]}
    rag = AttackRAG(techniques, encoder=fake_encoder, source_ref='fixture')
    result = run_system('S3', 42, output_dir=tmp_path, kb={'techniques': techniques, 'mitigations': {}},
                        rag=rag, task_runner=runner)
    assert result['execution'] == 'mock'
    assert (tmp_path / 'stages/S3_seed42/findings.json').exists()
    assert result['incidents'] == []


def test_held_out_seed_is_blocked_before_generation_without_system_freeze(tmp_path):
    with pytest.raises(RuntimeError, match='System freeze'):
        run_system('S0', 7, output_dir=tmp_path)
    assert not (tmp_path / 'seed7').exists()


def test_uncached_llm_run_requires_explicit_live_flag(tmp_path):
    with pytest.raises(RuntimeError, match='live'):
        run_system('S3', 42, output_dir=tmp_path)


def test_mock_result_is_not_accepted_as_a_real_benchmark(tmp_path):
    from cyberagents.evaluate import evaluate_saved
    path = tmp_path / 'mock.json'
    path.write_text(json.dumps({'execution': 'mock', 'system': 'S3', 'seed': 42}))
    with pytest.raises(ValueError, match='Mock outputs'):
        evaluate_saved(path, {}, output_dir=tmp_path)
