# PLAN — Multi-Agent Cyber-Threat Detection and Response System (CrewAI + RAG)

> **HOW we build what `goal.md` defines.** Read `goal.md` first; it overrides this file.
> Work phase by phase (§10). Don't start a phase until the previous phase's **exit checks** pass.
> Any deviation → add an entry to the Decision Log (§14).

**Current delivery (D37–D41):** The frozen V2 evaluation ran on Windows CPU, using development seed 42 and fresh held-out 812399/876694. All runs and the Windows notebook/report completed; mapping accuracy 0.7 on 876694 misses the unchanged per-seed target. Results and tags are published. See progress.md and outputs/evaluation_v2/report.md for current status. Historical Colab planning remains a full-submission requirement; fresh-Colab execution is unverified and outside current focus. Future implementation follows the restored AGENTS.md review workflow (D36).

---

## 0. Guiding design principles

1. **Deterministic where possible, LLM where it adds judgement.** Parsing, rule matching, ID validation, mitigation lookup and evaluation are plain Python. LLMs only do what rules can't: dismissing benign look-alikes, choosing the right technique, correlating across sources, writing the response.
2. **Closed-set choices.** The Threat Intel agent picks technique IDs from retrieved candidates instead of generating them from memory.
3. **Validate, don't trust.** Every agent output passes a code validator before it moves on (goal.md R1–R3, R8).
4. **Save everything.** Each stage writes JSON to `outputs/`, so evaluation never re-calls the LLM and a Colab disconnect costs nothing.

---

## 1. Architecture

```
                ┌──────────────────────────┐
 seed ─────────▶│ Synthetic Log Generator  │──▶ auth.log, access.log, firewall.csv
                │ (+ ground truth labels)  │──▶ ground_truth.json  (EVAL ONLY, never to agents)
                └────────────┬─────────────┘
                             ▼
                ┌──────────────────────────┐
                │ Parser & Normalizer      │──▶ events DataFrame (one row per line, event_id)
                └────────────┬─────────────┘
                             ▼
                ┌──────────────────────────┐
                │ Deterministic Pre-filter │──▶ candidate clusters (high recall, low precision)
                └────────────┬─────────────┘
                             ▼
   asset_inventory.json ─────┤
                             ▼
 ┌────────────────────── CrewAI (sequential) ───────────────────────┐
 │ 1. Log Analyst      → Findings (malicious / suspicious / benign) │
 │        │  [validator: evidence IDs ⊆ cluster IDs]                │
 │ 2. Threat Intel     → technique mapping  ◀── RAG (FAISS over     │
 │        │  [validator: ID exists + was retrieved]   ATT&CK)       │
 │ 3. Risk Assessor    → Incidents (correlation, severity, chain)   │
 │        │  [validator: findings exist, IDs valid]                 │
 │ 4. Response Planner → Response plans  ◀── mitigation lookup      │
 │           [validator: M#### exists & mitigates that technique]   │
 └──────────────────────────────┬───────────────────────────────────┘
                                ▼
                outputs/S3_seed{N}.json ──▶ Evaluation vs ground truth ──▶ tables, charts
```

**Systems compared** (all receive the same clusters + asset inventory):
- **S0: Rules-only.** Every cluster becomes an incident; no dismissal, no correlation, no technique mapping.
- **S1: Single LLM prompt, no RAG.** One call; outputs the same final schema. Validators run **only to measure** hallucinations, not to fix them.
- **S3: Full system.** 4 agents + RAG + validators.
- *(Optional S2: 4 agents without RAG; ablation, only if time allows.)*

---

## 2. Tech stack

Pin exact versions at the start of Phase 1 by running `pip show` and recording them in the Config cell and the Decision Log. **Don't trust version numbers or API signatures from memory**, including this document's.

