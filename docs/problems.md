# PROBLEMS — Multi-Agent Cyber-Threat Detection and Response System

> Every problem we hit: bugs, errors, failed tests, API changes, rate limits, wrong assumptions, dead ends.
> **Log it when it happens, even if it's fixed in five minutes.** Copy the exact error message.
> Read the **Open** table at the start of every session.

---

## Open problems

| # | Date | Phase | Title | Severity | Status |
|---|------|-------|-------|----------|--------|
| P8 | 2026-10-18 | Integration | CrewAI import creates credentials outside managed workspace | 🔴 Blocker | Open |
| P9 | 2026-10-18 | Live validation | API key and fresh-Colab execution unavailable | 🔴 Blocker | Deferred by owner |
| P3 | 2026-10-18 | Setup | Managed permissions prevent Git initialization and commits | 🔴 Blocker | Open |
| P2 | 2026-10-18 | Setup | Documentation conflicts and missing specifications | 🟠 Major | Open |

Severity: 🔴 Blocker · 🟠 Major (wrong results) · 🟡 Minor (workaround exists)

## Closed problems

| # | Date opened | Date closed | Title | Fix summary |
|---|-------------|-------------|-------|-------------|
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
- **Fix/status:** Open. User-controlled permissions must allow .git writes, subject to managed policy; alternatively commit from the ordinary macOS terminal. The agent did not bypass the sandbox and created no commits/tags.
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
