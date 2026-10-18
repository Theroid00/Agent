# PROBLEMS — Multi-Agent Cyber-Threat Detection and Response System

> Every problem we hit: bugs, errors, failed tests, API changes, rate limits, wrong assumptions, dead ends.
> **Log it when it happens, even if it's fixed in five minutes.** Copy the exact error message.
> Read the **Open** table at the start of every session.

---

## Open problems

| # | Date | Phase | Title | Severity | Status |
|---|------|-------|-------|----------|--------|
| P15 | 2026-10-19 | Live evaluation | Original D33 detection recall misses target | 🟠 Major | Original preserved; V2 development repair succeeds |
| P8 | 2026-10-18 | Integration | CrewAI credential directory restriction on original Mac | 🟡 Minor | Historical; Windows framework/live runs pass |
| P9 | 2026-10-18 | Live validation | Fresh-Colab execution unverified | 🔴 Blocker | Windows live execution complete; Colab pending |
| P2 | 2026-10-18 | Setup | Documentation conflicts and missing specifications | 🟠 Major | Open |

Severity: 🔴 Blocker · 🟠 Major (wrong results) · 🟡 Minor (workaround exists)

## Closed problems

| # | Date opened | Date closed | Title | Fix summary |
|---|-------------|-------------|-------|-------------|
| P18 | 2026-10-19 | 2026-10-19 | Direct Python used the Windows legacy text encoding | UTF-8 invocation passes the freeze gate and records D38 before held-out generation |
| P3 | 2026-10-18 | 2026-10-19 | Original Git metadata restriction | Windows checkout permits explicitly authorized Git writes; owner resumes commits in D36 |
| P17 | 2026-10-19 | 2026-10-19 | Successful-login retrieval and batch salvage | Evidence-focused query and per-record validation; revised live run completes with recall 1.0 |
| P16 | 2026-10-19 | 2026-10-19 | Missing stage-coverage checks | New regression suite and complete hand-off validation; full suite 82 passed |
| P14 | 2026-10-19 | 2026-10-19 | Synchronous CrewAI inside Jupyter event loop | Notebook invokes pipeline through asyncio.to_thread; real Gemini findings saved |
| P13 | 2026-10-19 | 2026-10-19 | Windows generated CSV doubled newlines | Preserve CSV writer line endings; unchanged parser tests report 3 passed |
| P12 | 2026-10-19 | 2026-10-19 | Windows notebook MemoryError during duplicate execution | Single kernel and native thread limits; actual retrieval passed 6/6 |
| P1 | 2026-10-18 | 2026-10-18 | Root AGENTS.md missing | Copied supplied instructions unchanged to the expected root path; retained original |
| P10 | 2026-10-18 | 2026-10-18 | Artifact QA and local invocation | Local caches, chart layout correction and documented src path |
| P4 | 2026-10-18 | 2026-10-18 | Package networking and native runtime | Verified official wheel downloads; isolate embedding subprocess (D21) |
| P5 | 2026-10-18 | 2026-10-18 | Retrieval below fixed threshold | Documented fallbacks and query normalization; actual final check passes (D22–D26) |
| P6 | 2026-10-18 | 2026-10-18 | Success hidden by first-ten sample | Range sample retains terminal success (D19) |
| P7 | 2026-10-18 | 2026-10-18 | Full-volume candidate budget exceeded | Normal-background model setting and regression test (D19) |

---

## Watch list (known risks from plan.md §12; log here if any actually happens)

- Free-tier rate limit or daily quota hit
- CrewAI API different from what we expected
- LLM output fails the Pydantic schema
- Retrieval misses the correct ATT&CK technique
- A6 chain not correlated into one incident
- A technique ID in goal.md §5 wrong for the pinned ATT&CK version
- Colab runtime disconnect / lost outputs

---

## Entries (newest first)

### P18 — Direct Python invocation needs UTF-8 mode on Windows
- **Date:** 2026-10-19
- **Symptom:** Development runs and the full freeze suite passed (`82 passed, 1 deselected, 26 warnings in 52.30s`), then reading the Unicode decision log failed before recording the freeze: `UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 11483: character maps to <undefined>`.
- **Cause:** Setting PYTHONUTF8 inside an already-started interpreter does not change its default text encoding. The Windows launchers set it before startup; the direct maintenance invocation omitted that step.
- **Fix:** Invoke the existing orchestration with `python -X utf8`. Reuse saved development outputs and rerun the freeze gate. No production source, approved test, evaluator or model change is needed; neither fresh dataset exists.
- **Status:** Resolved. UTF-8 retry passed `82 passed, 1 deselected, 26 warnings in 55.63s` and recorded System freeze D38. Neither fresh dataset existed at the freeze; original preservation checks pass.

