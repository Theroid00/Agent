# DECISIONS — Multi-Agent Cyber-Threat Detection and Response System

> Every decision that shapes the project, with the options considered and **why** the choice was made.
> Covers design choices, version pins, threshold/prompt changes, scope changes, test fixes, and benchmark/system freezes.
> **Never delete an entry.** If a decision is reversed, add a new one and mark the old one "Superseded by D#".
> If a decision changes `goal.md`, also add a row to goal.md's Change Log.

---

## Index

| # | Date | Decision | Status |
|---|------|----------|--------|
| D1 | 2026-10-18 | Project #1: Multi-Agent Cyber-Threat Detection and Response | Active |
| D2 | 2026-10-18 | Synthetic logs instead of public datasets | Active |
| D3 | 2026-10-18 | Deterministic pre-filter before the LLM | Active |
| D4 | 2026-10-18 | Closed-set technique selection | Active |
| D5 | 2026-10-18 | Response agent recommends only | Active |
| D6 | 2026-10-18 | Gemini free tier primary, Groq fallback | Active |
| D7 | 2026-10-18 | RFC 5737 documentation IPs for all external addresses | Active |
| D8 | 2026-10-18 | Test-first development | Active |
| D9 | 2026-10-18 | Dev / held-out seed split | Active |
| D10 | 2026-10-18 | Documentation in `docs/` (progress, decisions, problems) | Active |
| D11 | 2026-10-18 | Timeline 7 → 8 days | Active |
| D12 | 2026-10-18 | Python modules in src/ with pytest; notebook assembled in Phase 7 | Active |
| D13 | 2026-10-18 | Commits per green test group and phase/freeze tags | Active |
| D14 | 2026-10-18 | Human authorizes full build using goal, plan and decisions; set aside AGENTS workflow | Historical; workflow superseded by D36 |
| D15 | 2026-10-18 | Offline development and explicit pending live/Colab verification | Active |
| D16 | 2026-10-18 | Pin MITRE CTI source and verify its content hash | Active |
| D17 | 2026-10-18 | Direct dependency pins and current free-tier Gemini model | Active |
| D18 | 2026-10-18 | Staged CrewAI validation and explicit baseline metric semantics | Active |
| D19 | 2026-10-18 | Preserve terminal sample events and control normal background failure frequency | Active |
| D20 | 2026-10-18 | Self-contained notebook imports an embedded snapshot of the module project | Active |
| D21 | 2026-10-18 | Isolate CPU embedding from the FAISS native runtime | Active |
| D22 | 2026-10-18 | Clean retrieval documents after the measured MiniLM miss | Active |
| D23 | 2026-10-18 | Use the planned BGE-small fallback after MiniLM cleaning remained below target | Active |
| D24 | 2026-10-18 | Resolve the pinned STIX detection-strategy/analytic schema | Active |
| D25 | 2026-10-18 | Use the planned BM25+dense reciprocal-rank fusion fallback | Active |
| D26 | 2026-10-18 | Normalize security vocabulary in natural-language retrieval queries | Active |
| D27 | 2026-10-18 | Resolve transitive dependency conflict; keep project storage local and report framework import restriction | Active |
| D28 | 2026-10-19 | Local key file and Mac launcher; keep Colab secrets independent | Active |
| D29 | 2026-10-19 | Configure the cloned checkout for Windows without Git commits | Windows setup active; commit restriction superseded by D36 |
| D30 | 2026-10-19 | Owner supplies a local key and authorizes running the notebook | Active |
| D31 | 2026-10-19 | Preserve CSV writer newlines on Windows | Active |
| D32 | 2026-10-19 | Run synchronous pipeline calls outside Jupyter's event loop | Active |

| D33 | 2026-10-19 | System freeze | Active |
| D34 | 2026-10-19 | Development coverage repair; preserve D33 baseline | Active |
| D35 | 2026-10-19 | Evidence-focused login retrieval and per-record retry salvage | Active |
| D36 | 2026-10-19 | Owner authorizes committing completed work and future milestones | Active |

---

## Pending decisions (to make on build day; Phase 1)

