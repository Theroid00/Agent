# Multi-Agent Cyber-Threat Detection and Response

A college project that analyzes synthetic SSH, web and firewall logs using four CrewAI agents, MITRE ATT&CK retrieval and deterministic validators. It recommends response actions; it never executes them.

The owner-approved fresh V2 evaluation uses development seed 42 and held-out seeds 812399 and 876694. [System freeze D38](outputs/evaluation_v2/system_freeze.json) was committed at `a2e4246` and tagged `system-freeze-v2` / `benchmark-v2` before generating either fresh dataset. The separate [Windows evaluation notebook](notebooks/Cyber_Threat_MultiAgent.v2.evaluation.ipynb) reuses saved runs when available. Results are stored in outputs/evaluation_v2; original D33 and V2 development artifacts are preserved.

**Fresh evaluation is complete:** all 8 code cells in the [executed evaluation notebook](notebooks/Cyber_Threat_MultiAgent.v2.evaluation.executed.ipynb) completed; the full offline gate reports **82 passed, 1 deselected**. S3 recall is **1.0** and false positives **0** on both fresh seeds. Mapping accuracy is **0.9** on 812399 and **0.7** on 876694, so the second seed **misses the 0.8 mapping target**. A6 evidence coverage is **5** and **4** stages respectively; nonexistent/unretrieved IDs and invalid evidence references are **0**. Held-out means: S0 false positives **18.0**, S1 recall **0.41666666666666663** / mapping **0.6666666666666666**, S3 recall **1.0** / mapping **0.8**. The mean does not establish every seed passed. See the [measured report](outputs/evaluation_v2/report.md), [fresh-only table](outputs/evaluation_v2/held_out_results.csv), [target checks](outputs/evaluation_v2/target_checks.csv) and [mapping error analysis](outputs/evaluation_v2/mapping_error_analysis.md). This evaluates the same synthetic generator, not real-world logs.

The module implementation, a self-contained [Colab notebook](notebooks/Cyber_Threat_MultiAgent.ipynb) and a [notebook executed on Windows](notebooks/Cyber_Threat_MultiAgent.executed.ipynb) are included. The Windows notebook completed all 14 code cells, including live S1/S3 runs, frozen held-out evaluation and a real A6 report. Detection targets were missed; see the measured results and error analysis. Fresh-Colab verification remains pending. See [progress](docs/progress.md), [decisions](docs/decisions.md) and [problems](docs/problems.md).

The subsequent **coverage repair** is in the [executed V2 development notebook](notebooks/Cyber_Threat_MultiAgent.v2.executed.ipynb). All 7 cells completed, and the offline suite reports **82 passed, 1 deselected**. On the same development input bytes, S3 recall improved from 0.16666666666666666 to **1.0**, mapping accuracy from 0.8 to **0.9**, with **0 false positives**, **0 invalid evidence/nonexistent/unretrieved technique IDs**, and **5 A6 stages**. This is development evidence only; previously exposed held-out seeds were not rerun or used to claim new generalization. [Comparison](outputs/revision_v2/development_comparison.csv).

The original D33 outputs and executed notebook remain unchanged, with a verified source/results archive at outputs/frozen_d33_snapshot.zip. Revised output goes to outputs/revision_v2. The application protects old frozen output directories from revision writes; use the V2 notebook for the repaired development run.

## Run locally

### Windows

Double-click `setup-windows.cmd` to create `.venv`, install the pinned dependencies and create `.env` if absent. A new environment uses the installed Python launcher (`py -3.12`); an existing supported environment is reused. The setup checks dependency consistency and CLI startup. It uses a process-scoped PowerShell execution-policy override; no activation or permanent policy change is required.

From PowerShell in this folder:

```powershell
.\setup-windows.cmd --no-pause
.\run-notebook.cmd
.\run-local.cmd --help
.\run-local.cmd test
.\run-local.cmd prepare
```

`prepare` downloads the pinned knowledge base and embedding model, so the first run requires internet access. `test` runs the full non-live suite, including the retrieval check. The launcher sets the source path and Python UTF-8 mode, and changes to the repository directory. It works when launched from Explorer or another directory. CPU PyTorch wheels are selected explicitly on Windows.