| Component | Choice | Notes |
|-----------|--------|-------|
| Runtime | Windows CPU verified; Google Colab CPU planned | Local outputs persist on disk; fresh-Colab execution is unverified |
| Agents | CrewAI | Sequential process; `output_pydantic` on tasks; custom tools |
| LLM | Gemini (free tier) primary, Groq fallback | Model name lives in `CONFIG`; check currently available free models on build day. Temperature 0. |
| API keys | Environment variables; ignored .env locally, Colab Secrets in Colab | Never hard-coded or printed |
| Embeddings | `BAAI/bge-small-en-v1.5` (CPU), pinned revision in CONFIG | Planned fallback adopted after measured MiniLM misses (D23) |
| Vector store | FAISS (`faiss-cpu`) | Cosine similarity via normalized vectors + inner product |
| Keyword search | `rank_bm25` plus dense retrieval | Hybrid fallback adopted after measured dense misses (D25/D26) |
| Schemas | Pydantic v2 | |
| Data | pandas, numpy, `re` | |
| Charts | matplotlib | |
| ATT&CK data | `mitre/cti` GitHub repo → `enterprise-attack/enterprise-attack.json` (STIX 2) | Pin a specific release/commit; record ATT&CK version in Config |

---

## 3. Data design

### 3.1 Simulated environment (fixed across seeds) → `asset_inventory.json`

| Item | Value |
|------|-------|
| Internal network | `10.0.0.0/24` |
| SSH server | `ssh-srv` — `10.0.0.10` |
| Web server | `web-srv` — `10.0.0.20` (port 443/80) |
| Monitoring host | `mon-01` — `10.0.0.5` (role: service health checks) |
| Backup server | `backup.corp-example.net` — use an address from `192.0.2.0/24` (role: nightly backup target) |
| Admin user | `sysadmin` (expected sudo, working hours 09:00–19:00 IST) |
| Normal users | ~15 names, e.g., `asharma`, `rkumar`, `deploy`, `pmehta`, … |
| Attacker IPs | Drawn from RFC 5737 documentation ranges `203.0.113.0/24` and `198.51.100.0/24` |

Documentation IP ranges mean no real IPs appear anywhere. The inventory is given to agents; it contains roles, not labels.

### 3.2 Log formats (each line gets a stable ID: `auth:000123`, `web:004512`, `fw:010233`)

**auth.log** (syslog / sshd / sudo):
```
Oct 17 02:14:07 ssh-srv sshd[4123]: Failed password for root from 203.0.113.45 port 51522 ssh2
Oct 17 02:14:09 ssh-srv sshd[4124]: Failed password for invalid user admin from 203.0.113.45 port 51530 ssh2
Oct 17 02:19:44 ssh-srv sshd[4188]: Accepted password for deploy from 203.0.113.45 port 51790 ssh2
Oct 17 02:21:03 ssh-srv sudo:   deploy : TTY=pts/0 ; PWD=/home/deploy ; USER=root ; COMMAND=/bin/bash
```

**access.log** (Apache combined):
```
198.51.100.23 - - [17/Oct/2026:11:02:15 +0530] "GET /products?id=1%27%20OR%20%271%27%3D%271 HTTP/1.1" 200 512 "-" "sqlmap/1.7"
10.0.0.42 - - [17/Oct/2026:11:05:40 +0530] "GET /search?q=O%27Brien HTTP/1.1" 200 2048 "-" "Mozilla/5.0 ..."
```

**firewall.csv:**
```
ts,src_ip,src_port,dst_ip,dst_port,proto,action,bytes_out,bytes_in
2026-10-17T02:05:11+05:30,203.0.113.45,40112,10.0.0.10,22,tcp,ALLOW,60,0
```

### 3.3 Generator behaviour
- 24-hour window (IST timestamps, normalized to UTC at parse time).
- Benign background: ~3,000 auth, ~8,000 web, ~10,000 firewall lines with realistic daily rhythm (busier 09:00–19:00).
- Inject A1–A6 and B1–B5 (goal.md §5) at seed-dependent times and IPs; A6 stages in correct order within ~2 hours, same attacker IP for stages 1–3, the compromised user for stage 4, and `ssh-srv` → external IP for stage 5.
- Seeds: **42, 7, 2026**.
- Outputs: `outputs/seed{N}/auth.log`, `access.log`, `firewall.csv`, `ground_truth.json`.

