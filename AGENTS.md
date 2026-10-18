# AGENTS.md: How to work on this project

> **Read this file first, every session.** It explains how to work. The `docs/` folder explains what to build.
> Claude Code users: also create `CLAUDE.md` at the repo root containing just the line `@AGENTS.md`, so it is loaded automatically.

---

## 1. Reading order (every session, before doing anything)

1. `AGENTS.md` (this file)
2. `docs/progress.md`: **Current** and **What's next**
3. `docs/problems.md`: the **Open problems** table
4. `docs/goal.md`: always §5 (scenarios) and §7 (rules); the rest when relevant
5. `docs/plan.md`: only the sections for the current phase
6. `docs/decisions.md`: skim the index; read entries relevant to the current phase

**Precedence when documents disagree:**
1. `docs/goal.md` always wins.
2. This file wins over `docs/plan.md` on **code layout and workflow**. That means §3 here replaces the notebook-first layout in plan.md §9. The notebook is assembled at the end (§10).
3. `docs/plan.md` wins on everything else.

If you find a contradiction, **stop and ask**. Don't resolve it yourself.

---

## 2. Hard rules (summary; full text in goal.md §7)

- **Test-first.** Write tests for a component → stop for human review → implement only after approval.
- **Never edit an approved test to make it pass.** If a test is wrong, stop, explain why, and wait. If approved, log it in `decisions.md`.
- **No invented numbers.** Every number in any doc, README or report must be copied from real command or cell output.
- **Tune on seed 42 only.** Never generate, run or look at results for seeds 7 or 2026 before the System freeze is recorded in `decisions.md`.
- **Ground truth never reaches an agent or baseline.** Only `evaluate.py` and tests may read `ground_truth.json`.
- **No scope creep.** Nothing outside goal.md §4–§5. Ideas go in `progress.md` → What's next, marked "idea, not approved".
- **Check library APIs, don't recall them.** Before using CrewAI, the Gemini/Groq clients, FAISS or sentence-transformers, check the installed version (`pip show`, docstrings, official docs). Log version pins in `decisions.md`.
- **Response actions are never executed.** The system only recommends.
- **Secrets:** API keys only from environment variables (`.env` locally, Colab Secrets in Colab). Never print them, log them or commit them.

---

## 3. Repository layout

```
cyber-threat-agents/
├── AGENTS.md                 # this file
├── CLAUDE.md                 # one line: @AGENTS.md
├── README.md                 # written in Phase 7, real numbers only
├── requirements.txt          # exact pins (==), set in Phase 1
├── pyproject.toml            # pytest config + markers
├── .env.example              # GEMINI_API_KEY=, GROQ_API_KEY=  (no values)
├── .gitignore                # .env, __pycache__, .venv, large caches
├── docs/
│   ├── goal.md  plan.md  progress.md  decisions.md  problems.md
├── src/cyberagents/
│   ├── config.py             # the ONE CONFIG dict (plan.md §11); no magic numbers elsewhere
│   ├── attack_kb.py          # download/parse/filter ATT&CK, mitigation map      (Phase 1)
│   ├── rag.py                # embeddings, FAISS index, search + retrieval log   (Phase 1)
│   ├── generator.py          # environment, synthetic logs, ground truth         (Phase 2)
│   ├── parser.py             # parse + normalize to events DataFrame             (Phase 2)
│   ├── prefilter.py          # rules + clustering                                (Phase 3)
│   ├── schemas.py            # Pydantic models                                   (Phase 3)
│   ├── validators.py         # R1–R3 validators                                  (Phase 3)
│   ├── evaluate.py           # matching, metrics, tables (only reader of GT)     (Phase 3)
│   ├── baselines.py          # S0 (Phase 3), S1 (Phase 6)
│   ├── llm.py                # LLM client wrapper, throttling, response cache    (Phase 4)
│   ├── agents.py             # CrewAI agents, tools, tasks, crew                 (Phases 4–5)
│   └── pipeline.py           # run_system(system, seed) → saved JSON             (Phase 5)
├── tests/
│   ├── conftest.py
│   ├── fixtures/             # sample log lines, golden outputs, fake LLM responses
│   ├── test_kb.py            # T-KB
│   ├── test_rag.py           # T-RAG
│   ├── test_data.py          # T-DATA
│   ├── test_parse.py         # T-PARSE
│   ├── test_rules.py         # T-RULES
│   ├── test_schema.py        # T-SCHEMA
│   ├── test_validators.py    # T-VALID
│   ├── test_eval.py          # T-EVAL (golden)
│   ├── test_agents.py        # T-AGENT (contract)
│   └── test_e2e.py           # T-E2E
├── outputs/                  # generated data and run outputs (see §7 for what's committed)
└── notebooks/
    └── Cyber_Threat_MultiAgent.ipynb   # assembled in Phase 7 (§10)
```