### P17 — Development repair exposes an unretrieved successful-login mapping
- **Resolution:** All 7 revised notebook code cells completed after D35. Coverage is complete, the final stage validation log is empty, detection recall is 1.0 and mapping accuracy is 0.9. No grounding rule or evaluator was weakened. The original incomplete attempt is retained for inspection.
- **Date:** 2026-10-19
- **Symptom:** Revised notebook correctly stopped with coverage.complete=false. After its bounded mapping retry, the unresolved error was `F-c004-success: T1078.001 unknown or not retrieved for this finding`; real run reported 3 LLM calls and runtime_s 109.56200000003446. No improved metric is claimed from this incomplete attempt.
- **Action:** Inspect actual development candidates and refine per-finding closed-set guidance without weakening R1/R2. Also test that one invalid mapping does not downgrade otherwise valid mappings during salvage.
- **Status:** Investigating development-only; original D33 results unchanged.
- **Repair under validation:** D35 focuses accepted-session retrieval on cited parsed evidence, supplies per-finding allowed IDs and saves query provenance. It also preserves independently valid records during salvage and passes the inventory into coherence checks. The focused expanded suite reports `21 passed in 0.43s`; full notebook retry is running. The unsuccessful attempt is preserved in diagnostics/attempt1.zip.

### P16 — Revision coverage regression checks
- **Resolution:** Revised full suite reports `82 passed, 1 deselected, 26 warnings in 52.49s`; all 7 development notebook code cells completed. Approved tests and evaluator remain unchanged.
- **Date:** 2026-10-19
- **Symptom:** New tests initially reported `12 failed in 0.09s` with `AttributeError: module cyberagents.validators has no attribute validate_stage_coverage` because the test-first API placeholder was missing.
- **Action:** Add the placeholder, establish behavior failures, then implement stage-coverage contracts and test real retry hand-offs. D34 records the authorized revision; original approved tests/evaluator remain unchanged.
- **Status:** In progress.
- **Regression evidence:** With the placeholder present, `10 failed, 2 passed in 0.07s` established the missing behavior. After implementation, the targeted agent/validator/pipeline run reported `31 passed, 1 deselected, 26 warnings in 3.84s`; the expanded coverage suite, including multi-attack retries and freeze protection, reported `18 passed in 0.45s`. Full offline and real development evaluation are running in the revised notebook.

### P15 — Real development S3 run misses detection target
- **Development diagnosis (2026-10-19):** Read-only trace of seed 42 confirms four validated malicious findings with valid mappings are omitted from every final incident: f002 (brute force), f008 (password spraying), f010 (SQL injection), f012 (path traversal). f003 combines c003 and c009 from distinct source IPs; it cites 10 evidence lines from c003 and 0 from c009. The existing finding, mapping and incident validators each accept an empty output list. These are completeness/coherence gaps, not failed API execution. No source, approved test, evaluator or frozen result was modified during this diagnosis.
- **Date:** 2026-10-19
- **Evidence:** metrics_S3_seed42.json reports detected_scenarios [A6], detection_recall 0.16666666666666666, incident_precision 1.0, false_positives 0, mapping_accuracy 0.8, a6_stages 5 and a6_correlated true. Nonexistent/unretrieved IDs and invalid evidence references are 0. Misses A1–A5 are recorded as analyst dismissal/correlation.
- **Impact:** Successful execution and grounding do not establish that the detection targets were met. Preserve these measured misses in results/error analysis.
- **Action:** D33 has frozen the source/configuration; continue held-out evaluation without tuning or changing tests. The owner requested setup and notebook execution, not a new benchmark revision.
- **Status:** Full notebook completed. All S3 runs have detection_recall 0.16666666666666666. Mapping accuracy is 0.8 on development, 0.75 on seed 7 and 0.8 on seed 2026. Comparison/error analysis and the real A6 report are saved; targets remain missed and no post-freeze tuning was performed.

### P14 — Live notebook cell calls synchronous CrewAI inside Jupyter's event loop
- **Date:** 2026-10-19
- **Symptom:** After the full offline suite passed, code cell 9 failed with `RuntimeError: Agent execution was invoked synchronously from within a running event loop. Use agent.kickoff_async() / crew.kickoff_async() (or await agent.aexecute_task(...)) when calling from async code.` The ordinary-terminal framework contract test had passed.
- **Action:** Keep the existing synchronous pipeline/CLI and run it from notebook cells using await asyncio.to_thread, so CrewAI executes outside Jupyter's event loop. Apply to development and held-out S3 invocation; compile notebook cells with top-level-await support.
- **Status:** Fixed: all 14 notebook code cells completed, including real Gemini execution, System freeze and held-out evaluation.

