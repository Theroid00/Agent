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

---

## Pending decisions (to make on build day; Phase 1)

- [ ] Exact CrewAI version (check installed version's docs)
- [ ] Exact LLM model name for the free tier (check what's currently available)
- [ ] ATT&CK release/commit to pin
- [ ] Test runner: plain `assert` runner vs `ipytest`
- [ ] Confirm embedding model (MiniLM) after retrieval tests

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
