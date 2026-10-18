"""T-DATA: seed-42 determinism, scenario coverage and label isolation."""
import json
from cyberagents.generator import generate_logs
from cyberagents.parser import parse_logs


def test_generator_is_repeatable_and_keeps_labels_out_of_logs(tmp_path):
    a, b = tmp_path / 'a', tmp_path / 'b'
    generate_logs(42, a, background={'auth': 30, 'web': 40, 'fw': 50})
    generate_logs(42, b, background={'auth': 30, 'web': 40, 'fw': 50})
    for name in ['auth.log', 'access.log', 'firewall.csv', 'ground_truth.json', 'asset_inventory.json']:
        assert (a / name).read_bytes() == (b / name).read_bytes()
    for name in ['auth.log', 'access.log', 'firewall.csv', 'asset_inventory.json']:
        text = (a / name).read_text()
        assert 'scenario_id' not in text and 'accepted_techniques' not in text


def test_all_scenarios_have_real_line_ids_and_chain_stages(tmp_path):
    generate_logs(42, tmp_path, background={'auth': 30, 'web': 40, 'fw': 50})
    events = parse_logs(tmp_path)
    truth = json.loads((tmp_path / 'ground_truth.json').read_text())
    scenarios = {s['scenario_id']: s for s in truth['scenarios']}
    assert set(scenarios) == {f'A{i}' for i in range(1, 7)} | {f'B{i}' for i in range(1, 6)}
    for scenario in scenarios.values():
        assert scenario['line_ids'] and set(scenario['line_ids']) <= set(events.event_id)
    stages = scenarios['A6']['stages']
    assert [s['stage'] for s in stages] == [1, 2, 3, 4, 5]
    starts = [events[events.event_id.isin(s['line_ids'])].ts_utc.min() for s in stages]
    assert starts == sorted(starts)
    assert (starts[-1] - starts[0]).total_seconds() < 2 * 3600
    assert events.event_id.is_unique


def test_environment_ips_and_chain_indicators_match_the_fixed_design(tmp_path):
    from ipaddress import ip_address, ip_network
    generate_logs(42, tmp_path, background={'auth': 30, 'web': 40, 'fw': 50})
    events = parse_logs(tmp_path)
    allowed = [ip_network(cidr) for cidr in ['10.0.0.0/24', '192.0.2.0/24', '198.51.100.0/24', '203.0.113.0/24']]
    for value in set(events.src_ip.dropna()) | set(events.dst_ip.dropna()):
        assert any(ip_address(value) in network for network in allowed)
    truth = json.loads((tmp_path / 'ground_truth.json').read_text())
    chain = next(s['stages'] for s in truth['scenarios'] if s['scenario_id'] == 'A6')
    stage_ips = [set(events[events.event_id.isin(s['line_ids'])].src_ip.dropna()) for s in chain[:3]]
    assert stage_ips[0] == stage_ips[1] == stage_ips[2]
    login_users = set(events[events.event_id.isin(chain[2]['line_ids'])].user)
    sudo_users = set(events[events.event_id.isin(chain[3]['line_ids'])].user)
    assert login_users == sudo_users