### P13 — Generated-line parser contract fails on Windows
- **Date:** 2026-10-19
- **Symptom:** Notebook offline suite reported `1 failed, 60 passed, 1 deselected, 26 warnings in 58.70s`. Existing test_generated_lines_all_parse_without_touching_ground_truth expected equal parsed-event/physical-line counts but got `assert 5972 == 11829`.
- **Cause/fix:** csv.writer emits CRLF in StringIO, then Windows text output translates LF again. Preserve the buffer's line endings with Path.write_text(..., newline=''). No approved test or scenario was changed; D31 records the implementation fix.
- **Status:** Focused unchanged parser suite passed: `3 passed in 0.51s`. Full notebook suite and live cells are being retried.

### P12 — Windows notebook reloads ATT&CK and raises MemoryError
- **Date:** 2026-10-19
- **Symptom:** Local notebook completed its setup and knowledge-base cells, then cell 3 failed with `MemoryError` at `raw = path.read_bytes()` in attack_kb.py, called by check_retrieval → prepare_rag → build_kb. No live API request had been made. Partial outputs are saved in Cyber_Threat_MultiAgent.executed.ipynb.
- **Evidence:** Raw file size is 49253343 bytes. Windows reported FreePhysicalMemory 7888484 KiB and FreeVirtualMemory 4741920 KiB after the failure. An existing Jupyter server for this checkout had a busy kernel and embedding worker; the headless attempt duplicated that workload.
- **Action:** Observed the existing session until its server/workers stopped without producing an index. Retry with one kernel and OMP/OpenBLAS/MKL/NumExpr threads set to one before native imports; propagate those limits to launchers/notebook setup. No benchmark, threshold or approved test is changed.
- **Status:** Fixed for the Windows retry: retrieval completed and passed 6/6. The retry's notebook parent used 158871552 private bytes and embedding worker 914169856 private bytes in the inspected process output, below the earlier overlapping processes' memory use. Remaining notebook cells are still running.

### P11 — Windows checkout networking, Git ownership and Store Python
- **Date:** 2026-10-19
- **Symptoms:** Sandboxed clone failed with `Failed to connect to github.com port 443`. After the authorized external clone, sandboxed Git reported `fatal: detected dubious ownership in repository at 'D:/agent'`. The Windows Store interpreter could not start through the sandbox (`Unable to create process using` its WindowsApps path); its virtual environment likewise reported `No Python at` the WindowsApps alias.
- **Action:** Retry network and interpreter operations through explicit tool escalation. Scope Git's ownership exception to each read-only command with `git -c safe.directory=D:/agent`; do not alter global trust settings. Create and install into the project's .venv using the installed user interpreter.
- **Status:** Setup completed using explicit escalation where required: dependencies installed, pip check passed, local notebook kernel registered and CLI startup passed. Sandbox-specific restrictions remain understood; no global Git trust change was made.

### P10 — Artifact QA warnings and local import invocation
- **Date:** 2026-10-18
- **Symptom:** Chart generation emitted `Fontconfig error: No writable cache directories`; files were produced successfully. Visual inspection found a clipped hallucination-chart title. An ad-hoc inspection command without the documented source path returned `ModuleNotFoundError: No module named 'cyberagents'`.
- **Fix:** Set XDG_CACHE_HOME/MPLCONFIGDIR to the local cache for final chart rendering, shorten the title and show the rates on a nonnegative axis. Invoke local modules with the README's PYTHONPATH setup (pytest already configures it).
- **Status:** Fixed; charts visually checked after regeneration.


### P9 — Live and Colab validation unavailable
- **Date:** 2026-10-18
- **Symptom:** No GEMINI_API_KEY/GROQ_API_KEY was configured during the build. The live smoke test skips explicitly. No authenticated fresh Colab runtime was available.
- **Impact:** No real S1/S3 detection numbers, A6 model report, System freeze, held-out results or fresh-Colab Run All are claimed. The executable implementation and notebook are delivered; these exit checks remain pending.
- **Next:** Set a key privately in .env or Colab Secrets, run the dev systems, then freeze only after checks pass. Never paste a secret into chat.
- **Status:** Deferred by explicit owner choice: continue with offline results only. These exit checks remain incomplete.

### P8 — CrewAI import writes outside the managed workspace
- **Date:** 2026-10-18
- **Symptom:** Installed CrewAI imports attempted storage creation outside the workspace:
  ```text
  PermissionError: [Errno 1] Operation not permitted: '/Users/theroid0/Library/Application Support/Security-agent'
  PermissionError: [Errno 1] Operation not permitted: '/Users/theroid0/Library/Application Support/crewai'
  ```