Code lives in `src/` and tests in `tests/`. **Don't develop inside the notebook.** Agents edit `.ipynb` JSON badly; plain `.py` files diff cleanly and run under pytest.

---

## 4. Session workflow

**One phase per session** (Phase 3 may take two). Each phase has two stops:

### Step A: Tests (then STOP)
1. Write the tests for the phase's test groups (plan.md §8.4), plus fixtures.
2. Create minimal stubs (functions that raise `NotImplementedError`) so tests import.
3. Run the tests; they should **fail for the right reason** (not-implemented, not import or syntax errors).
4. **Stop and report:** list every test with a one-line description of what it proves, and point out any test you think is weak. Wait for approval.

### Step B: Implementation (after approval)
1. Implement until the phase's tests pass. Don't touch approved tests.
2. Run the **full** fast suite (§5), not just this phase's tests, to catch regressions.
3. Check every exit check for the phase (plan.md §10).
4. Update docs (§8), commit (§7).
5. **Stop and report** using the format in §9.

Also stop and ask (don't push on) when:
- an exit check fails and the fix would change goal.md, the benchmark or an approved test;
- a library API differs from plan.md in a way that changes the design;
- you'd need to add anything out of scope;
- you've tried the same fix twice and it still fails (log it in problems.md first).

---

## 5. Testing rules

- **Framework:** pytest. Markers are defined in `pyproject.toml`:
  - `live`: calls a real LLM API (needs a key, costs quota)
  - `slow`: builds embeddings/index or other work taking more than about 30 s
- **Default run:** `pytest -m "not live"`. This must stay green at all times after Phase 1.
- **Live tests** (`pytest -m live`) run only in T-AGENT and T-E2E, on seed 42, through the response cache.
- **No real LLM calls in any other test.** Use fake responses from `tests/fixtures/` (fast, free, repeatable).
- Tests check **contracts and behaviour**, never exact LLM wording.
- Golden tests (T-EVAL): the expected scores for the "bad" output are worked out by hand and written into the test **before** `evaluate.py` exists.
- Fixed seeds everywhere; a test that passes "sometimes" is a failing test (log it in problems.md).

---

## 6. LLM usage rules

- All LLM calls go through `llm.py`: one place for the model name (from CONFIG), temperature 0, throttling and a **disk cache** keyed by a hash of (model, prompt, inputs).
- Re-running the same input must hit the cache, not the API.
- On rate-limit errors: back off and retry a small, fixed number of times; then fail clearly and log it in problems.md. Don't silently switch providers mid-run. Switching to Groq is a decision (decisions.md).
- Record the number of LLM calls and tokens (if reported) per run, for the metrics.

---

## 7. Git rules

- `git init` in the setup session. Commit at least after each test group goes green and at each phase end.
- Commit messages: `phase<N>: <what>` (e.g., `phase3: T-VALID green, validators implemented`).
- **Tags:**
  - `phase<N>-done` at each phase end
  - `benchmark-v1` at the Benchmark freeze (end of Phase 3)
  - `system-freeze` at the System freeze (end of Phase 5)
- After `benchmark-v1`, `git diff benchmark-v1 -- tests/ src/cyberagents/evaluate.py` must be empty unless a decisions.md entry explains the change (benchmark v2).
- **Committed:** code, tests, fixtures, docs, `requirements.txt`, results CSVs and charts, the final run JSONs.
- **Not committed:** `.env`, caches, the raw ATT&CK download, the FAISS index (rebuilt from code), virtualenvs.

---

## 8. Documentation rules (when to update what)

| File | Update when |
|------|-------------|
| `docs/problems.md` | **Immediately** when anything goes wrong: error, failing test, wrong assumption, dead end. Include the exact error text. |
| `docs/decisions.md` | **Immediately** when making any choice: version pins, model name, thresholds, prompt changes, test fixes, freezes, provider switch. |
| `docs/progress.md` | **End of every session.** Add a session entry, rewrite **Current** and **What's next**, update the phase tracker and numbers board. |
| `docs/goal.md` | Only with explicit human approval, via its Change Log. |
| `docs/plan.md` | Only to fix errors, with a decisions.md entry. |

A session is not finished until progress.md is updated and committed.

---

## 9. End-of-session report format

```
## Session report: Phase N, Step A/B
- Done: (bullets)
- Tests: (command run + pass/fail counts, copied from output)
- Exit checks: (each one ✅/❌)
- Numbers: (copied from output, or n/a)
- Decisions logged: D#…
- Problems logged: P#… (open/fixed)
- Commit/tag: (hash, tag)
- Needs your input: (questions, or "nothing")
- Next session: (what it will do)
```

---

## 10. Notebook (Phase 7 only)

`notebooks/Cyber_Threat_MultiAgent.ipynb` follows the section order in plan.md §9, but each section **imports** from `src/cyberagents/` instead of containing the code:

1. In Colab: clone the repo from GitHub, `pip install -r requirements.txt`, read keys from Colab Secrets into environment variables.
2. Run the pipeline with saved outputs where they exist (cached), with a flag to run live.
3. Run `pytest -m "not live"` from a cell and show it green.
4. Show results tables and charts, the error analysis and the rendered A6 incident report.
5. Key code (agents, validators, prompts) is shown with `inspect.getsource` or short excerpts, so examiners can read it in the notebook.

Before submitting, confirm: fresh Colab runtime → Run All works.

---

## 11. Human checklist before Phase 1 (not for the agent)

- [ ] Instructor confirmed synthetic logs are acceptable
- [ ] Gemini API key created; Groq key as backup
- [ ] Checked which models the free tier currently allows, and their rate limits
- [ ] Colab's Python version noted (match it locally)
- [ ] Empty GitHub repo created
- [ ] `AGENTS.md` at the repo root, five docs in `docs/`

---

## 12. Prompt templates

**Setup session (run once, first):** see the starting prompt the project owner gave the agent; it creates the skeleton and logs D12–D13.

**Phase N, Step A (tests):**
> Read AGENTS.md, then docs/progress.md and the open items in docs/problems.md, then the plan.md sections for Phase N. We are doing Phase N, Step A. Write the tests and fixtures for its test groups, plus stubs so they import. Run them, then stop and give me the test list with what each one proves. Don't implement anything yet.

**Phase N, Step B (implement):**
> Tests approved [with these changes: …]. Implement Phase N until all its tests pass, without editing the approved tests. Run the full fast suite, check every exit check, update the docs, commit, and stop with the session report.

**Resume after a break or new chat:**
> Read AGENTS.md, docs/progress.md and docs/problems.md. Tell me in five lines where we are and what's next, then wait.

**Something broke:**
> Log this in docs/problems.md first, then investigate: [paste error]. Propose a fix and explain the cause before changing anything that touches tests, goal.md or the benchmark.