### 3.4 Ground truth (`ground_truth.json`, EVAL ONLY)
```json
{
  "seed": 42,
  "scenarios": [
    {"scenario_id": "A1", "type": "attack", "accepted_techniques": ["T1110.001","T1110"],
     "line_ids": ["auth:000881", "..."], "stages": null},
    {"scenario_id": "A6", "type": "attack",
     "stages": [{"stage": 1, "accepted_techniques": ["T1046","T1595.001"], "line_ids": ["fw:..."]}, "..."]},
    {"scenario_id": "B3", "type": "benign", "line_ids": ["web:..."]}
  ]
}
```

### 3.5 Normalized event schema (pandas)
`event_id, source, ts_utc, host, src_ip, src_port, dst_ip, dst_port, user, event_type, outcome, http_method, path, status, bytes_out, user_agent, raw`

`event_type` values include: `ssh_failed`, `ssh_invalid_user`, `ssh_accepted`, `sudo`, `http_request`, `conn`.

---

## 4. Deterministic pre-filter (high recall on purpose)

Thresholds live in `CONFIG`. **The rules are deliberately loose so B1–B5 also produce clusters.** Dismissing them is the agents' job and the core of the evaluation.

| Rule | Logic | Expected to catch |
|------|-------|-------------------|
| R-AUTH-FAIL | ≥ 3 failed logins from the same `src_ip` within 10 min | A1, A6-s2, **B1** |
| R-SPRAY | ≥ 5 distinct usernames from the same `src_ip` within 30 min | A2 |
| R-SUCCESS-AFTER-FAIL | Accepted login from an IP with failures in the prior 60 min | A6-s3, **B1** |
| R-SCAN | ≥ 15 distinct `dst_port` from the same `src_ip` within 5 min | A3, A6-s1, **B4** |
| R-WEB-PATTERN | Regex for SQLi tokens (`'`, `%27`, `UNION`, `OR 1=1`, `--`) and traversal (`../`, `%2e%2e`, `/etc/passwd`) | A4, A5, **B3** |
| R-SUDO-ROOT | `sudo` with `USER=root` and a shell command (`/bin/bash`, `/bin/sh`, `su`) | A6-s4, **B2** |
| R-EGRESS | `bytes_out` ≥ 100 MB to an external IP within 1 hour | A6-s5, **B5** |

**Cluster object** (stored in Python; a trimmed version goes to the LLM):
```
cluster_id, rule_ids[], src_ip, users[], hosts[], t_start, t_end,
line_count, all_line_ids[]  (kept in Python for validation/eval),
sample_lines[]  (≤ 10 raw lines + IDs, sent to agent)
```
Clusters are grouped by `src_ip` (or `user` for sudo, `host` for egress) and time window, and merged if overlapping.

---

## 5. RAG design

### 5.1 Knowledge base build
1. Download the pinned `enterprise-attack.json`.
2. Keep `attack-pattern` objects where `revoked != true` and `x_mitre_deprecated != true`.
3. Extract: ATT&CK ID (from `external_references` where `source_name == "mitre-attack"`), name, tactics (`kill_chain_phases`), platforms, description, and detection text if present in this version (field names vary between ATT&CK versions; check the pinned file).
4. Build `techniques` dict `{id → record}` and `mitigations` map from `relationship` objects of type `mitigates` (`course-of-action` → `attack-pattern`), giving `{technique_id → [M####, name]}`.
5. Save `outputs/attack_kb.json` + record ATT&CK version and technique count.

### 5.2 Index
- One document per technique: `"{ID} {name}. Tactics: … Platforms: … {description (first ~1,200 chars)}"`.
- Embed with MiniLM, L2-normalize, FAISS `IndexFlatIP`. Save index + ID order.

### 5.3 Retrieval tests (Phase 1 exit check; need ≥ 5 of 6 passing, top-5)
| Query | Must contain in top-5 |
|-------|----------------------|
| many failed SSH password attempts from one IP | T1110 or T1110.001 |
| one IP trying many different usernames | T1110 or T1110.003 |
| connection attempts to many ports on a host | T1046 or T1595.001 |
| SQL injection payload in web request | T1190 |
| sudo to root shell after login | T1548.003 or T1548 |
| large outbound data transfer to external server | T1048 or T1041 |

