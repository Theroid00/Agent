"""Synthetic auth/web/firewall logs; labels are written separately for evaluation."""

import csv
import io
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .config import CONFIG

ACCEPTED = {
    'A1': ['T1110.001', 'T1110'], 'A2': ['T1110.003', 'T1110'],
    'A3': ['T1046', 'T1595.001'], 'A4': ['T1190'], 'A5': ['T1190', 'T1083'],
}
CHAIN = [['T1046', 'T1595.001'], ['T1110.001', 'T1110'], ['T1078', 'T1021.004'],
         ['T1548.003'], ['T1048', 'T1041']]


def generate_logs(seed, out_dir, *, background=None):
    rng = random.Random(seed)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = datetime.fromisoformat(CONFIG['date']).replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
    users = ['asharma', 'rkumar', 'deploy', 'pmehta', 'srao', 'mshah', 'npatel', 'akhan',
             'vnair', 'rjain', 'pgupta', 'kdas', 'troy', 'singh', 'iyer']
    inventory = {
        'internal_network': '10.0.0.0/24',
        'hosts': {'10.0.0.10': {'name': 'ssh-srv', 'role': 'ssh server'},
                  '10.0.0.20': {'name': 'web-srv', 'role': 'web server'},
                  '10.0.0.5': {'name': 'mon-01', 'role': 'service health checks'},
                  '192.0.2.10': {'name': 'backup.corp-example.net', 'role': 'nightly backup target'}},
        'users': users + ['sysadmin'], 'admin_user': 'sysadmin',
        'admin_working_hours_ist': [9, 19], 'monitoring_host': '10.0.0.5',
        'backup_server': '192.0.2.10',
    }
    records = {source: [] for source in ['auth', 'web', 'fw']}

    def auth(seconds, ip, user, outcome='failed', scenario=None, stage=None, sudo=False):
        ts = base + timedelta(seconds=seconds)
        if sudo:
            message = f'sudo: {user} : TTY=pts/0 ; PWD=/home/{user} ; USER=root ; COMMAND=/bin/bash'
        else:
            result = 'Failed' if outcome == 'failed' else 'Accepted'
            message = f'sshd[4123]: {result} password for {user} from {ip} port 51522 ssh2'
        records['auth'].append((ts, f'{ts:%b %d %H:%M:%S} ssh-srv {message}', scenario, stage))

    def web(seconds, ip, path, scenario=None, agent='Mozilla/5.0'):
        ts = base + timedelta(seconds=seconds)
        line = f'{ip} - - [{ts:%d/%b/%Y:%H:%M:%S %z}] "GET {path} HTTP/1.1" 200 1024 "-" "{agent}"'
        records['web'].append((ts, line, scenario, None))

    def fw(seconds, src, dst, port, size=60, scenario=None, stage=None):
        ts = base + timedelta(seconds=seconds)
        row = [ts.isoformat(), src, 40112, dst, port, 'tcp', 'ALLOW', size, 0]
        records['fw'].append((ts, row, scenario, stage))

    counts = CONFIG['background'] if background is None else background
    for source, count in counts.items():
        for _ in range(count):
            seconds = rng.randrange(9 * 3600, 19 * 3600) if rng.random() < .7 else rng.randrange(24 * 3600)
            ip = f'10.0.0.{rng.randrange(100, 151)}'
            if source == 'auth':
                auth(seconds, ip, rng.choice(users), 'failed' if rng.random() < CONFIG['auth_background_fail_probability'] else 'accepted')
            elif source == 'web':
                web(seconds, ip, rng.choice(['/index', '/health', '/products?id=2', '/search?q=books']))
            elif source == 'fw':
                fw(seconds, ip, '10.0.0.20', rng.choice([22, 80, 443]), rng.randrange(100, 20000))
    attackers = rng.sample(range(10, 240), 6)
    ips = [f'203.0.113.{n}' for n in attackers]
    offset = rng.randrange(0, 1200)
    for i in range(12):
        auth(3600 + offset + i * 8, ips[0], 'root', scenario='A1')
    for i, user in enumerate(users[:8]):
        auth(5 * 3600 + offset + i * 12, ips[1], user, scenario='A2')
    for i in range(22):
        fw(8 * 3600 + offset + i, ips[2], '10.0.0.10', 20 + i, scenario='A3')
    for i, payload in enumerate(['/products?id=1%27%20OR%20%271%27=%271', '/products?id=1%20UNION%20SELECT%20password', '/login?u=admin%27--']):
        web(11 * 3600 + offset + i * 2, ips[3], payload, 'A4', 'sqlmap/1.7')
    for i in range(3):
        web(14 * 3600 + offset + i, ips[4], '/files?path=../../etc/passwd', 'A5')
    chain_start = 2 * 3600 + offset
    for i in range(22):
        fw(chain_start + i, ips[5], '10.0.0.10', 20 + i, scenario='A6', stage=1)
    for i in range(12):
        auth(chain_start + 600 + i * 6, ips[5], 'deploy', scenario='A6', stage=2)
    auth(chain_start + 900, ips[5], 'deploy', 'accepted', 'A6', 3)
    auth(chain_start + 1020, '', 'deploy', scenario='A6', stage=4, sudo=True)
    fw(chain_start + 1800, '10.0.0.10', '198.51.100.200', 4444,
       150_000_000, 'A6', 5)
    for i in range(3):
        auth(10 * 3600 + i * 20, '10.0.0.42', 'asharma', scenario='B1')
    auth(10 * 3600 + 80, '10.0.0.42', 'asharma', 'accepted', 'B1')
    auth(12 * 3600, '', 'sysadmin', scenario='B2', sudo=True)
    web(11 * 3600, '10.0.0.43', '/search?q=O%27Brien', 'B3')
    for seconds in range(0, 24 * 3600, 300):
        for i in range(20):
            fw(seconds + i, '10.0.0.5', '10.0.0.20', 20 + i, scenario='B4')
    fw(23 * 3600, '10.0.0.10', '192.0.2.10', 443, 200_000_000, 'B5')
    truth = {name: {'scenario_id': name, 'type': 'attack' if name.startswith('A') else 'benign',
                    'accepted_techniques': ACCEPTED.get(name, []), 'line_ids': [],
                    'stages': ([{'stage': i + 1, 'accepted_techniques': ids, 'line_ids': []}
                                for i, ids in enumerate(CHAIN)] if name == 'A6' else None)}
             for name in [*[f'A{i}' for i in range(1, 7)], *[f'B{i}' for i in range(1, 6)]]}
    for source, filename in [('auth', 'auth.log'), ('web', 'access.log'), ('fw', 'firewall.csv')]:
        rows = sorted(records[source], key=lambda row: row[0])
        output = io.StringIO()
        writer = csv.writer(output)
        if source == 'fw':
            writer.writerow(['ts', 'src_ip', 'src_port', 'dst_ip', 'dst_port', 'proto', 'action', 'bytes_out', 'bytes_in'])
        for index, (_, raw, scenario, stage) in enumerate(rows, 1):
            event_id = f'{source}:{index:06d}'
            if source == 'fw':
                writer.writerow(raw)
            else:
                output.write(raw + '\n')
            if scenario:
                truth[scenario]['line_ids'].append(event_id)
                if stage:
                    truth[scenario]['stages'][stage - 1]['line_ids'].append(event_id)
        (out_dir / filename).write_text(output.getvalue())
    (out_dir / 'ground_truth.json').write_text(json.dumps({'seed': seed, 'scenarios': list(truth.values())}, indent=2))
    (out_dir / 'asset_inventory.json').write_text(json.dumps(inventory, indent=2))
    return {'directory': str(out_dir), 'seed': seed}