- [x] CrewAI 1.15.28 installed with a metadata-consistent dependency closure; actual framework execution blocked by per-user credential storage (P8)
- [x] Gemini 3.5 Flash-Lite selected from current provider docs; account verification pending
- [x] ATT&CK commit and SHA256 pinned (D16)
- [x] pytest (D12), with tests written before implementation
- [x] Pinned BGE-small plus hybrid retrieval and explicit normalization passes the fixed development check (D23–D26)

---

## Entries

### D1 — Project choice: #1 Multi-Agent Cyber-Threat Detection and Response (CrewAI + RAG)
- **Date:** 2026-10-18
- **Options considered:** #2 Phishing detection (easiest, but common among students and judged too simple); #12 Code generation, testing and review (strong but agent coding tutorials are widespread); #14 Smart agriculture (unique but hard to evaluate); #1 Cyber-threat detection.
- **Choice:** #1
- **Why:** Most depth for the effort. RAG has a real job (MITRE ATT&CK knowledge base). Multi-stage attack correlation is a genuinely agentic task, few classmates will attempt it, and it can be measured against ground truth.
- **Impact:** ~8 days of work; RAG and log generator are the heaviest parts.

### D2 — Synthetic logs instead of public datasets
- **Date:** 2026-10-18
- **Options considered:** public IDS/log datasets; honeypot logs; synthetic generation.
- **Choice:** Synthetic, seeded generator.
- **Why:** Exact line-level ground truth; we control tricky benign cases (B1–B5); reproducible; no licensing issues; fits free Colab.
- **Impact:** Results don't prove real-world performance. Must be stated as a limitation. Confirm acceptability with instructor.

### D3 — Deterministic pre-filter before the LLM
- **Date:** 2026-10-18
- **Options considered:** send raw logs to the LLM; ML anomaly detector; rule-based pre-filter.
- **Choice:** Loose rule-based pre-filter producing clusters.
- **Why:** ~20k lines don't fit in context or free-tier limits. Rules make recall measurable and testable. Kept deliberately loose so benign look-alikes reach the agents.
- **Impact:** System recall is capped by pre-filter recall, so T-RULES requires 100% recall on all scenarios.

### D4 — Closed-set technique selection
- **Date:** 2026-10-18
- **Options considered:** let the agent name techniques freely; RAG tool only; pre-retrieved candidates + logged tool calls.
- **Choice:** Pre-retrieved top-8 candidates per finding plus logged `search_attack` calls; only those IDs are allowed.
- **Why:** Stops technique IDs from model memory (main hallucination risk) and makes grounding checkable in code.
- **Impact:** If retrieval misses the right technique, the agent can't pick it. Mitigated by retrieval tests and the agent's own searches.

### D5 — Response agent recommends only
- **Date:** 2026-10-18
- **Choice:** Playbooks with example commands; nothing is executed.
- **Why:** Safety; acting on systems is out of scope.
- **Impact:** None on evaluation.

### D6 — Gemini free tier primary, Groq fallback
- **Date:** 2026-10-18
- **Options considered:** paid APIs; local models in Colab; free-tier APIs.
- **Choice:** Gemini free tier, Groq as fallback.
- **Why:** ₹0 budget; no GPU needed; local models in free Colab are slow and memory-limited.
- **Impact:** Must design around rate limits (batching, throttling, caching outputs). Exact model name decided on build day.

### D7 — RFC 5737 documentation IPs
- **Date:** 2026-10-18
- **Choice:** External IPs only from `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`.
- **Why:** Avoids accidentally using real people's or organizations' IPs.
- **Impact:** Checked by T-DATA.

### D8 — Test-first development
- **Date:** 2026-10-18
- **Options considered:** build agents then test; write all tests on day 1; write each component's tests before that component.
- **Choice:** Tests before each component. The full harness (pre-filter tests, schemas, validators, golden-tested evaluation) is built and proven on mock data before any agent exists.
- **Why:** If agents come first, tests and metrics tend to get shaped around whatever the agents happen to output. Writing all tests on day 1 isn't possible because the data and schemas don't exist yet. Testing the evaluation harness itself (perfect/bad golden outputs) means the scores can be trusted.
- **Impact:** Phase 3 takes 2 days; agents start Day 5. Tests may never be edited to pass; test fixes need a decision entry.