If < 5 pass → try (a) a cleaner document text, (b) the bge-small model, (c) hybrid BM25 + dense. Log the choice in §14.

### 5.4 Tools exposed to agents
- `search_attack(query: str, k: int = 5)` → list of `{id, name, tactics, snippet}`. **Wrapped so every returned ID is recorded in a per-finding `retrieval_log`.**
- `get_technique(id: str)` → full record (only for IDs already in `retrieval_log`).
- `get_mitigations(technique_id: str)` → ATT&CK mitigations from the relationship map (deterministic).

### 5.5 Pre-retrieval (closed-set)
Before the Threat Intel task, Python builds a query from each finding's summary + indicators and retrieves the **top-8 candidates**, inserted into the task context. Allowed IDs for that finding = pre-retrieved candidates ∪ IDs returned by the agent's own `search_attack` calls.

---

## 6. Agents & tasks (CrewAI, sequential)

All agents: temperature 0, `allow_delegation=False`, concise backstories, `output_pydantic` set on each task.

| # | Agent | Input | Tools | Output |
|---|-------|-------|-------|--------|
| 1 | **Log Analyst**: "SOC Tier-1 analyst" | Trimmed clusters + asset inventory | none | `FindingList` |
| 2 | **Threat Intel Analyst**: "ATT&CK mapping specialist" | Non-benign findings + top-8 candidates each | `search_attack`, `get_technique` | `MappedFindingList` |
| 3 | **Risk Assessor**: "Incident correlation lead" | Mapped findings + inventory | none | `IncidentList` |
| 4 | **Response Planner**: "Incident responder" | Incidents | `get_mitigations` | `ResponsePlanList` |

**Key instructions per agent (summary; full prompts live in the notebook):**
- **Log Analyst:** judge each cluster as `malicious | suspicious | benign`, using the asset inventory (known monitoring host, backup server, admin working hours). Cite only line IDs shown in the cluster. Explain benign dismissals.
- **Threat Intel:** choose 1–3 techniques per finding **only from candidates or your own search results**. Give a justification tied to evidence. Mark the primary technique.
- **Risk Assessor:** link findings that share IP, user, or host within a plausible time order into one incident. Order stages chronologically as a kill chain. Assign severity (`low/medium/high/critical`) and confidence (0–1) with rationale.
- **Response Planner:** immediate containment actions (with target IP/user/host), ATT&CK mitigations **from the tool only**, investigation steps, and prevention. Commands are shown as examples; never executed.

### 6.1 Batching (free-tier friendly)
Each task processes **all** items in one call (not one call per cluster). Expected ≈ 4 task calls + a few tool calls per seed. Use CrewAI's request throttling (e.g., `max_rpm`, if present in the pinned version) or manual sleeps.

---

## 7. Schemas (Pydantic, summary)

```python
class Finding:        finding_id, cluster_ids[], verdict: Literal["malicious","suspicious","benign"],
                      summary, evidence_line_ids[] (≤10), src_ips[], users[], hosts[], reasoning
class TechniqueChoice: technique_id, name, tactic, is_primary: bool, justification
class MappedFinding:  finding_id, techniques: list[TechniqueChoice] (1–3), mapping_confidence: float
class KillChainStep:  order, ts_utc, finding_id, technique_id, description
class Incident:       incident_id, finding_ids[], title, severity, confidence: float,
                      attacker_ips[], affected_assets[], kill_chain: list[KillChainStep], rationale
class Action:         action, target, priority: Literal["P1","P2","P3"], example_command: str | None
class MitigationRef:  mitigation_id, name, for_technique_id
class ResponsePlan:   incident_id, executive_summary, immediate_actions: list[Action],
                      mitigations: list[MitigationRef], investigation_steps[], prevention[]
```
Each has a `…List` wrapper for batched output.

