# GOAL — Multi-Agent Cyber-Threat Detection and Response System (CrewAI + RAG)

> **This file is the single source of truth for WHAT we are building.**
> `plan.md` describes HOW. If `plan.md`, the notebook, or any AI assistant's suggestion disagrees with this file, **this file wins**.
> This file changes only through the Change Log at the bottom, with a reason.

---

## 1. One-line goal

Build a Google Colab notebook in which **four CrewAI agents** read synthetic server logs, **detect injected attacks**, **map each attack to a real MITRE ATT&CK technique using RAG**, **link related events into incidents** (including a multi-stage attack chain), and **produce a response playbook**. Every claim about how well it works must come from **measured results against known ground truth**.

---

## 2. Problem statement

Security teams receive thousands of log lines a day. Simple threshold rules flag too much (false positives) and give no context: they don't say *what kind* of attack it is, *how* separate alerts relate, or *what to do*. LLMs can add that reasoning, but they hallucinate technique IDs and evidence.

This project shows that a **multi-agent pipeline, grounded in the ATT&CK knowledge base and checked by code-level validators**, can:
1. dismiss benign look-alikes that rules alone flag,
2. map real attacks to the correct ATT&CK techniques,
3. correlate separate alerts into one attack chain, and
4. recommend concrete responses,

with **zero unverifiable technique IDs or evidence references in its final output**.

---

## 3. Objectives

| ID | Objective |
|----|-----------|
| O1 | Generate realistic synthetic logs (SSH auth, web access, firewall) with **6 injected attack scenarios** and **5 tricky benign cases**, with exact ground-truth labels. |
| O2 | Build a RAG knowledge base over the official **MITRE ATT&CK Enterprise** dataset (pinned version). |
| O3 | Implement **4 CrewAI agents**: Log Analyst → Threat Intel (RAG) → Risk Assessor (correlation) → Response Planner. |
| O4 | Enforce grounding with **code validators**: technique IDs must exist in ATT&CK and must have been retrieved; evidence line IDs must exist in the logs. |
| O5 | Evaluate the full system against **2 baselines** (rules-only; single LLM prompt without RAG) on **3 random seeds**. |
| O6 | Deliver a clean, top-to-bottom runnable notebook with results tables, error analysis and a demo incident report. |

---

## 4. Scope

### In scope
- Three log sources: `auth.log` (sshd/sudo, syslog format), web `access.log` (Apache combined format), firewall/connection log (CSV).
- One simulated environment: one SSH server, one web server, internal hosts, a fixed user list, a known backup server, and a known monitoring host.
- Offline batch analysis of a 24-hour log window per seed.
- A deterministic pre-filter (rules) that produces candidate clusters for the agents.
- RAG over ATT&CK techniques, plus a deterministic lookup of ATT&CK mitigations.
- Structured (Pydantic) outputs, validators, evaluation, baselines, error analysis.

### Out of scope (do NOT build these)
- Real-time or streaming detection, live packet capture, connecting to real servers.
- **Executing** any response action. The system only *recommends* actions.
- Training or fine-tuning any ML model.
- Windows, cloud, or Active Directory logs; malware or binary analysis.
- A web UI. (Optional stretch only after Definition of Done; see `plan.md` §13.)
- Any attack scenario not listed in §5.

---

## 5. Fixed scenario catalog

> Phase 1 of `plan.md` **must verify** every technique ID below against the pinned ATT&CK JSON (exists, not revoked, not deprecated, name matches). If one is wrong, fix it here via the Change Log; never in code silently.

### 5.1 Attack scenarios (must be detected)

| ID | Scenario | Log source(s) | Observable pattern | Accepted ATT&CK IDs (primary first) |
|----|----------|---------------|--------------------|--------------------------------------|
| A1 | SSH brute force | auth | Many failed passwords from one external IP against one account in a short window | **T1110.001**, T1110 |
| A2 | Password spraying | auth | One external IP, many different usernames, 1–2 attempts each | **T1110.003**, T1110 |
| A3 | Port scan | firewall | One external IP touching many distinct destination ports in minutes | **T1046**, T1595.001 |
| A4 | SQL injection | web | SQLi payloads in query strings (`' OR '1'='1`, `UNION SELECT`, etc.), scanner user agent | **T1190** |
| A5 | Path traversal | web | `../` sequences, `/etc/passwd` in URLs | **T1190**, T1083 |
| A6 | Multi-stage chain | all three | Port scan → SSH brute force → **successful login** (same IP) → `sudo` to root shell → large outbound transfer to an external IP | Stages: **T1046** → **T1110.001** → **T1078** (also T1021.004) → **T1548.003** → **T1048** (also T1041). **Must be reported as ONE incident.** |

### 5.2 Tricky benign cases (must NOT become incidents)

These are designed to trip the rules-only baseline. The pre-filter **must let them through** so the agents are actually tested on them.

| ID | Benign case | Why it looks suspicious |
|----|-------------|-------------------------|
| B1 | Employee mistypes password 3 times from an internal IP, then logs in | Failed logins followed by success |
| B2 | Admin runs `sudo` to root during working hours from a known internal IP | Privilege escalation pattern |
| B3 | Legitimate web searches containing apostrophes (e.g., `O'Brien`) | Matches SQLi quote patterns |
| B4 | Known internal monitoring host checks ~20 service ports every 5 minutes | Looks like a port scan |
| B5 | Nightly large transfer to the known backup server | Looks like data exfiltration |