### D9 — Dev / held-out seed split
- **Date:** 2026-10-18
- **Choice:** Tune on seed 42 only. Seeds 7 and 2026 run once, after System freeze.
- **Why:** Test-first alone doesn't stop overfitting. Tuning prompts on the same data you score on inflates results.
- **Impact:** Held-out numbers may be lower than dev; they're reported as they come out.

### D10 — Documentation structure
- **Date:** 2026-10-18
- **Choice:** `docs/` with `goal.md`, `plan.md`, `progress.md`, `decisions.md`, `problems.md`. `progress.md` gets a session entry plus updated **Current** and **What's next** at the end of every session.
- **Why:** Work spans many sessions (and possibly AI assistants without memory). A written state prevents drift, repeated mistakes and invented results.
- **Impact:** A few minutes of upkeep per session.

### D11 — Timeline 7 → 8 days
- **Date:** 2026-10-18
- **Choice:** Phase 3 (test & benchmark harness) gets 2 days.
- **Why:** Test-first harness is more work up front but saves debugging later.
- **Impact:** Cut list in plan.md §10 never includes tests or freezes.

---

### D12 — Python modules with pytest; notebook assembled in Phase 7
- **Date:** 2026-10-18
- **Phase:** Setup
- **Options considered:** Notebook-first development in plan.md §9; plain Python modules with pytest under AGENTS.md §3.
- **Choice:** Code lives in `src/cyberagents/` as `.py` modules; tests live in `tests/` and run with pytest. Assemble `notebooks/Cyber_Threat_MultiAgent.ipynb` in Phase 7, importing the modules.
- **Why:** Explicit setup instruction; plain modules support readable diffs and a reviewable test-first workflow.
- **Impact / trade-offs:** AGENTS.md overrides plan.md §9 on code layout. Preserve the notebook's section order for the final presentation. Setup placeholders contain docstrings only; Phase 1 implementation and test behavior are deferred.

### D13 — Commits per green test group and phase/freeze tags
- **Date:** 2026-10-18
- **Phase:** Setup
- **Options considered:** Commits only at phase boundaries; commits after each green test group and at phase end.
- **Choice:** Commit at least after each test group goes green and at each phase end, using `phase<N>: <what>` for phase work. Tag phase completion as `phase<N>-done`, Benchmark freeze as `benchmark-v1`, and System freeze as `system-freeze`.
- **Why:** Explicit setup instruction; preserve reviewable checkpoints and identifiable benchmark/system freezes.
- **Impact / trade-offs:** Setup uses the requested `setup: repo skeleton and docs` initial commit followed by a documentation commit. No phase or freeze tag is due during setup. Actual initialization and commits are currently blocked by managed permissions (P3).

---

### D14 — Human changes the session scope and workflow
- **Date:** 2026-10-18
- **Choice:** The owner explicitly requested the entire project and then instructed: “forget agenst md adn follow the rest of the docs”. Follow goal.md, plan.md and this decision log. Keep the src/ module layout and pytest from D12. Write tests before implementation, without the per-phase human-review pauses imposed by AGENTS.md.
- **Impact:** The setup-only restriction is superseded. Do not use AGENTS.md to impose additional approval gates. Its file remains preserved for history.

### D15 — Continue offline development; preserve honest verification status
- **Date:** 2026-10-18
- **Choice:** Build and test components locally even where external phase exit checks cannot yet run. Record live Gemini/Groq, real embedding retrieval and fresh-Colab checks as pending until actually performed; never label mocked runs as S3 benchmark results.
- **Why:** Neither GEMINI_API_KEY nor GROQ_API_KEY is set. Package-manager network access failed. Git metadata remains read-only in this session.
- **Impact:** Implement the project without claiming its Definition of Done. Preserve D9: use seed 42 for development; leave held-out runs until a recorded System freeze. The plan's early all-seed exit checks remain pending rather than silently treating them as passed.

### D16 — Pin the official ATT&CK data source
- **Date:** 2026-10-18
- **Choice:** MITRE CTI commit `50be388e93819a5d20e71cbaaeccfda157abc846`, file `enterprise-attack/enterprise-attack.json`; downloaded SHA256 `66f3fe3f07ef1a2de0bd2fe4b3e8a9ea06c1d0bb2c46171bdbb57c7f7b666524`.
- **Evidence:** GitHub commit API and SHA256 calculated from the downloaded file. The parser printed 26689 STIX objects before filtering.
- **Impact:** Verify the hash before use; ignore raw downloads and rebuild the index. Verify scenario IDs/names against these pinned bytes.