### 7.1 Validators (run after each task; goal.md R1–R3, R8)
| Validator | Checks |
|-----------|--------|
| `validate_findings` | Every `evidence_line_id` ∈ `all_line_ids` of its `cluster_ids`; cluster IDs exist |
| `validate_mappings` | Technique ID exists, not revoked/deprecated; ∈ allowed set for that finding; exactly one primary |
| `validate_incidents` | Finding IDs exist; kill-chain technique IDs ∈ that finding's validated mapping |
| `validate_plans` | Incident IDs exist; each `M####` exists and is linked to `for_technique_id` in the relationship map |

On failure: re-run that task once with the validator errors appended. If still failing: strip invalid items, set `status="unvalidated"`, log to `outputs/validation_log.json`.

---

## 8. Evaluation

### 8.1 Matching outputs to ground truth
- **Incident ↔ scenario:** an incident matches the scenario that owns the most of its evidence line IDs (via its findings). A scenario is **detected** if at least one non-benign incident matches it.
- **False positive:** an incident whose evidence lines are mostly from B1–B5 or unlabeled background.
- **Mapping correct:** for each detected scenario (each stage for A6), the primary technique on the matching kill-chain step ∈ accepted set.
- **Chain correlated:** one incident's evidence spans ≥ 4 of A6's 5 stages.

### 8.2 Metrics (per system × seed)
1. Scenario detection recall (A1–A6)
2. Incident precision
3. False-positive count (B1–B5)
4. Mapping accuracy (primary technique)
5. A6 chain correlated (Y/N, stages covered)
6. **Hallucinated technique IDs**: % of IDs not in ATT&CK or not retrieved (S1 measured raw; S3 pre- and post-validation)
7. Invalid evidence references (%)
8. Runtime, number of LLM calls, tokens if the API reports them

### 8.3 Outputs
- `results_by_seed.csv`, `results_summary.csv` (mean ± std over 3 seeds)
- Charts: grouped bar chart for recall / FP / mapping accuracy per system; hallucination-rate bar chart
- Error analysis table: every miss and FP → cause (pre-filter, analyst verdict, retrieval miss, mapping choice, correlation)

---

## 9. Notebook layout

| § | Section | Type |
|---|---------|------|
| 0 | Title, problem, architecture diagram, how to run | Markdown |
| 1 | Setup: installs, version pins, secrets, `CONFIG`, seeds | Code |
| 2 | ATT&CK knowledge base: download, parse, filter, mitigation map | Code |
| 3 | RAG index + retrieval tests | Code |
| 4 | Environment + synthetic log generator + ground truth | Code |
| 5 | Parsing & normalization | Code |
| 6 | Deterministic pre-filter → clusters | Code |
| 7 | Schemas & validators | Code |
| 8 | Tools, agents, tasks, crew | Code |
| 9 | Run S3 on one seed + pretty-printed walkthrough | Code |
| 10 | Baselines S0, S1 | Code |
| 11 | Run all systems × 3 seeds (skip if output file exists) | Code |
| 12 | Evaluation: tables + charts | Code |
| 13 | Error analysis | Code + Markdown |
| 14 | Demo: rendered A6 incident report | Code (Markdown render) |
| 15 | Conclusions, limitations, future work | Markdown |

`CONFIG` holds all thresholds, model names, k values, seeds and paths. No magic numbers elsewhere.

---

## 10. Timeline & phases (~7 days)

### Phase 1 — Setup + ATT&CK RAG (Day 1)
- Colab setup, installs, record exact versions, secrets, `CONFIG`.
- Build ATT&CK KB (§5.1), mitigation map, FAISS index (§5.2).
- **Verify every technique ID in goal.md §5** exists in the pinned data with the expected name.
- **Exit checks:** technique count printed; goal.md §5 IDs all verified (or Change Log updated); ≥ 5 of 6 retrieval tests pass; one test LLM call succeeds.

### Phase 2 — Log generator + parser (Day 2)
- Environment + inventory (§3.1), generator (§3.3), ground truth (§3.4), parser (§3.5).
- **Exit checks:** 3 seeds generated; every A/B scenario present in ground truth with line IDs; 100% of lines parse; spot-check 5 lines per source by eye.