The agents are given an **asset inventory** (known hosts, roles, users, backup and monitoring servers). This is legitimate operational context, not ground truth.

---

## 6. Success criteria (targets, measured on 3 seeds)

| Metric | Target |
|--------|--------|
| Scenario detection recall (A1–A6) | ≥ 5 of 6 per seed |
| False-positive incidents from B1–B5 | ≤ 1 per seed |
| ATT&CK mapping accuracy (primary technique in accepted set, per detected scenario/stage) | ≥ 80% |
| A6 reported as a single incident covering ≥ 4 of 5 stages | ≥ 2 of 3 seeds |
| Invalid / unretrieved technique IDs in **final** output | **0** (enforced by validator) |
| Evidence line IDs in final output that don't exist in that finding's cluster | **0** (enforced by validator) |
| Full system beats rules-only baseline on false positives, and beats no-RAG baseline on mapping accuracy + hallucinated IDs | Yes |
| End-to-end runtime per seed on free Colab + free LLM tier | ≤ 15 min |

**These are targets, not claims.** The report states the actual numbers, including any targets that were missed, with an explanation in the error analysis.

---

## 7. Non-negotiable rules

### 7.1 For the system (enforced in code, not just in prompts)
- **R1** — Every ATT&CK technique ID (T####/T####.###) and mitigation ID (M####) in any output must exist in the pinned ATT&CK dataset and be neither revoked nor deprecated.
- **R2** — Every technique ID chosen for a finding must come from the retrieval results for that finding (pre-retrieved candidates or a logged RAG tool call). IDs from model memory are rejected.
- **R3** — Every evidence line ID cited in a finding must exist and belong to the clusters that finding came from.
- **R4** — All agent outputs are Pydantic-validated structured objects. Free text is allowed only in designated text fields.
- **R5** — The Response agent recommends; nothing in the notebook executes a response action.
- **R6** — Ground-truth labels are never visible to any agent or baseline. They are used only in the evaluation section.
- **R7** — Reproducibility: temperature 0, fixed seeds (42, 7, 2026), pinned library and ATT&CK versions, all outputs saved to disk.
- **R8** — On validation failure: retry once with the validator's error message; if still invalid, strip the invalid item, mark the finding `unvalidated`, and log it. Never silently "fix" an ID.

### 7.2 For whoever builds it (me, teammates, or any AI assistant)
- Do not add features, scenarios, agents or data sources not in this file.
- Never write a number in the report or README that was not printed by a notebook cell in the final run.
- Do not rely on memory for library APIs (CrewAI, Gemini/Groq, FAISS). Check the installed version's docs. If an API differs, change the code, not the goal.
- Do not claim the system works on real-world logs; it is evaluated on synthetic data only. State this as a limitation.
- When behind schedule, cut from the optional list in `plan.md` first, then simplify within scope. Never expand scope to compensate.
- Every deviation from `plan.md` gets an entry in the plan's Decision Log.

---

## 8. Deliverables

1. `Cyber_Threat_MultiAgent.ipynb`: runs top to bottom on a fresh Colab runtime with only API keys added to Colab Secrets.
2. `outputs/` folder: generated logs, ground truth, ATT&CK index metadata, per-run JSON outputs, results tables (CSV), charts (PNG).
3. In-notebook report sections: architecture diagram, results table (3 systems × 3 seeds), error analysis, limitations.
4. One rendered sample incident report (the A6 chain) as a demo.
5. `README.md` (written at the end): how to run, what it does, the actual results.

---

## 9. Constraints

- **Cost:** ₹0. Free Colab (CPU only) and free-tier LLM API (Gemini primary, Groq fallback).
- **Time:** ~7 working days (see `plan.md` §10).
- **Compute:** No GPU. Embeddings run on CPU (small sentence-transformers model).
- **API limits:** The design must stay within free-tier rate limits (batching, caching outputs to disk, `max_rpm` throttling).

---

## 10. Definition of Done

- [ ] All Phase exit checks in `plan.md` §10 pass.
- [ ] Notebook runs end-to-end on a fresh runtime without manual edits.
- [ ] Results table for S0, S1, S3 across 3 seeds is generated from saved outputs.
- [ ] Validator logs show 0 invalid IDs and 0 invalid evidence refs in S3 final outputs.
- [ ] Error analysis explains every missed scenario and every false positive.
- [ ] Demo incident report for A6 is rendered.
- [ ] README written with actual numbers only.

---

## 11. Glossary

- **MITRE ATT&CK**: public knowledge base of adversary tactics and techniques; each technique has an ID like T1110 (sub-technique T1110.001).
- **Tactic**: the attacker's goal at a stage (e.g., Credential Access). **Technique**: how they achieve it.
- **Mitigation (M####)**: ATT&CK's recommended defensive measure, linked to techniques.
- **Cluster**: group of suspicious log lines produced by the deterministic pre-filter.
- **Finding**: Log Analyst's judgement on one or more clusters.
- **Incident**: one or more related findings judged to be a single attack (may be a multi-stage chain).
- **RAG**: Retrieval-Augmented Generation; the agent reasons over text retrieved from the ATT&CK index.
- **Hallucinated ID**: a technique/mitigation ID that doesn't exist in ATT&CK or wasn't retrieved for that finding.

---

## 12. Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-10-18 | Initial version | — |
