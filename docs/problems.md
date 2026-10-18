# PROBLEMS — Multi-Agent Cyber-Threat Detection and Response System

> Every problem we hit: bugs, errors, failed tests, API changes, rate limits, wrong assumptions, dead ends.
> **Log it when it happens, even if it's fixed in five minutes.** Copy the exact error message.
> Read the **Open** table at the start of every session.

---

## Open problems

| # | Date | Phase | Title | Severity | Status |
|---|------|-------|-------|----------|--------|
| P3 | 2026-10-18 | Setup | Managed permissions prevent Git initialization and commits | 🔴 Blocker | Open |
| P2 | 2026-10-18 | Setup | Documentation conflicts and missing specifications | 🟠 Major | Open |

Severity: 🔴 Blocker · 🟠 Major (wrong results) · 🟡 Minor (workaround exists)

## Closed problems

| # | Date opened | Date closed | Title | Fix summary |
|---|-------------|-------------|-------|-------------|
| P1 | 2026-10-18 | 2026-10-18 | Root AGENTS.md missing | Copied supplied instructions unchanged to the expected root path; retained original |

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
- **Fix:** None in this session. Setup files and documentation updates are present, but neither requested commit exists.
- **Status:** Open; Git initialization and both commits blocked.
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
- **Status:** Open; does not prevent setup, but Phase 1 needs clarification of applicable conflicts and prerequisites.
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