- **Cause:** CREWAI_STORAGE_DIR relocates project storage, but the installed crewai-core TokenManager independently creates its per-user credentials directory during import, even with tracing disabled.
- **Action:** Configure project storage under .cache. Do not patch installed authentication code or bypass the filesystem policy. The actual Agent/Task/Crew test explicitly skips this specific permission error; four-stage contract tests use injected stage responses and pass. Google GenAI and Groq imports succeeded.
- **Next:** Run the framework contract test in an ordinary user terminal or Colab. A skip is not framework verification.
- **Status:** Open.

### P7 — Full-volume candidate budget exceeded
- **Date:** 2026-10-18
- **Symptom:** Initial seed-42 output contained 100 rule clusters, above plan's less-than-40 budget. Initial measured S0 false positives: 91. Initial artifacts are retained under outputs/diagnostics/.
- **Cause/fix:** Synthetic normal failures were too frequent; D19 records the pre-freeze background-model change. Default source counts, injected cases and rule thresholds stay fixed. A full-volume regression test now checks the budget.
- **Status:** Fixed; final measurements are separately regenerated. No held-out seed was used.

### P6 — Terminal login missing from displayed sample
- **Date:** 2026-10-18
- **Symptom:** The new endpoint-sampling test failed because accepted-login evidence followed more than ten failures and was omitted from the displayed sample.
- **Fix:** Sample evenly across the time range and preserve endpoints (D19), with a regression assertion for the accepted event.
- **Status:** Fixed.

### P5 — Fixed retrieval queries initially missed their IDs
- **Date:** 2026-10-18
- **Symptom:** Actual top-five checks passed 3/6 for initial MiniLM, 4/6 after cleaning, 3/6 for BGE descriptions, 4/6 with modern detection text, and 4/6 with equal reciprocal-rank fusion. The CLI reported `Retrieval threshold missed; record a decision before changing the embedding design`.
- **Fix:** D22–D26 record each fallback, modern STIX schema extraction and explicit generic query normalization. Final measured check: 6/6. Original queries, accepted IDs and target remained unchanged. Prior reports remain in outputs/diagnostics/.
- **Status:** Fixed for the fixed development check; broader retrieval quality is unmeasured.

### P4 — Package networking and native embedding runtime failure
- **Date:** 2026-10-18
- **Symptom:** The bulk dependency install failed with `failed to lookup address information: nodename nor servname provided, or not known` for `https://pypi.org/simple/crewai/`.
- **Workaround:** Downloaded public official wheels with curl, verified registry SHA256 hashes, and installed the needed offline-test/embedding packages locally. The pinned model files were downloaded separately. Large ATT&CK/Torch transfers timed out and completed after range-resume; partial files were not treated as valid.
- **Native failure:** The first real retrieval command loaded model weights and exited with code 139 before writing retrieval results. Its final warning included `resource_tracker: There appear to be 1 leaked semaphore objects to clean up at shutdown`.
- **Fix/status:** Fixed. D21 isolates embedding from FAISS and sets one CPU thread. The combined runtime had also emitted `OMP: Error #15: Initializing libomp.dylib, but found libomp.dylib already initialized.` Actual final retrieval succeeds. Dependency metadata closure reports no missing/incompatible active requirements after the Kubernetes pin in D27.

### P3 — Managed permissions prevent Git initialization and commits
- **Date:** 2026-10-18
- **Phase / notebook section:** Setup
- **Severity:** 🔴 Blocker
- **Symptom:** `git init` exited with this exact error:
  ```text
  /Users/theroid0/PycharmProjects/Security-agent/.git: Operation not permitted
  ```
  Dependent staging and commit commands were mistakenly attempted after initialization failed and returned:
  ```text
  fatal: not a git repository (or any of the parent directories): .git
  ```
  The staged-diff command consequently returned this error and no repository diff:
  ```text
  error: unknown option `cached'
  ```
- **How found:** Attempting the explicitly requested first setup commit.
- **Continuation retry (2026-10-18):** `git init` still failed. Exact output:
  ```text
  error: could not lock config file /Users/theroid0/PycharmProjects/Security-agent/.git/config: Operation not permitted
  error: could not lock config file /Users/theroid0/PycharmProjects/Security-agent/.git/config: Operation not permitted
  error: could not lock config file /Users/theroid0/PycharmProjects/Security-agent/.git/config: Operation not permitted
  fatal: could not set 'core.repositoryformatversion' to '0'
  ```
  No dependent staging or commit commands were attempted after this retry failed.
  Read-only status confirmed Git metadata now exists and printed `## No commits yet on main`. `git log -2 --format='%h %s'` returned `fatal: your current branch 'main' does not have any commits yet`.
