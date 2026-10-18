"""Build the local, development-only repair notebook; preserve the frozen run."""
from pathlib import Path
import ast
import nbformat as nbf

root = Path(__file__).resolve().parents[1]
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    compile(text, '<development notebook>', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    cells.append(nbf.v4.new_code_cell(text))


md('''# Coverage repair: development evaluation
This notebook evaluates the repaired agent hand-offs on development data only.
Original D33 results are preserved. This is a development comparison, not new unseen-test evidence.
API keys come from the ignored local `.env`. All response commands are inert recommendations.''')
code('''import asyncio, hashlib, json, os, pathlib, shutil, subprocess, sys, zipfile
ROOT = pathlib.Path.cwd()
if ROOT.name == 'notebooks':
    ROOT = ROOT.parent
os.chdir(ROOT)
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']:
    os.environ[name] = '1'
sys.path.insert(0, str(ROOT / 'src'))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env', override=False)
if not os.environ.get('GEMINI_API_KEY'):
    raise RuntimeError('Add GEMINI_API_KEY privately in .env before running.')
from cyberagents.config import CONFIG
RUN = ROOT / 'outputs/revision_v2'
RUN.mkdir(parents=True, exist_ok=True)
print('Revision:', CONFIG['system_revision'])
print('Model:', CONFIG['llm']['model'])
print('Development seed:', CONFIG['dev_seed'])
''')
md('## Regression and offline checks')
code('''checked = subprocess.run([sys.executable, '-m', 'pytest', '-m', 'not live', '-q'],
                         cwd=ROOT, text=True, capture_output=True)
print(checked.stdout.splitlines()[-1] if checked.stdout else checked.stderr)
if checked.returncode:
    print(checked.stdout, checked.stderr)
    raise RuntimeError('Offline checks failed')
''')
md('## Identical development inputs and pinned knowledge base')
code('''source_data = ROOT / 'outputs/seed42'
if not (RUN / 'seed42').exists():
    shutil.copytree(source_data, RUN / 'seed42')
for name in ['auth.log', 'access.log', 'firewall.csv', 'asset_inventory.json', 'ground_truth.json']:
    # Byte-preserving copy check only; labels are interpreted solely by the evaluator.
    assert hashlib.sha256((source_data / name).read_bytes()).digest() == hashlib.sha256((RUN / 'seed42' / name).read_bytes()).digest()
from cyberagents.attack_kb import build_kb
kb = build_kb()
print('Input bytes match the original development dataset.')
''')
md('## Repaired live agent run')
code('''from cyberagents.pipeline import run_system
# Refresh this development output; the provider response cache still reuses identical calls.
s3 = await asyncio.to_thread(run_system, 'S3', 42, output_dir=RUN, live=True, force=True)
print(json.dumps({key: s3[key] for key in ['execution', 'runtime_s', 'llm_calls', 'cache_hits', 'coverage']}, indent=2))
if not s3['coverage']['complete']:
    raise RuntimeError('Incomplete agent coverage; inspect revision_v2/stages before claiming success.')
''')
md('## Measured development comparison')
code('''from cyberagents.evaluate import evaluate_saved, render_results
import pandas as pd
from IPython.display import display, Image, Markdown
baseline = json.loads((ROOT / 'outputs/metrics_S3_seed42.json').read_text())
revised = evaluate_saved(RUN / 'S3_seed42.json', kb, output_dir=RUN)
columns = ['detection_recall', 'false_positives', 'mapping_accuracy', 'a6_stages',
           'invalid_evidence_refs', 'nonexistent_technique_ids', 'unretrieved_technique_ids', 'runtime_s', 'llm_calls']
comparison = pd.DataFrame([{**{key: row[key] for key in columns}, 'version': label}
    for label, row in [('D33 original', baseline), ('V2 development', revised)]]).set_index('version')
comparison.to_csv(RUN / 'development_comparison.csv')
display(comparison)
render_results(RUN)
import matplotlib.pyplot as plt
figure, axes = plt.subplots(1, 3, figsize=(12, 4))
for axis, metric in zip(axes, ['detection_recall', 'false_positives', 'mapping_accuracy']):
    comparison[metric].plot.bar(ax=axis, rot=0, color=['#9ca3af', '#2563eb'])
    axis.set_title(metric.replace('_', ' '))
    axis.set_xlabel('')
figure.suptitle('Development seed: original versus coverage repair')
figure.tight_layout()
figure.savefig(RUN / 'development_comparison.png', dpi=160)
plt.close(figure)
display(Image(filename=str(RUN / 'development_comparison.png')))
print('Development comparison only; previously exposed held-out seeds were not rerun.')
''')
md('## Real incident report')
code('''from cyberagents.evaluate import render_a6_demo
try:
    report = render_a6_demo(RUN / 'S3_seed42.json', RUN / 'demo_incident.md', output_dir=RUN)
    display(Markdown(report))
except ValueError as error:
    print(str(error))
''')
md('## Original results preserved')
code('''with zipfile.ZipFile(ROOT / 'outputs/frozen_d33_snapshot.zip') as snapshot:
    manifest = json.loads(snapshot.read('frozen_manifest.json'))
    original_files = {name: digest for name, digest in manifest['files'].items()
                      if name.startswith(('outputs/', 'notebooks/'))}
    for name, digest in original_files.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
print('Original output/notebook files unchanged:', len(original_files))
print('No revised held-out evaluation or new freeze was performed.')
''')
notebook = nbf.v4.new_notebook(cells=cells, metadata={'kernelspec': {
    'display_name': 'Python (.venv)', 'language': 'python', 'name': 'python3'}})
destination = root / 'notebooks/Cyber_Threat_MultiAgent.v2.ipynb'
nbf.validate(notebook)
nbf.write(notebook, destination)
print('Development notebook:', destination)
print('Code cells:', sum(cell.cell_type == 'code' for cell in cells))