---

### D17 — Dependency/runtime pins and the primary model
- **Date:** 2026-10-18
- **Choice:** Exact direct pins are in requirements.txt, taken from installed metadata or the PyPI release metadata, not memory. CrewAI 1.15.28 requires Pydantic below 2.13; selected and installed Pydantic 2.12.5 with pydantic-core 2.41.5 locally. Local Python is 3.13.9; fresh Colab compatibility remains to be tested.
- **Model:** Gemini `gemini-3.5-flash-lite`, temperature zero. Google's current documentation limits 2.5 Flash to existing users and lists 3.5 Flash-Lite as a new-project model with free input/output pricing. Account availability and rate limits are unverified without a key. Groq `llama-3.3-70b-versatile` is an explicit configured backup, never an automatic switch; its account quota/pricing must be checked before use.
- **Embeddings:** MiniLM revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, obtained from the official Hugging Face model API. Cache/index metadata records that revision.
- **Sources:** https://pypi.org/project/crewai/1.15.28/ ; https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite ; https://ai.google.dev/gemini-api/docs/pricing ; https://console.groq.com/docs/models ; https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- **Impact:** A bulk package install failed on DNS. Public official wheels are being installed locally for available integration checks. Registry-selected pins are not a claim that the full CrewAI dependency set has been installed and verified.

### D18 — Validate between CrewAI stages; make evaluation interpretations explicit
- **Date:** 2026-10-18
- **Choice:** Execute the four CrewAI agents as sequential isolated task executions. Validate each result before constructing the next task's context, perform Python pre-retrieval between Analyst and Threat Intel, retry once with errors, then strip invalid items and mark them unvalidated. Every provider call uses the same cached client. This replaces a single uninterrupted crew kickoff while preserving the four-agent pipeline.
- **Why:** Invalid outputs must never become a later agent's context; pre-retrieval needs the validated findings first.
- **Evaluation:** S1 is the plan's raw no-RAG experimental baseline. Its hallucination rate measures nonexistent IDs; absence of retrieval is not a meaningful failure for a system with no retriever. S3 measures nonexistent or unretrieved choices. S0 has no mapping score. False-positive totals include unlabeled background as defined in plan §8.1. Deterministic incident-match ties use scenario ID order, and empty evidence does not detect an attack. Only evidenced A6 stages enter stage mapping accuracy. Golden perfect/bad outputs were written before evaluator implementation.
- **Ambiguity:** goal R1's broad wording versus intentionally raw S1 artifacts remains documented in P2; no goal text was silently changed. Final S3 grounding guarantees do not describe raw experimental traces.
- **Impact:** Mock pipeline outputs are explicitly marked and refused by saved benchmark evaluation. Chain timestamps must be timezone-aware. Failed mappings mark their corresponding finding unvalidated.

### D19 — Candidate budget and sample coverage on the development seed
- **Date:** 2026-10-18
- **Choice:** Spread the maximum ten displayed lines across each candidate's time range, including the endpoints. Keep successful-login evidence visible after a longer failure burst.
- **Evidence:** The new success-sampling test failed because the accepted login was outside the first ten lines, then passed after range sampling.
- **Background setting:** The initial normal-auth failure probability was 0.04. The first full-volume seed-42 run produced 100 clusters and failed the plan's less-than-40 budget. Configure normal-background failures as 0.004 while retaining all background line counts and every injected A/B scenario; the new full-volume budget test passes. Rule thresholds and accepted attack techniques are unchanged. No held-out seed was generated or inspected.
- **Impact:** Regenerate seed-42 synthetic files and S0 measurements after this pre-freeze development change. Log this modeling limitation; the background is synthetic, not calibrated to a real server.

### D20 — Portable notebook with module imports
- **Date:** 2026-10-18
- **Choice:** Assemble the final notebook using scripts/build_notebook.py. It embeds a compressed source/test/docs snapshot plus available measured outputs, extracts ordinary module files in a fresh Colab workspace, installs requirements and imports from src/.
- **Why:** No GitHub remote has been supplied. A self-contained notebook can start with only Colab API secrets, without an unfilled clone URL or notebook-contained development code.
- **Impact:** Regenerate the notebook after source/docs/output changes. The archive excludes .env, keys, downloaded models, raw ATT&CK data, FAISS indexes and LLM response caches. A syntax/schema check is not fresh-Colab execution; that remains pending.

