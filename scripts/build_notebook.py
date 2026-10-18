"""Assemble the module-based, self-contained Colab submission notebook."""

import base64
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
stream = io.BytesIO()
paths = [ROOT / name for name in ['requirements.txt', 'pyproject.toml', '.env.example', 'README.md', 'run-local.command']]
for folder in ['src', 'tests', 'docs']:
    paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix in {'.py', '.md', '.json'})
if (ROOT / 'outputs').exists():
    paths.extend(p for p in (ROOT / 'outputs').rglob('*') if p.is_file() and p.suffix in {'.json', '.csv', '.png', '.log', '.md'})
with zipfile.ZipFile(stream, 'w') as archive:
    for path in sorted(set(paths)):
        info = zipfile.ZipInfo(str(path.relative_to(ROOT)), (1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, path.read_bytes())
payload = base64.b64encode(stream.getvalue()).decode()
cells = []


def md(text):
    cells.append({'cell_type': 'markdown', 'metadata': {}, 'source': text.splitlines(True)})


def code(text):
    cells.append({'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [], 'source': text.splitlines(True)})


md('''# Multi-Agent Cyber-Threat Detection and Response

A college project using CrewAI, MITRE ATT&CK retrieval and deterministic validators.
This notebook analyzes **synthetic data only**. Response commands are inert recommendations.

The offline implementation and the six fixed retrieval queries are tested locally. Live-model results and fresh-Colab verification remain pending until actually run. No S1/S3 performance is claimed from mock tests.

```text
Synthetic logs → parser → loose rules → Log Analyst → Threat Intel + RAG
                                           → Risk Assessor → Response Planner
                                                    ↓
                               saved output → ground-truth evaluation
```

Run the cells from top to bottom on a Colab CPU runtime. Add `GEMINI_API_KEY` to Colab Secrets and allow notebook access. `GROQ_API_KEY` is an optional manually selected backup. The notebook embeds the project files so an unpublished GitHub repository is not required.
''')
md('## 1. Setup, dependencies, secrets and configuration')
code('''import base64, importlib.metadata as metadata, io, json, os, pathlib, subprocess, sys, zipfile
try:
    from google.colab import userdata
    IN_COLAB = True
except ImportError:
    IN_COLAB = False
root = pathlib.Path('/content/cyber-threat-agents') if IN_COLAB else pathlib.Path.cwd()
if not IN_COLAB and root.name == 'notebooks':
    root = root.parent
if not (root / 'src/cyberagents').exists():
    root.mkdir(parents=True, exist_ok=True)
    archive = zipfile.ZipFile(io.BytesIO(base64.b64decode("""''' + payload + '''""")))
    for member in archive.infolist():
        target = (root / member.filename).resolve()
        if not target.is_relative_to(root.resolve()):
            raise ValueError('Unsafe archive member')
    archive.extractall(root)
os.chdir(root)
if IN_COLAB:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', '-r', 'requirements.txt'])
    for key in ['GEMINI_API_KEY', 'GROQ_API_KEY']:
        try:
            value = userdata.get(key)
            if value:
                os.environ[key] = value
        except userdata.SecretNotFoundError:
            pass
        except userdata.NotebookAccessError:
            print(f'Grant notebook access to {key} in Colab Secrets.')
else:
    if pathlib.Path('.env').exists():
        from dotenv import load_dotenv
        load_dotenv(override=False)
sys.path.insert(0, str(root / 'src'))
from cyberagents.config import CONFIG, CATALOG
RUN_LIVE = bool(os.environ.get({'gemini': 'GEMINI_API_KEY', 'groq': 'GROQ_API_KEY'}[CONFIG['llm']['provider']]))
print('Python:', sys.version.split()[0])
print('Live requests enabled:', RUN_LIVE)
print('Source:', CONFIG['attack']['commit'])
print('LLM:', CONFIG['llm']['provider'], CONFIG['llm']['model'])
from packaging.requirements import Requirement
for line in pathlib.Path('requirements.txt').read_text().splitlines():
    if not line.strip() or line.startswith(('#', '--')):
        continue
    requirement = Requirement(line)
    if requirement.marker and not requirement.marker.evaluate():
        continue
    name = requirement.name
    try:
        print(name, metadata.version(name))
    except metadata.PackageNotFoundError:
        print(name, 'NOT INSTALLED — install requirements.txt before live work')
''')
md('## 2. Pinned ATT&CK knowledge base and mitigation map')
code('''from cyberagents.attack_kb import build_kb, verify_catalog
kb = build_kb()
verify_catalog(kb)
print('Active techniques:', len(kb['techniques']))
print('Verified catalog IDs:', len(CATALOG))
print('Techniques with mitigation relationships:', len(kb['mitigations']))
''')
md('## 3. CPU embeddings, FAISS and semantic retrieval checks')
code('''from cyberagents.pipeline import check_retrieval
if IN_COLAB or RUN_LIVE:
    retrieval = check_retrieval()
    assert retrieval['passed'] >= 5, 'Retrieval target missed; record a decision before changing the index design.'
else:
    retrieval = None
    print('Real semantic retrieval is not executed in this offline notebook session. The saved retrieval check, where supplied, records the actual measured result.')
''')
md('## 4. Synthetic environment and seed-42 logs')
code('''from cyberagents.generator import generate_logs
seed_dir = pathlib.Path('outputs/seed42')
if not seed_dir.exists():
    generate_logs(42, seed_dir)
for name in ['auth.log', 'access.log', 'firewall.csv']:
    print(name, 'lines:', len((seed_dir / name).read_text().splitlines()))
print('Inventory:', json.loads((seed_dir / 'asset_inventory.json').read_text()))
# Ground-truth labels remain unread until the evaluation section.
''')
md('## 5. Parsing and UTC normalization')
code('''from cyberagents.parser import parse_logs
events = parse_logs(seed_dir)
print('Parsed events:', len(events))
display(events[['event_id', 'source', 'ts_utc', 'event_type', 'src_ip']].head())
''')
md('## 6. Deterministic candidate clusters')
code('''from cyberagents.prefilter import prefilter
clusters = prefilter(events)
print('Candidate clusters:', len(clusters))
print('Sample-size maximum:', max(len(c['sample_lines']) for c in clusters))
display(__import__('pandas').DataFrame([{k: c[k] for k in ['cluster_id', 'rule_ids', 'line_count', 't_start', 't_end']} for c in clusters]))
''')
md('## 7. Schemas, validators and the test-first benchmark harness')
code('''import inspect
from cyberagents import schemas, validators, evaluate
print(inspect.getsource(validators.validate_mappings))
checked = subprocess.run([sys.executable, '-m', 'pytest', '-m', 'not live', '-q'], text=True, capture_output=True)
print(checked.stdout)
if checked.returncode:
    print(checked.stderr)
    raise RuntimeError('Offline suite failed')
''')
md('## 8. CrewAI tasks, prompts, logged tools and cached requests')
code('''from cyberagents import agents, llm
print(json.dumps(agents.PROMPTS, indent=2))
print(inspect.getsource(llm.CachedLLM.text_call))
print('Each CrewAI task is validated before the next agent receives its output. Invalid items are retried once, then stripped and marked unvalidated.')
''')
md('## 9. Full-system seed-42 run and walkthrough')
code('''from cyberagents.pipeline import run_system
s3_path = pathlib.Path('outputs/S3_seed42.json')
s3 = run_system('S3', 42, live=RUN_LIVE) if RUN_LIVE or s3_path.exists() else None
if s3 is None:
    print('S3 not run: provide a Gemini key. No mock result is substituted.')
else:
    print(json.dumps({k: s3[k] for k in ['execution', 'runtime_s', 'llm_calls', 'tokens', 'cache_hits']}, indent=2))
    print(json.dumps(s3['incidents'], indent=2))
''')
md('## 10. S0 rules-only and S1 single-LLM baselines')
code('''s0 = run_system('S0', 42)
print('S0 incidents:', len(s0['incidents']))
s1_path = pathlib.Path('outputs/S1_seed42.json')
s1 = run_system('S1', 42, live=RUN_LIVE) if RUN_LIVE or s1_path.exists() else None
print('S1:', 'saved/live output available' if s1 else 'not run; API key required')
''')
md('## 11. System freeze and held-out evaluation runs')
code('''from cyberagents.pipeline import record_system_freeze
freeze_path = pathlib.Path('outputs/system_freeze.json')
if s3 is not None and retrieval is not None and not freeze_path.exists():
    print(json.dumps(record_system_freeze(), indent=2))
if freeze_path.exists():
    for seed in CONFIG['held_out_seeds']:
        for system in ['S0', 'S1', 'S3']:
            path = pathlib.Path(f'outputs/{system}_seed{seed}.json')
            if RUN_LIVE or path.exists():
                result = run_system(system, seed, live=RUN_LIVE)
                print(system, seed, result['execution'])
else:
    print('Held-out seeds remain untouched until a real current dev run and retrieval checks permit System freeze.')
''')
md('## 12. Evaluation, measured tables and charts')
code('''from cyberagents.evaluate import evaluate_saved, render_results
for path in sorted(pathlib.Path('outputs').glob('S*_seed*.json')):
    measured = evaluate_saved(path, kb)
    print(json.dumps({k: v for k, v in measured.items() if k != 'errors'}, indent=2))
table = render_results()
display(table)
from IPython.display import Image, Markdown, display
for name in ['comparison.png', 'hallucinations.png']:
    display(Image(filename=str(pathlib.Path('outputs') / name)))
print('S1 has no retriever: its hallucination rate measures nonexistent IDs; S3 also measures retrieval violations. S0 mapping is not applicable.')
''')
md('## 13. Error analysis')
code('''import pandas as pd
errors = pd.read_csv('outputs/error_analysis.csv')
display(errors)
print('Every missed scenario and false-positive incident is listed. Inspect the corresponding saved clusters, findings, candidates and validation logs to distinguish pre-filter, dismissal, retrieval, mapping and correlation errors.')
''')
md('## 14. Rendered A6 incident report')
code('''from cyberagents.evaluate import render_a6_demo
if s3 is not None:
    try:
        report = render_a6_demo('outputs/S3_seed42.json', 'outputs/demo_incident.md')
        display(Markdown(report))
    except ValueError as error:
        print(str(error))
else:
    print('No real S3 result yet; an A6 response report cannot be claimed.')
''')
md('''## 15. Conclusions and limitations

Use the measured table above to assess the targets from `docs/goal.md`. A missed target remains a missed target; do not tune after System freeze or replace held-out results.

The data is synthetic and does not establish real-world detection performance. LLM results can vary despite temperature zero; cached responses make repeated analysis reproducible. Rates and model availability depend on the provider account. S1 intentionally retains raw outputs for baseline measurement. All response commands are examples for human review; no action is executed.

A complete submission needs all systems across all catalog seeds, semantic retrieval checks, a real full-system run, error analysis, an A6 demonstration where detected, and a fresh-Colab Run All. Missing checks must remain labelled pending.
''')
notebook = {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                                      'language_info': {'name': 'python'}, 'colab': {'name': 'Cyber_Threat_MultiAgent.ipynb'}},
            'nbformat': 4, 'nbformat_minor': 4}
for cell in cells:
    if cell['cell_type'] == 'code':
        compile(''.join(cell['source']), '<notebook cell>', 'exec')
path = ROOT / 'notebooks/Cyber_Threat_MultiAgent.ipynb'
path.write_text(json.dumps(notebook, indent=1))
print('Notebook assembled:', path)
print('Code cells syntax-checked:', sum(cell['cell_type'] == 'code' for cell in cells))
print('Embedded project bytes:', len(stream.getvalue()))
