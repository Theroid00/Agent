"""T-RULES: every injected stage and benign look-alike reaches the agents."""
import json
import pandas as pd
from cyberagents.generator import generate_logs
from cyberagents.parser import parse_logs
from cyberagents.prefilter import prefilter
from cyberagents.baselines import rules_only


def test_prefilter_preserves_attack_stages_and_benign_lookalikes(tmp_path):
    generate_logs(42, tmp_path, background={'auth': 30, 'web': 40, 'fw': 50})
    events = parse_logs(tmp_path)
    clusters = prefilter(events)
    truth = json.loads((tmp_path / 'ground_truth.json').read_text())
    covered = {line for c in clusters for line in c['all_line_ids']}
    for scenario in truth['scenarios']:
        for part in scenario['stages'] or [scenario]:
            assert covered.intersection(part['line_ids']), (scenario['scenario_id'], part)
    assert len(clusters) < 40
    assert all(len(c['sample_lines']) <= 10 for c in clusters)
    assert all(set(c['all_line_ids']) <= set(events.event_id) for c in clusters)
    output = rules_only(clusters, seed=42)
    assert len(output['incidents']) == len(clusters)
    assert output['mappings'] == []


def test_failures_outside_window_do_not_trigger_threshold():
    records = [dict(event_id=f'auth:{i}', event_type='ssh_failed', src_ip='203.0.113.10',
                    ts_utc=pd.Timestamp('2026-10-17T00:00Z') + pd.Timedelta(hours=i),
                    user='deploy', host='ssh-srv', source='auth', raw='failure',
                    path=None, target_user=None, command=None, bytes_out=0, dst_ip='10.0.0.10')
               for i in range(3)]
    assert prefilter(pd.DataFrame(records)) == []


def test_cluster_sampling_keeps_the_success_after_failures(tmp_path):
    generate_logs(42, tmp_path, background={'auth': 0, 'web': 0, 'fw': 0})
    events = parse_logs(tmp_path)
    clusters = prefilter(events)
    for cluster in clusters:
        if 'R-SUCCESS-AFTER-FAIL' in cluster['rule_ids']:
            shown = {line['event_id'] for line in cluster['sample_lines']}
            accepted = set(events[(events.event_id.isin(cluster['all_line_ids'])) &
                                  (events.event_type == 'ssh_accepted')].event_id)
            assert shown & accepted


def test_full_dev_window_stays_within_the_documented_cluster_budget(tmp_path):
    generate_logs(42, tmp_path)
    clusters = prefilter(parse_logs(tmp_path))
    assert len(clusters) < 40
