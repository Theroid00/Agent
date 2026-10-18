"""Loose deterministic rules preserve benign look-alikes for agent evaluation."""

from collections import Counter
from ipaddress import ip_address, ip_network
import re
import pandas as pd
from .config import CONFIG


def _windows(group, minutes, *, count=1, unique=None, total=None):
    rows = group.sort_values('ts_utc').to_dict('records')
    left, selected, counts, amount = 0, set(), Counter(), 0
    window = pd.Timedelta(minutes=minutes)
    for right, row in enumerate(rows):
        if unique:
            counts[row[unique]] += 1
        amount += row.get('bytes_out') or 0
        while row['ts_utc'] - rows[left]['ts_utc'] > window:
            if unique:
                key = rows[left][unique]
                counts[key] -= 1
                if counts[key] == 0:
                    del counts[key]
            amount -= rows[left].get('bytes_out') or 0
            left += 1
        size = len(counts) if unique else right - left + 1
        if size >= count and (total is None or amount >= total):
            selected.update(r['event_id'] for r in rows[left:right + 1])
    bursts, current, previous = [], set(), None
    for row in rows:
        if row['event_id'] not in selected:
            continue
        if previous is not None and row['ts_utc'] - previous > window:
            bursts.append(current)
            current = set()
        current.add(row['event_id'])
        previous = row['ts_utc']
    return bursts + ([current] if current else [])


def prefilter(events):
    if events.empty:
        return []
    settings, candidates = CONFIG['rules'], []

    def add(rule, subset, key, minutes, **criteria):
        for _, group in subset.groupby(key, dropna=True):
            for ids in _windows(group, minutes, **criteria):
                candidates.append({'rules': {rule}, 'ids': ids})

    failed = events[events.event_type == 'ssh_failed']
    add('R-AUTH-FAIL', failed, 'src_ip', settings['auth_fail_window_min'], count=settings['auth_fail_n'])
    add('R-SPRAY', failed, 'src_ip', settings['spray_window_min'], count=settings['spray_users_n'], unique='user')
    for _, group in events[events.event_type.isin(['ssh_failed', 'ssh_accepted'])].groupby('src_ip'):
        failures = group[group.event_type == 'ssh_failed']
        for accepted in group[group.event_type == 'ssh_accepted'].to_dict('records'):
            prior = failures[(failures.ts_utc <= accepted['ts_utc']) &
                             (failures.ts_utc >= accepted['ts_utc'] - pd.Timedelta(minutes=settings['success_after_fail_window_min']))]
            if not prior.empty:
                candidates.append({'rules': {'R-SUCCESS-AFTER-FAIL'}, 'ids': set(prior.event_id) | {accepted['event_id']}})
    connections = events[events.event_type == 'conn']
    add('R-SCAN', connections, 'src_ip', settings['scan_window_min'], count=settings['scan_ports_n'], unique='dst_port')
    web = events[(events.event_type == 'http_request') & events.path.fillna('').str.contains(
        r"'|UNION|OR\s+1=1|--|\.\./|/etc/passwd", case=False, regex=True)]
    add('R-WEB-PATTERN', web, 'src_ip', 30)
    sudo = events[(events.event_type == 'sudo') & (events.target_user == 'root') &
                  events.command.fillna('').str.contains(r'/bin/(?:ba)?sh|\bsu\b', regex=True)]
    add('R-SUDO-ROOT', sudo, 'user', 30)
    internal = ip_network('10.0.0.0/24')
    external = connections.loc[connections.dst_ip.map(lambda ip: ip_address(ip) not in internal).astype(bool)]
    add('R-EGRESS', external, 'host', settings['egress_window_min'], total=settings['egress_bytes'])
    merged = []
    for candidate in candidates:
        overlapping = [item for item in merged if item['ids'] & candidate['ids']]
        for item in overlapping:
            candidate['ids'].update(item['ids'])
            candidate['rules'].update(item['rules'])
            merged.remove(item)
        merged.append(candidate)
    clusters = []
    for item in merged:
        subset = events[events.event_id.isin(item['ids'])].sort_values(['ts_utc', 'event_id'])
        limit = CONFIG['cluster_sample_lines']
        positions = ([round(i * (len(subset) - 1) / (limit - 1)) for i in range(limit)]
                     if len(subset) > limit and limit > 1 else list(range(min(limit, len(subset)))))
        clusters.append({
            'rule_ids': sorted(item['rules']), 'src_ips': sorted(subset.src_ip.dropna().unique()),
            'users': sorted(subset.user.dropna().unique()), 'hosts': sorted(subset.host.dropna().unique()),
            't_start': subset.ts_utc.min().isoformat(), 't_end': subset.ts_utc.max().isoformat(),
            'line_count': len(subset), 'all_line_ids': list(subset.event_id),
            'sample_lines': [{'event_id': r['event_id'], 'ts_utc': r['ts_utc'].isoformat(), 'raw': r['raw']}
                             for r in subset.iloc[positions].to_dict('records')],
        })
    clusters.sort(key=lambda c: (c['t_start'], c['all_line_ids'][0]))
    for index, cluster in enumerate(clusters, 1):
        cluster['cluster_id'] = f'c{index:03d}'
    return clusters
