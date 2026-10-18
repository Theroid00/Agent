"""T-PARSE: auth, Apache and firewall normalization without ground-truth reads."""
import pandas as pd
from cyberagents.parser import parse_line, parse_logs
from cyberagents.generator import generate_logs


def test_auth_failure_and_sudo_fields():
    record = parse_line('auth', 'Oct 17 02:14:07 ssh-srv sshd[4123]: Failed password for invalid user admin from 203.0.113.45 port 51522 ssh2', 'auth:000001')
    assert record['event_type'] == 'ssh_failed'
    assert record['user'] == 'admin' and record['src_ip'] == '203.0.113.45'
    assert record['ts_utc'] == pd.Timestamp('2026-10-16T20:44:07Z')
    sudo = parse_line('auth', 'Oct 17 02:21:03 ssh-srv sudo: deploy : TTY=pts/0 ; PWD=/home/deploy ; USER=root ; COMMAND=/bin/bash', 'auth:000002')
    assert sudo['event_type'] == 'sudo' and sudo['user'] == 'deploy'
    assert sudo['target_user'] == 'root' and sudo['command'] == '/bin/bash'


def test_web_decodes_queries_and_preserves_apostrophes():
    record = parse_line('web', '10.0.0.42 - - [17/Oct/2026:11:05:40 +0530] "GET /search?q=O%27Brien HTTP/1.1" 200 2048 "-" "Mozilla/5.0"', 'web:000001')
    assert record['path'] == "/search?q=O'Brien"
    assert record['status'] == 200 and record['host'] == 'web-srv'


def test_generated_lines_all_parse_without_touching_ground_truth(tmp_path):
    generate_logs(42, tmp_path, background={'auth': 30, 'web': 40, 'fw': 50})
    (tmp_path / 'ground_truth.json').unlink()
    events = parse_logs(tmp_path)
    count = sum(len((tmp_path / name).read_text().splitlines()) for name in ['auth.log', 'access.log', 'firewall.csv']) - 1
    assert len(events) == count
    assert not events.ts_utc.isna().any()
    assert set(events.source) == {'auth', 'web', 'fw'}