Enter your Gemini key privately in `.env` and use `run-notebook.cmd` for the current frozen evaluation. The direct CLI defaults to the original output directory; that directory is deliberately protected by its D33 freeze. Programmatic revision runs must pass a separate output_dir. Preserve both earlier result directories.

To use the notebook locally, double-click `run-notebook.cmd`. It opens the executed V2 evaluation notebook when available, using the project's `.venv` kernel. Select **Run → Run All Cells** to verify the frozen source, run offline tests, reuse completed runs and regenerate tables/report. Missing held-out runs require the private API key and consume quota. The notebook never forces held-out reruns or retunes the system. It reads the key from `.env`; never put it in a cell. Setup installs JupyterLab through `requirements-notebook.txt`.

For a deliberately refreshed development output in a separate revision directory, the notebook uses force=True on development seed 42 only. The launcher also accepts the CLI's `evaluate`, `results` and other commands. Live runs consume API quota. No key is needed for setup or offline verification.

For direct Python commands in a PowerShell session, set the same environment first:

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONPATH = Join-Path $PWD 'src'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:NUMEXPR_NUM_THREADS = '1'
.\.venv\Scripts\python.exe -m cyberagents --help
```

### macOS / Linux

On the prepared Mac checkout, open `.env` beside this README and fill in `GEMINI_API_KEY=`. The file is ignored by Git. Then double-click `run-local.command` in Finder, or run `./run-local.command` from Terminal. It uses the existing project environment and runs S3 on development seed 42; a successful result is saved to `outputs/S3_seed42.json`. Groq is optional and can stay blank.

For a new installation, use Python 3.11–3.13. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export PYTHONPATH="$PWD/src"
cp -n .env.example .env
```

Add your Gemini key to the local `.env` file. Do not commit it or paste it into chat. The CLI loads `.env` without printing its values. Gemini is the default provider. Groq requires an explicit configuration change and a decision entry; it is never selected automatically.

```bash
python -m pytest -m "not live"
python -m cyberagents prepare
python -m cyberagents run --system S0 --seed 42
python -m cyberagents run --system S1 --seed 42 --live
python -m cyberagents run --system S3 --seed 42 --live
python -m cyberagents evaluate --system S0 --seed 42
python -m cyberagents evaluate --system S1 --seed 42
python -m cyberagents evaluate --system S3 --seed 42
python -m cyberagents results
```

`prepare` downloads the pinned ATT&CK data and configured embedding revision, builds the CPU FAISS index and prints the actual retrieval check. The documented fallback moved from MiniLM to BGE-small after real retrieval misses (D22/D23). A live key is unnecessary for embeddings. The `live` pytest marker makes API calls only when explicitly selected; absent keys produce an explicit skip. `slow` marks the real embedding/index test.

Saved output is reused only when its input/configuration/source fingerprint matches. For development output after a deliberate source change, use `--force` on seed 42. Raw downloads, indexes, model files and response caches are ignored by Git. The response cache includes provider, model, sampling settings, prompt and inputs in its key.

## Colab

Upload `notebooks/Cyber_Threat_MultiAgent.ipynb`, choose a CPU runtime, add `GEMINI_API_KEY` to Colab Secrets, allow notebook access and Run All. It embeds a snapshot of the Python modules/tests/docs and available measured outputs, so it does not need an unpublished repository URL. It installs requirements and imports ordinary module files. Only the notebook upload is needed in Colab; your local `.env`, virtual environment and project folder are not required. Set the key separately in Colab Secrets; the real `.env` is never embedded.

Regenerate the notebook after changing source, tests, documentation or saved outputs:

```bash
python scripts/build_notebook.py
```

All 14 code cells executed successfully on Windows with the owner's local key. The notebook runs the synchronous pipeline in a worker thread to support Jupyter's event loop. This does not establish that a fresh Colab run works; that verification remains pending. Saved fingerprints/freezes belong to the source/configuration used to produce them.

## Evaluation and freezes

Use seed 42 for development. Before held-out work, obtain real current S3 dev output, pass the retrieval check and offline suite, then record System freeze:

```bash
python -m cyberagents freeze-system
```

Only then run S0/S1/S3 on the held-out seeds listed in CONFIG, without force or tuning. The freeze records the source/configuration digest and a decision entry. The code refuses held-out generation/runs without a matching freeze. No held-out data is generated by the offline tests.

S0 produces one incident per rule cluster and has no mapping score. S1 uses one no-RAG prompt and retains its raw output. Its hallucination rate measures nonexistent IDs; S3 additionally measures retrieval violations. Total false positives include background, with a separate count for the fixed benign cases. Mapping is scored on detected scenarios/stages. The evaluator is the only production reader of ground truth.

Charts and tables are generated from saved evaluated files. A rules-only table is not a three-system comparison. An A6 report is rendered only from a real saved incident that overlaps A6 evidence; model-generated text is never substituted for measured results.

## Layout

- `src/cyberagents/`: configuration, KB/RAG, generator/parser, pre-filter, schemas/validators, evaluation, baselines, LLM cache, CrewAI stages and orchestration.
- `tests/`: deterministic contract tests, hand-scored evaluator cases, mock pipeline tests and explicitly marked integration checks.
- `outputs/`: generated logs, evaluation-only labels, measured runs/tables/charts and stage validation logs.
- `docs/`: goal, plan, state, decisions and failures.

The earlier build workflow exception is historical (D14). The newly supplied AGENTS.md test-review workflow governs future implementation (D36). The owner explicitly approved this fresh evaluation protocol (D37).

## Limitations and current verification

These are synthetic logs from a controlled environment, not evidence of real-world performance. The normal background is not calibrated from production traffic. Temperature zero and fixed seeds do not guarantee identical future provider behavior; saved responses preserve repeatability. Account-specific free-tier model availability and quotas must be checked before live execution. A live API failure is reported rather than silently switching providers.

The owner now authorizes local Git commits for completed and future milestones (D36). The Windows setup and development repair are saved in `203ba0c`; the pre-evaluation V2 freeze is `a2e4246`. Historical Git restrictions from the original Mac build are recorded in the project logs. Nothing is pushed without authorization.

## Measured Windows results

The full offline suite and freeze gate report **61 passed, 1 deselected**. The actual CrewAI contract test passes in this Windows environment, and the live notebook successfully calls Gemini. Installed dependency metadata is consistent. The original Mac credential-directory restriction remains documented as historical context.

Actual retrieval passes **6 of 6** fixed development queries with pinned BGE-small, FAISS, ATT&CK detection analytics, BM25 fusion and disclosed vocabulary normalization. This calibrated check does not establish general retrieval performance.

| Seed-42 rules-only measurement | Actual value |
|---|---|
| Parsed events | 26852 |
| Candidate clusters / incidents | 20 |
| Detected attacks | A1–A6; recall 1.0 |
| Incident precision | 0.45 |
| False positives | 11 total: 5 designed benign, 6 background |
| Most A6 stages in one incident | 2 |
| Mapping accuracy | Not applicable to S0 |
| Invalid evidence references | 0 |
| Runtime | 1.890999999945052 seconds |
| LLM calls | 0 |

The [per-seed results](outputs/results_by_seed.csv) contain 9 measured runs across S0/S1/S3. The [System freeze](outputs/system_freeze.json) was recorded under D33 before held-out execution. S3 reports detection recall 0.16666666666666666 on each seed, with 0 false positives and 0 invalid evidence or nonexistent/unretrieved technique IDs. Its mapping accuracy is 0.8 on development, 0.75 on one held-out seed and 0.8 on the other. The A6 chain is correlated, but other attack cases are missed; successful execution does not establish that the detection targets were met.

See [retrieval](outputs/retrieval_check.json), [error analysis](outputs/error_analysis.csv), the [real A6 report](outputs/demo_incident.md) and the [executed notebook](notebooks/Cyber_Threat_MultiAgent.executed.ipynb). The older outputs/verification.json describes the original Mac offline run. Fresh-Colab verification and the full submission checklist remain pending. No Git commit or tag was created during Windows setup/execution.
