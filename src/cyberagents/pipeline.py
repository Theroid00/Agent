"""Offline batch orchestration, output provenance and held-out protection."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from .config import CONFIG, RETRIEVAL_QUERIES
from .generator import generate_logs
from .parser import parse_logs
from .prefilter import prefilter
from .baselines import rules_only, single_llm
from .attack_kb import build_kb
from .rag import AttackRAG, expand_query
from .llm import CachedLLM
from .agents import run_agents

ROOT = Path(__file__).resolve().parents[2]


def source_hash():
    content = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted((ROOT / 'src/cyberagents').glob('*.py'))}
    content['configuration'] = CONFIG
    content['requirements'] = hashlib.sha256((ROOT / 'requirements.txt').read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


def _seed_allowed(seed, directory, *, force=False):
    if seed == CONFIG['dev_seed']:
        freeze = directory / 'system_freeze.json'
        if freeze.exists() and json.loads(freeze.read_text())['source_hash'] != source_hash():
            raise RuntimeError('Frozen output directory belongs to an earlier revision; use a separate output_dir')
        return
    if seed not in CONFIG['held_out_seeds']:
        raise ValueError('Seed is outside the fixed benchmark catalog')
    freeze = directory / 'system_freeze.json'
    if not freeze.exists():
        raise RuntimeError('System freeze must be recorded before generating or running held-out seeds')
    record = json.loads(freeze.read_text())
    decisions = (ROOT / 'docs/decisions.md').read_text()
    if record['source_hash'] != source_hash() or f"### {record['decision_id']} — System freeze" not in decisions:
        raise RuntimeError('System freeze does not match current source/configuration and decision log')
    if force:
        raise RuntimeError('Held-out runs cannot be forced or retuned after System freeze')


def prepare_rag(kb=None):
    kb = kb or build_kb()
    directory = Path(CONFIG['paths']['index'])
    if (directory / 'metadata.json').exists():
        try:
            rag = AttackRAG.load(directory, expected_source_ref=kb['source_ref'])
        except ValueError as error:
            print(f'Rebuilding the disposable index cache: {error}')
            rag = None
    else:
        rag = None
    if rag is None:
        rag = AttackRAG(kb['techniques'], source_ref=kb['source_ref'])
        rag.save(directory)
    out = Path(CONFIG['paths']['out'])
    out.mkdir(parents=True, exist_ok=True)
    (out / 'attack_index_metadata.json').write_text(json.dumps({
        'source_ref': kb['source_ref'], 'model': CONFIG['embed_model'], 'technique_count': len(rag.ids),
        'embedding_dimension': rag.index.d, 'id_order': rag.ids,
        'model_revision': CONFIG['embed_revision'], 'document_settings': CONFIG['rag'],
    }, indent=2))
    return rag


def check_retrieval():
    rag = prepare_rag()
    rows = []
    for index, (query, accepted) in enumerate(RETRIEVAL_QUERIES):
        results = rag.search(query, k=CONFIG['rag']['k_tool'], finding_id=f'retrieval-test-{index}')
        ids = [r['id'] for r in results]
        rows.append({'query': query, 'expanded_query': expand_query(query), 'accepted': sorted(accepted),
                     'returned': ids, 'passed': bool(accepted & set(ids))})
    result = {'passed': sum(row['passed'] for row in rows), 'total': len(rows), 'queries': rows,
              'source_ref': rag.source_ref, 'model': CONFIG['embed_model'],
              'model_revision': CONFIG['embed_revision'], 'document_settings': CONFIG['rag'],
              'execution': 'sentence-transformers'}
    (Path(CONFIG['paths']['out']) / 'retrieval_check.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


def run_system(system, seed, *, output_dir=None, force=False, live=False, kb=None, rag=None, client=None, task_runner=None):
    if system not in {'S0', 'S1', 'S3'}:
        raise ValueError('System must be S0, S1 or S3')
    directory = Path(output_dir or CONFIG['paths']['out'])
    _seed_allowed(seed, directory, force=force)
    destination = directory / f'{system}_seed{seed}.json'
    if system != 'S0' and not destination.exists() and not live and task_runner is None:
        raise RuntimeError('Uncached LLM execution requires live=True and configured API credentials')
    if task_runner is not None and output_dir is None:
        raise ValueError('Mock runs require an explicit separate output directory')
    seed_dir = directory / f'seed{seed}'
    if not seed_dir.exists():
        generate_logs(seed, seed_dir)
    required = [seed_dir / name for name in ['auth.log', 'access.log', 'firewall.csv', 'asset_inventory.json']]
    if not all(path.exists() for path in required):
        raise ValueError('Incomplete synthetic dataset; restore missing files before running')
    fingerprint = hashlib.sha256((source_hash() + ''.join(hashlib.sha256(p.read_bytes()).hexdigest()
                                                          for p in required)).encode()).hexdigest()
    if destination.exists() and not force:
        cached = json.loads(destination.read_text())
        if cached.get('fingerprint') != fingerprint:
            raise ValueError('Cached run does not match current inputs/configuration; use force on seed 42 only')
        if cached.get('execution') == 'mock' and task_runner is None:
            raise ValueError('Cached run is a mock contract test, not a real system result')
        return cached
    if system != 'S0' and not live and task_runner is None:
        raise RuntimeError('Replacing an LLM run requires live=True')
    started = time.monotonic()
    events = parse_logs(seed_dir)
    clusters = prefilter(events)
    inventory = json.loads((seed_dir / 'asset_inventory.json').read_text())
    directory.mkdir(parents=True, exist_ok=True)
    if system == 'S0':
        output = rules_only(clusters, seed=seed)
    else:
        client = client or (CachedLLM() if task_runner is None else None)
        if system == 'S1':
            trimmed = [{k: v for k, v in c.items() if k != 'all_line_ids'} for c in clusters]
            output = single_llm(trimmed, inventory, client, seed=seed)
        else:
            kb = kb or build_kb()
            rag = rag or prepare_rag(kb)
            output = run_agents(clusters, inventory, kb, rag, client=client, seed=seed,
                                task_runner=task_runner, save_dir=directory / 'stages' / f'{system}_seed{seed}')
    execution = 'deterministic' if system == 'S0' else ('mock' if task_runner is not None or getattr(client, 'is_mock', False) else 'live')
    output.update(runtime_s=time.monotonic() - started, execution=execution, fingerprint=fingerprint,
                  source_hash=source_hash(), clusters=clusters, model=client.model if client else None,
                  attack_source_ref=CONFIG['attack']['commit'])
    temporary = destination.with_suffix('.tmp')
    temporary.write_text(json.dumps(output, indent=2))
    temporary.replace(destination)
    return output


def record_system_freeze(output_dir=None):
    """Freeze only after real dev execution and the retrieval/fast-suite checks."""
    directory = Path(output_dir or CONFIG['paths']['out'])
    dev = json.loads((directory / 'S3_seed42.json').read_text())
    retrieval = json.loads((directory / 'retrieval_check.json').read_text())
    if dev.get('execution') != 'live' or dev.get('source_hash') != source_hash():
        raise RuntimeError('A real current seed-42 S3 run is required before System freeze')
    if not dev.get('coverage', {}).get('complete', True):
        raise RuntimeError('Agent coverage is incomplete; cannot freeze')
    if (dev['runtime_s'] > 15 * 60 or retrieval['passed'] < 5
            or retrieval['source_ref'] != CONFIG['attack']['commit']
            or retrieval.get('model') != CONFIG['embed_model']
            or retrieval.get('model_revision') != CONFIG['embed_revision']
            or retrieval.get('document_settings') != CONFIG['rag']):
        raise RuntimeError('Runtime/retrieval exit checks have not passed')
    checked = subprocess.run([sys.executable, '-m', 'pytest', '-m', 'not live', '-q'], cwd=ROOT)
    if checked.returncode:
        raise RuntimeError('Fast suite failed; cannot freeze')
    from .evaluate import evaluate_saved
    metrics = evaluate_saved(directory / 'S3_seed42.json', build_kb(), output_dir=directory)
    if metrics['invalid_evidence_refs'] or metrics['nonexistent_technique_ids'] or metrics['unretrieved_technique_ids']:
        raise RuntimeError('Final grounding checks failed; cannot freeze')
    import re
    from datetime import datetime
    from zoneinfo import ZoneInfo
    freeze_date = datetime.now(ZoneInfo('Asia/Kolkata')).date().isoformat()
    decisions_path = ROOT / 'docs/decisions.md'
    decisions = decisions_path.read_text()
    number = max(map(int, re.findall(r'^### D(\d+) —', decisions, re.M))) + 1
    identifier = f'D{number}'
    entry = (f'### {identifier} — System freeze\n- **Date:** ' + freeze_date +
             f'\n- **Choice:** Freeze source/configuration SHA256 `{source_hash()}` after real dev execution, retrieval checks and fast pytest success.\n'
             '- **Impact:** Held-out seeds may now be generated and run without tuning. Git freeze tag must be created separately if metadata is read-only.\n\n')
    decisions = decisions.replace('## Entry template', entry + '## Entry template')
    index_row = f'| {identifier} | {freeze_date} | System freeze | Active |\n'
    decisions = decisions.replace('\n---\n\n## Pending decisions', '\n' + index_row + '\n---\n\n## Pending decisions', 1)
    decisions_path.write_text(decisions)
    record = {'decision_id': identifier, 'source_hash': source_hash(), 'dev_metrics': metrics}
    (directory / 'system_freeze.json').write_text(json.dumps(record, indent=2))
    return record


def render_incident(output_path, destination, *, incident_id=None):
    """Render a saved incident as text; action commands remain inert examples."""
    output = json.loads(Path(output_path).read_text())
    if output.get('execution') == 'mock':
        raise ValueError('A mock run cannot be presented as the demonstration incident')
    incidents = output.get('incidents', [])
    if not incidents:
        raise ValueError('No saved incident is available to render')
    if incident_id is not None:
        incident = next(i for i in incidents if i['incident_id'] == incident_id)
    else:
        incident = max(incidents, key=lambda i: len(i.get('kill_chain', [])))
    plans = {p['incident_id']: p for p in output.get('plans', [])}
    plan = plans.get(incident['incident_id'], {})
    lines = [f"# {incident['title']}", '', 'Synthetic-data demonstration; recommendations only.', '',
             f"Severity: {incident['severity']} | Confidence: {incident['confidence']}", '',
             plan.get('executive_summary', incident['rationale']), '', '## Timeline', '']
    for step in incident['kill_chain']:
        lines.append(f"- {step['ts_utc']}: {step['technique_id']} — {step['description']}")
    lines += ['', '## Recommended actions', '']
    for action in plan.get('immediate_actions', []):
        lines.append(f"- {action['priority']}: {action['action']} (target: {action['target']})")
        if action.get('example_command'):
            lines += ['', '```text', action['example_command'], '```', '']
    lines += ['', '## ATT&CK mitigations', '']
    lines.extend(f"- {m['mitigation_id']} {m['name']} → {m['for_technique_id']}" for m in plan.get('mitigations', []))
    Path(destination).write_text('\n'.join(lines) + '\n')
    return '\n'.join(lines)
