"""Ground-truth matching and metrics; evaluation is the only production label reader."""

import json
from collections import Counter
from pathlib import Path
import pandas as pd


def evaluate(output, truth, kb, *, valid_line_ids=None):
    scenarios = {s['scenario_id']: s for s in truth['scenarios']}
    owners = {line: sid for sid, scenario in scenarios.items() for line in scenario['line_ids']}
    valid = set(owners) if valid_line_ids is None else set(valid_line_ids)
    findings = {f['finding_id']: f for f in output.get('findings', [])}
    mappings = {m['finding_id']: m for m in output.get('mappings', [])}
    evidence = [line for finding in findings.values() for line in finding.get('evidence_line_ids', [])]
    cluster_lines = {c['cluster_id']: set(c['all_line_ids']) for c in output.get('clusters', [])}
    invalid_evidence = 0
    for finding in findings.values():
        permitted = set().union(*(cluster_lines.get(cid, set()) for cid in finding.get('cluster_ids', []))) if cluster_lines else valid
        invalid_evidence += sum(line not in valid or line not in permitted for line in finding.get('evidence_line_ids', []))
    matches, detected, false_positives, benign_fp, error_rows = [], set(), 0, 0, []
    for incident in output.get('incidents', []):
        lines = set().union(*(set(findings.get(fid, {}).get('evidence_line_ids', []))
                              for fid in incident.get('finding_ids', []))) & valid
        votes = Counter(owners.get(line, '__background__') for line in lines)
        winner = sorted(votes, key=lambda sid: (-votes[sid], sid))[0] if votes else '__background__'
        malicious = scenarios.get(winner, {}).get('type') == 'attack'
        if malicious:
            detected.add(winner)
        else:
            false_positives += 1
            benign_fp += scenarios.get(winner, {}).get('type') == 'benign'
            error_rows.append({'kind': 'false_positive', 'item': incident.get('incident_id'),
                               'matched_scenario': winner, 'cause': 'Benign/background evidence retained as an incident'})
        matches.append((incident, winner, lines))
    attacks = {sid for sid, scenario in scenarios.items() if scenario['type'] == 'attack'}
    for sid in sorted(attacks - detected):
        scenario_lines = set(scenarios[sid]['line_ids'])
        cluster_covered = any(scenario_lines & ids for ids in cluster_lines.values())
        error_rows.append({'kind': 'miss', 'item': sid, 'matched_scenario': sid,
                           'cause': 'Analyst dismissal/correlation' if cluster_covered else 'Pre-filter/no retained incident'})
    correct, total, chain_stages = 0, 0, 0
    for sid in sorted(detected):
        scenario = scenarios[sid]
        candidates = [(incident, lines) for incident, owner, lines in matches if owner == sid]
        if sid == 'A6':
            chain_stages = max((sum(bool(set(stage['line_ids']) & lines) for stage in scenario['stages'])
                                for _, lines in candidates), default=0)
        for part in scenario.get('stages') or [scenario]:
            part_lines = set(part['line_ids'])
            relevant = [(incident, lines) for incident, lines in candidates if part_lines & lines]
            if not relevant:
                continue
            total += 1
            mapped_correctly = False
            for incident, _ in relevant:
                for step in incident.get('kill_chain', []):
                    fid = step.get('finding_id')
                    own_evidence = set(findings.get(fid, {}).get('evidence_line_ids', []))
                    primary = {t.get('technique_id') for t in mappings.get(fid, {}).get('techniques', []) if t.get('is_primary')}
                    if own_evidence & part_lines and step.get('technique_id') in primary & set(part.get('accepted_techniques', [])):
                        mapped_correctly = True
            correct += mapped_correctly
    choices = [(m.get('finding_id'), t.get('technique_id')) for m in output.get('mappings', [])
               for t in m.get('techniques', [])]
    nonexistent = sum(tid not in kb['techniques'] for _, tid in choices)
    # S1 has no retriever: measure invented IDs, not absence of an unavailable tool.
    unretrieved = sum(tid not in output.get('retrieval_log', {}).get(fid, []) for fid, tid in choices) if output['system'] == 'S3' else None
    hallucinated = sum(tid not in kb['techniques'] or (output['system'] == 'S3' and
                       tid not in output.get('retrieval_log', {}).get(fid, [])) for fid, tid in choices)
    count = len(output.get('incidents', []))
    return {
        'system': output['system'], 'seed': output.get('seed'),
        'detected_scenarios': sorted(detected), 'detection_recall': len(detected) / len(attacks) if attacks else 0,
        'incident_precision': (count - false_positives) / count if count else 0,
        'false_positives': false_positives,
        'benign_case_false_positives': benign_fp,
        'background_false_positives': false_positives - benign_fp,
        'mapping_accuracy': correct / total if total else 0,
        'a6_stages': chain_stages, 'a6_correlated': chain_stages >= 4,
        'hallucination_rate': hallucinated / len(choices) if choices else 0,
        'nonexistent_technique_ids': nonexistent, 'unretrieved_technique_ids': unretrieved,
        'invalid_evidence_refs': invalid_evidence,
        'invalid_evidence_rate': invalid_evidence / len(evidence) if evidence else 0,
        'runtime_s': output.get('runtime_s'), 'llm_calls': output.get('llm_calls', 0),
        'tokens': output.get('tokens', 0), 'errors': error_rows,
    } | ({'mapping_accuracy': None} if output['system'] == 'S0' else {})