### Phase 3 — Pre-filter + S0 baseline (Day 3)
- Rules (§4), clustering, S0 output in final schema.
- **Exit checks:** every A1–A6 stage and every B1–B5 case lands in at least one cluster on all seeds (pre-filter recall = 100%); cluster count reasonable (< ~40 per seed); S0 output saved.

### Phase 4 — Agents 1–2 + validators (Day 4)
- Schemas (§7), validators (§7.1), Log Analyst, Threat Intel with logged tools, pre-retrieval.
- **Exit checks:** on seed 42, outputs parse into Pydantic; validators run; retry path tested once by forcing an invalid ID.

### Phase 5 — Agents 3–4 + full crew (Day 5)
- Risk Assessor, Response Planner, `get_mitigations`, full sequential crew, saving outputs.
- **Exit checks:** S3 full run on seed 42 under 15 min; A6 visible as one incident (or failure noted for error analysis); response plans contain only valid M#### IDs.

### Phase 6 — Evaluation (Day 6)
- S1 baseline, run S0/S1/S3 × 3 seeds, evaluation harness (§8), charts, error analysis.
- **Exit checks:** results CSVs + charts generated from saved files; every miss/FP has a cause.

### Phase 7 — Polish + submission (Day 7)
- Markdown narrative, demo report, limitations, README with actual numbers.
- **Exit checks:** fresh runtime → Run All succeeds (with cached outputs allowed for LLM steps; also verify a full live run once); goal.md §10 checklist complete.

**If behind schedule, cut in this order:** optional S2 ablation → charts beyond the two required → reduce to 2 seeds (log in §14) → shorten benign background volume.

---

## 11. CONFIG (authoritative runtime settings)

The one CONFIG dictionary lives in src/cyberagents/config.py. Model names, exact embedding/ATT&CK revisions, thresholds, correlation policy and seed metadata are recorded there and covered by the source/configuration freeze. Inspect the actual settings instead of maintaining a second copy here:

```python
import json
from cyberagents.config import CONFIG
print(json.dumps(CONFIG, indent=2))
```

The active V2 comparison uses CONFIG['evaluation_seeds']: development 42, held-out 812399/876694. Legacy held-out IDs remain recognized only for compatibility with original runs and approved tests; do not add them to the V2 comparison. Both fresh seeds are now exposed. The default output path retains original D33 files; the current notebook passes outputs/evaluation_v2 explicitly and reuses matching saved runs. Any future tuning requires a separate approved development/freeze/unseen-data cycle; never alter the current frozen source or force held-out reruns.

---

## 12. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Free-tier rate limits / daily quota | Batched tasks, throttling, bounded retries and cached outputs; provider changes require an explicit documented decision |
| CrewAI API differs from expectations | Read installed version's docs on Day 1; keep CrewAI-specific code in one section |
| LLM output fails schema | `output_pydantic` + one retry with error text; mark `unvalidated` |
| Retrieval misses correct technique | Pre-retrieval tests (§5.3); bge-small / hybrid BM25 fallback; agent can search further |
| A6 not correlated | Provide shared indicators clearly in findings; ask for explicit linking; report honestly if still missed |
| Synthetic data too easy | Tricky benign cases B1–B5 + varied attacker IPs/times per seed; state as limitation |
| Colab disconnects | Write to Drive-mounted `outputs/`; idempotent cells |
| Scope creep | goal.md §4 out-of-scope list; Decision Log required for any change |

---

## 13. Optional stretch (ONLY after goal.md Definition of Done)

1. S2 ablation (agents without RAG) to isolate RAG's effect.
2. Simple Gradio demo: upload logs → incident reports.
3. Qualitative run on a small public SSH honeypot log sample (clearly labelled as unevaluated).

---

## 14. Decision Log