---

### D21 — Isolate native embedding and FAISS runtimes
- **Date:** 2026-10-18
- **Evidence:** Combined embedding/index execution first exited with code 139. Setting both libraries to one thread then produced `OMP: Error #15: Initializing libomp.dylib, but found libomp.dylib already initialized.` Standalone one-thread CPU embedding succeeded with shape (1, 384).
- **Choice:** Encode in a small Python subprocess that imports PyTorch/sentence-transformers but never FAISS. Keep the actual FAISS index in the parent. Pin embedding/FAISS thread count to one. No duplicate-OpenMP override or binary patch is used.
- **Impact:** Repeated model loading adds runtime overhead, to be measured in real runs. The slow retrieval test checks package availability without importing PyTorch into the FAISS test process; no assertion or acceptance threshold was weakened. Primary project sources: https://github.com/facebookresearch/faiss/wiki/Threads-and-asynchronous-calls and https://github.com/faiss-wheels/faiss-wheels/issues/40 .

### D22 — Retrieval fallback: clean the document representation
- **Date:** 2026-10-18
- **Evidence:** Actual pinned MiniLM/FAISS retrieval passed 3 of 6 fixed queries. Port discovery, SQL injection and outbound transfer missed their required top-five IDs. This is a measured failure, not a mock result.
- **Choice:** Apply the first fallback in plan §5.3: strip citation/link/HTML markup, keep the ID/name and focus embedding text on the description instead of long platform/tactic lists. Keep those metadata fields in retrieval results. Preserve all query strings, accepted IDs, the top-five bound and the five-of-six target.
- **Impact:** Record the document settings in index metadata and rebuild incompatible caches. If cleaning is insufficient, continue with the documented bge-small/hybrid fallbacks and log the result.

---

