"""Deterministic grounding checks; no IDs are guessed or silently corrected."""

import re
from collections import Counter
from datetime import datetime, timedelta
from ipaddress import ip_address, ip_network
from .config import CONFIG


def validate_stage_coverage(stage, items, *, clusters=(), findings=(), mappings=(), incidents=(), inventory=None):
    """Validate complete stage hand-offs independently of grounding checks."""
    errors = []
    catalog = {c['cluster_id']: c for c in clusters}
    eligible = {f['finding_id']: f for f in findings
                if f.get('status', 'validated') == 'validated' and f.get('verdict') != 'benign'}
    if stage == 'findings':
        represented = set()
        for finding in items:
            ids = finding['cluster_ids']
            represented.update(ids)
            if len(ids) != 1:
                errors.append(f"{finding['finding_id']}: use exactly one cluster per finding; correlate later")
            for cid in ids:
                if cid in catalog and not set(finding['evidence_line_ids']) & set(catalog[cid]['all_line_ids']):
                    errors.append(f"{finding['finding_id']}: missing cited evidence from cluster {cid}")
        missing = set(catalog) - represented
    elif stage == 'mappings':
        missing = set(eligible) - {item['finding_id'] for item in items}
    elif stage == 'incidents':
        mapped = {m['finding_id'] for m in mappings if m.get('status', 'validated') == 'validated'}
        counts = Counter(fid for item in items for fid in item['finding_ids'])
        missing = (eligible.keys() & mapped) - counts.keys()
        for fid, count in counts.items():
            if count > 1:
                errors.append(f'{fid}: assigned to multiple incidents')
        network = (inventory or {}).get('internal_network')
        internal = ip_network(network) if network else None
        for incident in items:
            iid = incident['incident_id']
            steps = {step['finding_id'] for step in incident['kill_chain']}
            for fid in set(incident['finding_ids']) - steps:
                errors.append(f'{iid}: missing kill-chain step for {fid}')
            actor_ips, intervals = set(), []
            for fid in incident['finding_ids']:
                for cid in eligible.get(fid, {}).get('cluster_ids', []):
                    cluster = catalog.get(cid, {})
                    for address in cluster.get('src_ips', []):
                        if internal is None or ip_address(address) not in internal:
                            actor_ips.add(address)
                    if cluster.get('t_start') and cluster.get('t_end'):
                        intervals.append((datetime.fromisoformat(cluster['t_start']),
                                          datetime.fromisoformat(cluster['t_end'])))
            if len(actor_ips) > 1:
                errors.append(f'{iid}: unrelated external actors {sorted(actor_ips)} must remain separate')
            if intervals:
                intervals.sort()
                end = intervals[0][1]
                for start, finish in intervals[1:]:
                    if start - end > timedelta(minutes=CONFIG['correlation']['max_gap_min']):
                        errors.append(f'{iid}: disconnected time windows; use separate incidents')
                    end = max(end, finish)
    elif stage == 'plans':
        counts = Counter(item['incident_id'] for item in items)
        missing = {item['incident_id'] for item in incidents} - counts.keys()
        errors.extend(f'{iid}: multiple response plans' for iid, count in counts.items() if count > 1)
    else:
        raise ValueError(f'Unknown stage: {stage}')
    if missing:
        errors.append(f'{stage}: missing required inputs {sorted(missing)}')
    return errors


def validate_findings(findings, clusters):
    catalog = {c['cluster_id']: set(c['all_line_ids']) for c in clusters}
    errors, seen = [], set()
    for finding in findings:
        fid = finding['finding_id']
        if fid in seen:
            errors.append(f'{fid}: duplicate finding ID')
        seen.add(fid)
        ids = finding['cluster_ids']
        if not ids or any(cid not in catalog for cid in ids):
            errors.append(f'{fid}: unknown or empty cluster IDs')
        allowed = set().union(*(catalog.get(cid, set()) for cid in ids))
        if not finding['evidence_line_ids'] or not set(finding['evidence_line_ids']) <= allowed:
            errors.append(f'{fid}: evidence does not belong to its clusters')
    return errors


def validate_mappings(mappings, findings, kb, retrieval_log):
    known = {f['finding_id'] for f in findings if f.get('verdict') != 'benign'}
    errors, seen = [], set()
    for mapping in mappings:
        fid = mapping['finding_id']
        if fid not in known or fid in seen:
            errors.append(f'{fid}: unknown, benign or duplicate finding mapping')
        seen.add(fid)
        choices = mapping['techniques']
        if not choices or sum(t['is_primary'] for t in choices) != 1:
            errors.append(f'{fid}: exactly one primary technique required')
        for choice in choices:
            tid = choice['technique_id']
            record = kb['techniques'].get(tid)
            if not record or tid not in retrieval_log.get(fid, []):
                errors.append(f'{fid}: {tid} unknown or not retrieved for this finding')
            elif choice.get('name') != record.get('name') or choice.get('tactic') not in record.get('tactics', []):
                errors.append(f'{fid}: {tid} name or tactic disagrees with the pinned catalog')
    return errors


def validate_incidents(incidents, findings, mappings):
    known = {f['finding_id'] for f in findings if f.get('verdict') != 'benign'}
    allowed = {m['finding_id']: {t['technique_id'] for t in m['techniques']} for m in mappings}
    errors, seen = [], set()
    for incident in incidents:
        iid = incident['incident_id']
        if iid in seen:
            errors.append(f'{iid}: duplicate incident ID')
        seen.add(iid)
        if not incident['finding_ids'] or not set(incident['finding_ids']) <= known:
            errors.append(f'{iid}: unknown, benign or empty finding references')
        for step in incident['kill_chain']:
            fid = step['finding_id']
            if fid not in incident['finding_ids'] or step['technique_id'] not in allowed.get(fid, set()):
                errors.append(f'{iid}: kill-chain technique does not belong to the referenced finding')
        stamps = [datetime.fromisoformat(s['ts_utc']) for s in incident['kill_chain'] if s.get('ts_utc')]
        if stamps != sorted(stamps):
            errors.append(f'{iid}: kill-chain timestamps are not chronological')
    return errors


def validate_plans(plans, incidents, kb):
    allowed = {i['incident_id']: {s['technique_id'] for s in i['kill_chain']} for i in incidents}
    errors, seen = [], set()
    for plan in plans:
        iid = plan['incident_id']
        if iid not in allowed or iid in seen:
            errors.append(f'{iid}: unknown or duplicate response incident')
        seen.add(iid)
        for mitigation in plan['mitigations']:
            tid, mid = mitigation['for_technique_id'], mitigation['mitigation_id']
            records = kb['mitigations'].get(tid, [])
            match = next((m for m in records if m['id'] == mid), None)
            if not match or tid not in allowed.get(iid, set()):
                errors.append(f'{iid}: mitigation is not linked to an incident technique')
            elif mitigation.get('name', match['name']) != match['name']:
                errors.append(f'{iid}: mitigation name disagrees with the catalog')
    return errors


def validate_text_ids(value, kb):
    errors = []
    known = set(kb['techniques']) | {m['id'] for records in kb['mitigations'].values() for m in records}
    if isinstance(value, dict):
        for field in value.values():
            errors.extend(validate_text_ids(field, kb))
    elif isinstance(value, list):
        for item in value:
            errors.extend(validate_text_ids(item, kb))
    elif isinstance(value, str):
        for identifier in re.findall(r'\b(?:T\d{4}(?:\.\d+)?|M\d{4})\b', value):
            if identifier not in known:
                errors.append(f'Unknown ID in output text: {identifier}')
    return errors