- **Root cause:** Managed workspace permissions grant read access only to `.git`; sandbox approval is unavailable.
- **Latest check:** An external initial commit now exists: `a132914 Initial`; it was not created or amended by the agent. Normal staging still failed:
  ```text
  fatal: Unable to create '/Users/theroid0/PycharmProjects/Security-agent/.git/index.lock': Operation not permitted
  ```
- **Fix/status:** Resolved for the current Windows checkout. On 2026-10-19 the owner authorized previous and future commits (D36); explicitly approved Git staging succeeds in D:\agent and staged whitespace checks pass. The original Mac restriction remains historical. The local checkpoint records the completed work; no remote push or new freeze tag is intended.
- **Prevention:** Stop dependent Git commands when initialization fails; use a workspace with writable Git metadata to complete the two commits.
- **Time lost:** Not measured.

### P2 — Documentation conflicts and missing specifications
- **Date:** 2026-10-18
- **Phase / notebook section:** Setup; review before Phase 1
- **Severity:** 🟠 Major
- **Symptom:** The supplied documents disagree or omit required details:
  - Plan §10 requires held-out seed generation in Phase 2 and checks on all seeds in Phase 3; AGENTS §2 and D9 prohibit those runs before System freeze.
  - Plan §10 schedules schemas/validators in Phase 4 and evaluation in Phase 6; AGENTS §3, progress and D8 place the harness in Phase 3 before agents.
  - Plan §10 uses seven days; D11 specifies eight.
  - Phase 1 requires a successful LLM call; AGENTS §5 restricts live tests to T-AGENT and T-E2E.
  - AGENTS §4 references nonexistent plan §8.4.
  - The pending test-runner choice lists plain asserts versus ipytest despite the pytest requirement.
  - Plan §6 places prompts in the notebook, while AGENTS requires module development and notebook assembly in Phase 7.
  - Plan §10 permits reducing to two seeds; goal §§3, 6 and 10 require three.
  - Goal R1–R4 describe validation of all outputs; plan §1 retains invalid raw S1 outputs. S1 has no retrieval set for the unretrieved-ID metric in plan §8.2.
  - Plan §7 omits the required unvalidated status field; §8.1 omits matching ties and empty evidence; §7.1 does not explicitly require a mitigation's technique to belong to the incident.
  - AGENTS §7 requires an empty diff for all tests after benchmark-v1, although later phases add tests; the intended exception process is unclear.
  - Plan §14 uses D1–D6 for different choices from the same IDs in decisions.md.
  - Progress requires notebook-cell evidence for numbers; AGENTS also permits command output.
  - Human prerequisites in AGENTS §11 are unchecked: instructor acceptance, keys, current free-tier availability, Colab Python version and GitHub setup.
- **How found:** Full setup review in the requested document order.
- **Root cause:** Multiple planning documents have not been reconciled.
- **Fix:** None; listed for human clarification as requested. D12/D13 record only the explicitly authorized layout and git rules.
- **Status:** Partly addressed by the owner workflow override (D14) and explicit implementation/evaluation decisions (D18). The broad goal/raw-S1 wording and external human prerequisites remain open; no goal text was silently changed.
- **Prevention:** Review before starting Phase 1; do not silently change goal.md, plan.md or approved tests.
- **Time lost:** Not measured.

### P1 — Root AGENTS.md missing
- **Date:** 2026-10-18
- **Phase / notebook section:** Setup
- **Severity:** 🟡 Minor
- **Symptom:** `cat: AGENTS.md: No such file or directory`
- **How found:** First requested document read.
- **Root cause:** Supplied instructions were located at `docs/AGENTS (1).md`.
- **Fix:** Copied the supplied file unchanged to root `AGENTS.md`; retained the original.
- **Status:** Fixed
- **Prevention:** Keep root AGENTS.md available for subsequent sessions and the CLAUDE.md reference.
- **Time lost:** Not measured.

---

## Entry template

```
### P# — Short title
- **Date:**
- **Phase / notebook section:**
- **Severity:** 🔴 / 🟠 / 🟡
- **Symptom:** (exact error message or wrong output, copied)
- **How found:** (which test or cell)
- **Root cause:**
- **Fix:** (what changed; link decision D# if it changed the design)
- **Status:** Open / Fixed / Workaround / Won't fix
- **Prevention:** (new test added? rule changed?)
- **Time lost:**
```