### D23 — Planned BGE-small retrieval fallback
- **Date:** 2026-10-18
- **Evidence:** Cleaning MiniLM documents improved the fixed top-five check from 3 of 6 to 4 of 6. Port discovery and SQL injection still missed their accepted IDs.
- **Choice:** Use `BAAI/bge-small-en-v1.5` at revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`, the next fallback explicitly listed in plan §5.3. Follow its model card: prefix retrieval queries with the recommended instruction; leave documents unprefixed. Queries, accepted technique IDs, top-five limit and pass threshold remain unchanged.
- **Source:** https://huggingface.co/BAAI/bge-small-en-v1.5
- **Impact:** Rebuild the index and measure the same fixed check. Keep both MiniLM results as diagnostic evidence. Do not generate held-out data or change the benchmark to match retrieval output.

---

### D24 — Extract modern detection-strategy analytics from the pinned data
- **Date:** 2026-10-18
- **Evidence:** BGE with description-only documents passed 3 of 6. Inspection of the pinned STIX bundle found that detection information uses `detects` relationships from active `x-mitre-detection-strategy` objects and `x_mitre_analytic_refs`, rather than the legacy `x_mitre_detection` field. The initial parser omitted that operational text.
- **Choice:** Complete plan §5.1's version-aware detection extraction: follow active strategy/analytic references and include their original names/descriptions in each technique record. Keep legacy detection text when present. Embed the cleaned detection text as well as the description, with bounds in CONFIG; no scenario-specific synonyms or expected IDs are injected.
- **Impact:** Add a fixture test for modern active analytics and deprecated-analytic filtering before implementation. Rebuild the KB/index and run the unchanged six-query check before considering an additional BM25 dependency. Keep the previous real retrieval reports under outputs/diagnostics/.

---

### D25 — Planned hybrid BM25 plus dense retrieval
- **Date:** 2026-10-18
- **Evidence:** Version-aware detection text improved BGE retrieval from 3 of 6 to 4 of 6. Port discovery and outbound transfer still missed the fixed accepted top-five IDs.
- **Choice:** Apply plan §5.3's hybrid fallback using rank-bm25 0.2.2, verified against its registry metadata and project documentation. Fuse dense and lexical rankings with equal reciprocal-rank contributions and a configured rank constant of 60. Lexical tokenization lowercases, removes common grammatical words and normalizes simple plurals; it never maps a query to a hand-coded technique ID. Credit only positive lexical matches.
- **Impact:** Preserve all fixed queries, accepted IDs and thresholds. Keep cosine score and fused rank score separate in returned results. Record the policy in configuration/retrieval reports. Add a test proving lexical retrieval can recover a relevant document when the injected dense vectors disagree. Keep the measured dense-only failures under outputs/diagnostics/.
- **Source:** https://github.com/dorianbrown/rank_bm25

---

### D26 — Explicit security-vocabulary normalization for retrieval
- **Date:** 2026-10-18
- **Evidence:** Equal-rank dense/BM25 fusion still passed 4 of 6 fixed queries. Lexical port-discovery retrieval placed T1046 fifth, but the dense ranking pulled it below the final top five. The outbound-transfer query also missed its accepted parent techniques.
- **Choice:** Preserve the original query and append ordinary security vocabulary for two broad observable concepts: connections to many/multiple/distinct ports are network port scanning; outbound data/traffic transfer is data exfiltration. This is query normalization, not a rule returning technique IDs. Use the normalized text for both dense and lexical search and include it in the measured retrieval report.
- **Impact:** No ID, scenario label, accepted set or test threshold is inserted or changed. The six public retrieval checks are development/calibration cases; their pass rate is not a generalization claim. A contract test verifies that normalization preserves the original input and never injects an ATT&CK ID. No held-out generator output or system result has been inspected.
- **Measured result:** Final real BGE/FAISS/hybrid check passed 6 of 6; saved in outputs/retrieval_check.json, with expanded queries disclosed.

---

### D27 — Runtime dependency compatibility and local storage
- **Date:** 2026-10-18
- **Evidence:** The latest transitive Kubernetes dependency required Pydantic >=2.13.5, conflicting with crewai-core's Pydantic <2.13 requirement and our exact 2.12.5 pin. Installed package metadata was inspected before changing pins.
- **Choice:** Pin kubernetes==36.0.2, whose official version metadata has no Pydantic requirement, alongside the direct/runtime pins. Active dependency-closure inspection now reports no missing/incompatible requirements. Google GenAI and Groq SDKs import successfully. Requirements use the official PyTorch CPU wheel index on Linux to avoid an unnecessary CUDA install.
- **Storage:** Set CREWAI_STORAGE_DIR to the project's ignored .cache/crewai before import, disable tracing and telemetry. crewai-core independently attempts a per-user credentials directory; the managed environment denies it (P8). Do not patch authentication code or bypass filesystem permissions. The real framework test explicitly skips that specific permission failure; stage contract tests do not establish real CrewAI execution.
- **Impact:** Fresh Colab installation and framework execution remain exit checks. No live key/call is claimed. The owner subsequently chose offline results only for this session.

### D28 — Prepare local key entry and a minimal Mac launcher
- **Date:** 2026-10-19
- **Choice:** Create .env only if absent, preserve existing contents, restrict its permissions to owner read/write, and keep it ignored by Git. Supply empty GEMINI_API_KEY/GROQ_API_KEY fields; the user enters the key privately.
- **Launcher:** run-local.command changes to the project folder, uses the existing .venv and source path, and delegates to the existing CLI for the development S3 run. No new pipeline or environment bootstrap is introduced. The launcher is included in the notebook's project snapshot, while the actual .env is excluded.
- **Verification:** Shell syntax and CLI help smoke checks passed without API calls. Notebook payload/schema/file-equality checks are repeated after rebuilding. Colab reads its own Secrets, independently of the local .env. Prior live/Colab validation limitations remain.

### D29 — Windows setup and launchers
- **Date:** 2026-10-19
- **Authorization:** Owner requested cloning the GitHub repository and configuring it for Windows, with no Git commits. This supersedes commit requirements for this session.
- **Choice:** Reuse the installed Windows Python through a project-local virtual environment. Add setup-windows.cmd/setup-windows.ps1 and run-local.cmd; set Python UTF-8 mode and the src path without requiring environment activation. Preserve an existing .env and create only blank fields when absent. Use explicit CPU PyTorch pins on Windows as on Linux.
- **Portability:** Build notebook archive member names with POSIX separators so Windows-built notebooks extract correctly on Colab. Include Windows launchers in the embedded snapshot. No benchmark, model, threshold or approved test change is intended.
- **Verification:** Installation and Windows offline validation are in progress; actual results will be recorded in progress.md. No live API call, held-out run, freeze, commit or tag is authorized by this setup request.

### D30 — Run the notebook with the owner's local key
- **Date:** 2026-10-19
- **Authorization:** The owner requested adding an API key and running the notebook, then confirmed the key was saved in .env. Live execution is now authorized for this notebook; keep keys out of chat, notebook sources, output and Git.
- **Choice:** Install JupyterLab through a separate requirements-notebook.txt, register the project-local kernel, and supply run-notebook.cmd. Refresh the deterministic development S0 output for this checkout's source fingerprint. The notebook's existing freeze and held-out safeguards remain in effect.
- **Runtime:** A headless execution completed the setup/KB cells and hit P12 while another notebook server/kernel was also building embeddings. Observed that existing session until its server and workers stopped without an index. Retried with a single kernel and OMP/OpenBLAS/MKL/NumExpr threads limited to one before native imports, matching the configured embedding limit. Apply the limits in the Windows launchers and the notebook's setup cell. Save completed cells to a separate executed notebook and redact local API keys from saved outputs.
- **Git:** No commits or tags, per the owner's standing instruction.

### D31 — Prevent doubled CSV newlines on Windows
- **Date:** 2026-10-19
- **Evidence:** Existing approved parser contract failed with `assert 5972 == 11829` on Windows, while the remaining suite passed. csv.writer emits CRLF into StringIO; Path.write_text's default Windows translation then changes LF to CRLF again, producing CR-CR-LF.
- **Choice:** Write the generated log buffer with newline='' to preserve its existing line endings. Keep every scenario, seed, event ID, threshold and approved test unchanged. The existing test provides the failing-before regression check.
- **Verification:** Run the unchanged parser test, then rerun the notebook's full offline suite and subsequent live cells. No System freeze or held-out run has occurred before this fix.

### D32 — Notebook integration with CrewAI's running-event-loop restriction
- **Date:** 2026-10-19
- **Evidence:** Notebook test gate reported `61 passed, 1 deselected, 26 warnings in 53.61s`, but the live S3 cell failed with the running-event-loop RuntimeError logged in P14. Inspected installed crewai/agent/core.py: the synchronous entry point explicitly rejects an awaitable invoke result.
- **Choice:** Keep the tested synchronous pipeline/CLI unchanged. Invoke development S1/S3 and held-out pipeline calls with await asyncio.to_thread in notebook cells. Compile cells with ast.PyCF_ALLOW_TOP_LEVEL_AWAIT during notebook assembly.
- **Impact:** Framework execution runs outside Jupyter's active event loop. Providers, prompts, schemas, response cache, evaluation and freeze safeguards are unchanged. Rerun the notebook to verify the actual integration.

### D33 — System freeze
- **Date:** 2026-10-19
- **Choice:** Freeze source/configuration SHA256 `62ba5e641bbdaf1a518bb18f6d2e80310ce44b303cce002a49718790be4b3109` after real dev execution, retrieval checks and fast pytest success.
- **Impact:** Held-out seeds may now be generated and run without tuning. Git freeze tag must be created separately if metadata is read-only.

### D34 — Development revision for complete and coherent stage hand-offs
- **Date:** 2026-10-19
- **Authorization:** Owner said "go" after the diagnosed repair plan. Implement and evaluate the repaired system on development seed 42, with no Git commits and no Colab work.
- **Preservation:** Before source/test changes, verified the D33 source hash and saved outputs/frozen_d33_snapshot.zip with 108 source, test, documentation, notebook and result files plus a SHA256 manifest. Original result files and executed notebook remain in place; revised outputs use outputs/revision_v2.
- **Design:** Add a separate stage-coverage validator so approved grounding tests remain unchanged. Require every cluster to receive a finding, every eligible finding a mapping and incident, and every incident a plan. Require one source cluster per finding; perform correlation only at the incident stage, preserving standalone attacks. Detect different external actors and disconnected time windows. Missing coverage triggers the existing bounded retry; exhausted retries remain explicitly incomplete, never fabricated.
- **Correlation policy:** The current synthetic-log scope provides no campaign evidence joining distinct external actors, so keep such actors separate. Configure the maximum gap between incident activity intervals in CONFIG.correlation.max_gap_min (60); use transitive adjacent intervals rather than limiting total chain duration. This is a conservative scoped policy, not a claim that real multi-actor campaigns cannot exist.
- **Artifact protection:** Reject development writes into an output directory carrying a different source freeze. New local development notebook and results use revision_v2; D33 source/tests/results are preserved in the snapshot, and original results stay in place.
- **Evaluation:** Evaluator, accepted techniques, targets, synthetic data and original approved tests remain unchanged. Previously exposed seeds are not used to tune or claim fresh generalization. No new freeze or held-out run is planned for this revision.
- **Regression workflow:** Added tests first. Initial invocation exposed a missing placeholder API (12 AttributeError failures); supplied the placeholder before running behavior assertions.

### D35 — Preserve observed successful sessions in retrieval and valid records in salvage
- **Date:** 2026-10-19
- **Evidence:** The first revised live run split successful authentication correctly, but its narrative retrieval was dominated by preceding brute-force context. Candidates omitted the relevant account/session techniques; bounded retry retained an unretrieved ID. The notebook correctly stopped with incomplete coverage. Saved the attempt in outputs/revision_v2/diagnostics/attempt1.zip.
- **Retrieval choice:** Parse only cited auth evidence using the existing parser. For accepted-session evidence without cited failed attempts, search the neutral text "successful authenticated SSH remote session using valid account credentials". Real index probing returned SSH and Valid Accounts. Do not hard-code technique IDs, add labels, expand candidate count or relax R1/R2. Save actual queries and expose each finding's allowed IDs explicitly to the mapper. Do not infer account namespaces absent from logs.
- **Salvage choice:** Validate records individually after a failed batch retry; retain independently valid records and sanitize/mark only invalid ones. Pass inventory through salvage so internal egress is not misclassified as a second external actor. A remaining unresolved stage still marks the run incomplete. Validator-owned status is assigned after checks.
- **Regression evidence:** New cases reproduced the invalid-record downgrade and missing focused-query helper. Focused expanded suite now reports `21 passed in 0.43s`. The revised notebook is rerunning full offline checks and the development live run; original frozen results and evaluator remain unchanged.
- **Verified outcome:** Full offline gate: `82 passed, 1 deselected, 26 warnings in 52.49s`. All 7 revised notebook cells completed. Same-input development recall 1.0, mapping_accuracy 0.9, false_positives 0, a6_stages 5, invalid evidence/nonexistent/unretrieved IDs 0, coverage.complete true and empty final stage validation log. Runtime_s 115.71899999992456 with 3 live calls and 1 response-cache hit; timing is not an uncached speedup claim. The notebook verified 69 original output/notebook files unchanged. No revised held-out run or new freeze.

### D36 — Resume Git checkpoints for completed and future work
- **Date:** 2026-10-19
- **Authorization:** Owner said "ok start git commiting previous an future". This supersedes the no-commit restriction in D29, D30 and D34, and authorizes local commits of the completed Windows setup, notebook execution and development repair, followed by future milestone commits.
- **Checkpoint:** Save the existing completed work together, including source, regression tests, Windows launchers, executed notebooks, measured outputs and the D33 preservation snapshot. Do not reconstruct historical phase commits or mark the revised system frozen. Keep secrets, environments, downloaded models and caches excluded.
- **Workflow:** The owner's newly supplied AGENTS.md governs future work, including test review before implementation; the earlier D14 workflow exception is historical. New evaluation seeds or benchmark changes still require separate approval. Colab remains outside the current focus. This instruction authorizes commits, not a remote push.
- **Verification:** Preservation/source/notebook/API-key checks pass; original approved tests and evaluator remain unchanged. The existing complete notebook test gate is `82 passed, 1 deselected, 26 warnings in 52.49s`; no implementation changed for this checkpoint.

## Entry template

```
### D# — Title
- **Date:**
- **Phase:**
- **Options considered:**
- **Choice:**
- **Why:**
- **Impact / trade-offs:**
- **Supersedes / superseded by:** (if any)
```