| # | Date | Decision | Reason |
|---|------|----------|--------|
| D1 | 2026-10-18 | Synthetic logs instead of public datasets | Exact ground truth, controllable tricky benign cases, no licensing issues |
| D2 | 2026-10-18 | Deterministic pre-filter before LLM | Logs too large for LLM context; free-tier limits; makes recall measurable |
| D3 | 2026-10-18 | Closed-set technique selection (pre-retrieved candidates + logged tool calls) | Prevents technique IDs from model memory |
| D4 | 2026-10-18 | Response = recommendations only | Safety; out of scope to act on systems |
| D5 | 2026-10-18 | Gemini free tier primary, Groq fallback | ₹0 budget, no GPU needed |
| D6 | 2026-10-18 | Documentation IP ranges (RFC 5737) for all external IPs | No real IPs in data |
| D14 | 2026-10-18 | Human replaces AGENTS workflow with goal/plan/decisions; tests still precede implementation | Explicit instruction during full-build session |
| D15 | 2026-10-18 | Develop offline components while external exit checks remain explicitly pending; held-out runs wait for freeze | Missing API keys, package network and Git permissions; no invented verification |
| D16 | 2026-10-18 | Pin MITRE CTI commit and SHA256 in configuration | Reproducible knowledge-base source; see decisions.md |
| D17 | 2026-10-18 | Pin direct dependencies, compatible Pydantic and Gemini 3.5 Flash-Lite | Current official registry/provider evidence; account verification pending |
| D18 | 2026-10-18 | Isolated sequential CrewAI tasks with validation; S1 hallucinations mean nonexistent IDs | Enforce stage hand-offs and make no-RAG measurement meaningful |
| D19 | 2026-10-18 | Range sampling and configured normal-background failure probability | Dev tests exposed hidden success evidence and excessive full-volume clusters |
| D20 | 2026-10-18 | Assemble self-contained module-importing notebook | Fresh Colab startup without an unspecified GitHub URL |
| D21 | 2026-10-18 | Isolate CPU embedding in a worker process | Actual duplicate-OpenMP failure with the installed native wheels |
| D22 | 2026-10-18 | Clean retrieval documents and invalidate stale index formats | Real MiniLM check passed only 3 of 6 fixed queries |
| D23 | 2026-10-18 | Use pinned BGE-small with the documented query instruction | Cleaned MiniLM passed only 4 of 6 fixed queries |
| D24 | 2026-10-18 | Extract detection text through modern STIX strategies/analytics | The pinned release no longer places it in the legacy technique field |
| D25 | 2026-10-18 | Add the planned BM25+dense rank fusion | BGE with detection text still passed only 4 of 6 fixed queries |
| D26 | 2026-10-18 | Normalize broad port-scanning/exfiltration vocabulary before hybrid retrieval | Public retrieval checks remained below target; no ID lookup rules or changed acceptance sets |
| D27 | 2026-10-18 | Pin Kubernetes 36.0.2 for CrewAI/Pydantic compatibility; local CrewAI storage, explicit import permission skip | Installed metadata exposed incompatible latest transitive dependency; external validation remains pending |
| D34 | 2026-10-19 | Repair stage completeness in a development revision; one cluster per finding, incident-level correlation with actor/time guards | Live D33 output silently omitted mapped attacks; preserve original results, retry missing inputs, and evaluate seed 42 separately |
| D35 | 2026-10-19 | Use cited successful-auth evidence for its retrieval query; salvage valid records independently | Narrative context obscured the observed login, and a batch error downgraded valid mappings; preserve candidate limits and grounding rules |
| D37 | 2026-10-19 | Owner approves V2 evaluation on development 42 and fresh held-out 812399, 876694; freeze before generation | Original held-out outcomes are already exposed; preserve V1, use the same evaluator/targets and do not tune after exposure |
| D38 | 2026-10-19 | Freeze V2 source/configuration after cached current development execution and existing full gates | Complete coverage, measured development output, calibrated retrieval and unchanged offline tests pass before either fresh dataset exists |
| D39 | 2026-10-19 | Report all fresh outcomes without tuning, including mapping 0.7 on one seed | A passing held-out mean does not satisfy every seed; preserve semantic errors and distinguish evidence-stage coverage from correct technique mapping |
| D41 | 2026-10-19 | Synchronize verified Windows runtime/retrieval status and replace stale CONFIG example with the authoritative source | Current docs must match the completed frozen evaluation; preserve historical decisions and unchanged goals/benchmark |