def evaluate_saved(output_path, kb, *, output_dir='outputs'):
    from .parser import parse_logs
    output = json.loads(Path(output_path).read_text())
    if output.get('execution') == 'mock':
        raise ValueError('Mock outputs cannot be evaluated as measured benchmark runs')
    directory = Path(output_dir) / f"seed{output['seed']}"
    truth = json.loads((directory / 'ground_truth.json').read_text())
    metrics = evaluate(output, truth, kb, valid_line_ids=set(parse_logs(directory).event_id))
    path = Path(output_dir) / f"metrics_{output['system']}_seed{output['seed']}.json"
    path.write_text(json.dumps(metrics, indent=2))
    return metrics


def render_results(output_dir='outputs'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output_dir = Path(output_dir)
    metrics = [json.loads(p.read_text()) for p in sorted(output_dir.glob('metrics_*_seed*.json'))]
    if not metrics:
        raise ValueError('No evaluated run files exist')
    numeric = ['detection_recall', 'incident_precision', 'false_positives', 'mapping_accuracy',
               'a6_stages', 'hallucination_rate', 'invalid_evidence_rate', 'runtime_s', 'llm_calls']
    table = pd.DataFrame([{k: v for k, v in m.items() if k not in ['errors', 'detected_scenarios']} for m in metrics])
    table.to_csv(output_dir / 'results_by_seed.csv', index=False)
    table.groupby('system')[numeric].agg(['mean', 'std']).to_csv(output_dir / 'results_summary.csv')
    errors = [dict(system=m['system'], seed=m['seed'], **error) for m in metrics for error in m['errors']]
    pd.DataFrame(errors, columns=['system', 'seed', 'kind', 'item', 'matched_scenario', 'cause']).to_csv(output_dir / 'error_analysis.csv', index=False)
    figure, axes = plt.subplots(1, 3, figsize=(12, 4))
    summary = table.groupby('system')[numeric].mean()
    for axis, metric in zip(axes, ['detection_recall', 'false_positives', 'mapping_accuracy']):
        available = summary[metric].dropna()
        axis.set_title(metric.replace('_', ' '))
        if available.empty:
            axis.text(.5, .5, 'Not applicable', ha='center', va='center', transform=axis.transAxes)
            axis.set_xticks([])
        else:
            available.plot.bar(ax=axis, rot=0)
    figure.suptitle('Available measured systems')
    figure.tight_layout()
    figure.savefig(output_dir / 'comparison.png', dpi=160)
    plt.close(figure)
    figure, axis = plt.subplots(figsize=(6, 4))
    summary.hallucination_rate.plot.bar(ax=axis, title='Technique hallucination rate\nS1: nonexistent; S3: nonexistent or unretrieved', rot=0)
    axis.set_ylim(0, 1)
    if set(summary.index) == {'S0'}:
        axis.text(.5, .5, 'S0 makes no technique claims', ha='center', va='center', transform=axis.transAxes)
    figure.tight_layout()
    figure.savefig(output_dir / 'hallucinations.png', dpi=160)
    plt.close(figure)
    return table


def render_a6_demo(output_path, destination, *, output_dir='outputs'):
    from .pipeline import render_incident
    output = json.loads(Path(output_path).read_text())
    truth = json.loads((Path(output_dir) / f"seed{output['seed']}" / 'ground_truth.json').read_text())
    a6 = next(scenario for scenario in truth['scenarios'] if scenario['scenario_id'] == 'A6')
    findings = {f['finding_id']: set(f['evidence_line_ids']) for f in output['findings']}
    candidates = []
    for incident in output['incidents']:
        lines = set().union(*(findings.get(fid, set()) for fid in incident['finding_ids']))
        stages = sum(bool(lines & set(stage['line_ids'])) for stage in a6['stages'])
        if stages:
            candidates.append((stages, incident['incident_id']))
    if not candidates:
        raise ValueError('A6 was not detected; no A6 demonstration can be claimed')
    stages, identifier = max(candidates)
    rendered = render_incident(output_path, destination, incident_id=identifier)
    rendered += f'\n\nEvaluation: this incident covers {stages} of the A6 stages.\n'
    Path(destination).write_text(rendered)
    return rendered
