"""Normalize supported log sources; this module never reads ground truth."""

import csv
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
import pandas as pd
from .config import CONFIG

FIELDS = ['event_id', 'source', 'ts_utc', 'host', 'src_ip', 'src_port', 'dst_ip', 'dst_port',
          'user', 'event_type', 'outcome', 'http_method', 'path', 'status', 'bytes_out',
          'user_agent', 'raw', 'target_user', 'command']
AUTH = re.compile(r'^(\w{3}\s+\d+ \d+:\d+:\d+) (\S+) (.*)$')
LOGIN = re.compile(r'(Failed|Accepted) password for (?:invalid user )?(\S+) from (\S+) port (\d+)')
WEB = re.compile(r'^(\S+) \S+ \S+ \[([^]]+)\] "(\S+) (.*?) HTTP/[^\"]+" (\d{3}) (\d+|-) "[^"]*" "([^"]*)"$')


def parse_line(source, line, event_id):
    record = dict.fromkeys(FIELDS)
    record.update(event_id=event_id, source=source, raw=line)
    if source == 'auth':
        match = AUTH.match(line)
        if not match:
            raise ValueError(f'Unrecognized auth line: {event_id}')
        stamp, host, message = match.groups()
        year = CONFIG['date'][:4]
        ts = datetime.strptime(f'{year} {stamp} +0530', '%Y %b %d %H:%M:%S %z')
        record.update(ts_utc=pd.Timestamp(ts).tz_convert('UTC'), host=host, dst_ip='10.0.0.10')
        login = LOGIN.search(message)
        if login:
            outcome, user, ip, port = login.groups()
            record.update(event_type='ssh_failed' if outcome == 'Failed' else 'ssh_accepted',
                          outcome=outcome.lower(), user=user, src_ip=ip, src_port=int(port), dst_port=22)
        elif 'sudo:' in message:
            sudo = re.search(r'sudo:\s+(\S+)\s*:.*?USER=(\S+)\s*;\s*COMMAND=(.*)$', message)
            if not sudo:
                raise ValueError(f'Unrecognized sudo line: {event_id}')
            user, target, command = sudo.groups()
            record.update(event_type='sudo', user=user, target_user=target, command=command, outcome='accepted')
        else:
            raise ValueError(f'Unrecognized auth message: {event_id}')
    elif source == 'web':
        match = WEB.match(line)
        if not match:
            raise ValueError(f'Unrecognized access line: {event_id}')
        ip, stamp, method, path, status, size, agent = match.groups()
        record.update(ts_utc=pd.Timestamp(datetime.strptime(stamp, '%d/%b/%Y:%H:%M:%S %z')).tz_convert('UTC'),
                      host='web-srv', src_ip=ip, dst_ip='10.0.0.20', dst_port=80,
                      event_type='http_request', http_method=method, path=unquote(path), status=int(status),
                      bytes_out=0 if size == '-' else int(size), user_agent=agent)
    else:
        raise ValueError(f'Unsupported source: {source}')
    return record


def parse_logs(directory):
    directory, rows = Path(directory), []
    for source, name in [('auth', 'auth.log'), ('web', 'access.log')]:
        for number, line in enumerate((directory / name).read_text().splitlines(), 1):
            rows.append(parse_line(source, line, f'{source}:{number:06d}'))
    with (directory / 'firewall.csv').open(newline='') as stream:
        for number, line in enumerate(csv.DictReader(stream), 1):
            record = dict.fromkeys(FIELDS)
            record.update(event_id=f'fw:{number:06d}', source='fw', ts_utc=pd.Timestamp(line['ts']).tz_convert('UTC'),
                          host='ssh-srv' if line['src_ip'] == '10.0.0.10' or line['dst_ip'] == '10.0.0.10' else 'web-srv',
                          src_ip=line['src_ip'], dst_ip=line['dst_ip'], src_port=int(line['src_port']),
                          dst_port=int(line['dst_port']), bytes_out=int(line['bytes_out']),
                          event_type='conn', outcome=line['action'], raw=','.join(line.values()))
            rows.append(record)
    return pd.DataFrame(rows, columns=FIELDS).sort_values(['ts_utc', 'event_id']).reset_index(drop=True)
