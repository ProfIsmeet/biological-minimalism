# Biological Minimalism

**An evidence-driven methodology for the target-specific marginal value of sensing components in autonomous astronaut health monitoring**

Built for the **77th International Astronautical Congress (IAC 2026)**, Antalya,
Türkiye — IAF/IAA Space Life Sciences Symposium, Interactive Presentation format.

> **This README is a human-readable overview, not the scientific source of
> truth.** It summarizes the project's final (Stage-5) state for a new reader.
> For final scientific claims, architecture state, evidence classifications,
> and release provenance, the canonical Stage-5 artifacts — starting with
> [`docs/BIOLOGICAL_MINIMALISM_FINAL_PROJECT_HANDOFF.md`](docs/BIOLOGICAL_MINIMALISM_FINAL_PROJECT_HANDOFF.md)
> and the `results/final_*.json` manifests and claim ledger — take precedence
> over this document and over any older/intermediate documentation elsewhere
> in the repository. This is normal provenance hygiene for a project that
> ran in staged sprints, not a sign that something is wrong.

## 1. What this is

Long-duration spaceflight requires continuous physiological monitoring, but
every sensor added to a wearable costs mass, power, contact points, and crew
burden. **Biological Minimalism** asks, per candidate sensing modality,
whether it provides *measurable incremental value* — after controlling for
model capacity, temporal correspondence, subject separation, heterogeneity,
and physical burden — and uses that evidence, not intuition, to select a
final wearable architecture. It is **not** a claim that one fixed sensor set
is universally optimal; some modalities were retained, some were excluded,
and some remain unresolved.

The repository also ships a NASA Mission Control–styled dashboard demo. Its
synthetic mode illustrates a *proposed*, motivating four-sensor personalized
**Biological Digital Twin** concept (wireless EEG, PPG, peripheral
temperature, bio-impedance) — this is a UI/demo vision, distinct from (and
not the same sensor set as) the final evaluated architecture below. Its
replay mode plays one real, synchronized PPG-DaLiA subject through the
validated PPG+IMU heart-rate model, with genuine locally-computed SHAP
explainability over the synthetic physiology estimator. See
[Sensor & Data Honesty](#9-sensor--data-honesty-dashboard-demo) for exactly
what is and isn't real in the running demo.

## 2. Final project status

| Item | Status |
|---|---|
| Final architecture | **`CORE_PLUS_CONTEXT`** (see §3) |
| Module topology | `DISTRIBUTED_BODY_MODULE_TOPOLOGY` (wrist, chest, head) |
| Formal Pareto analysis | `COMPLETE` — no unique mathematical winner (see §5) |
| Gate D (engineering burden completeness) | `CONDITIONALLY_READY` (Coordinator-accepted bounded uncertainty) |
| Gate E (EOG / sparse-EEG external validity) | `FREEZE_CONDITIONALLY` ×2, with predefined revision triggers |
| Digital Twin | `ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED` (see §7) |
| GalaxyPPG external replication | `EXTERNAL_REPLICATION_SUPPORTIVE` with participant heterogeneity |
| HMC full-cohort (EOG external validity) | `LOWER_PRIORITY_EXTERNAL_WORK_PENDING` |
| ds003838 full-cohort (sparse EEG) | `LOWER_PRIORITY_EXTERNAL_WORK_PENDING` |
| Release | `stage5-v1.0.0-release-candidate`, independent final audit `CONDITIONAL_PASS` |

This table intentionally does **not** say `NOT_READY` for architecture or
Pareto — that was the honest state at an earlier (pre-Stage-4) point in the
project and is preserved in historical artifacts, but it is no longer the
current state. See §13 for why older files with different statuses still
exist in this repository.

## 3. Final wearable architecture

**`CORE_PLUS_CONTEXT`** — selected from the Pareto-relevant candidate set
after jointly weighing scientific evidence, physical burden, implementation
topology, and explicitly bounded uncertainty. It is a Coordinator judgment
call within that set, not a claim of unique optimality (see §5).

| Body region | Module | Sensors |
|---|---|---|
| Wrist | `wrist_module` | PPG + IMU |
| Chest | `chest_module` | ECG |
| Head | `head_module` | Frontal EEG + EOG (EOG shares the EEG module's AFE/reference infrastructure — it is not a separate module) |

Topology: **`DISTRIBUTED_BODY_MODULE_TOPOLOGY`** — three independent
body-worn modules, each with its own local electronics/power/MCU-radio
domain, rather than a shared central hub.

Safe framing (do not strengthen beyond this):

> CORE_PLUS_CONTEXT was selected from the Pareto-relevant architecture set
> after jointly considering scientific evidence, physical burden,
> implementation topology, and explicitly bounded uncertainty.

This is **not**: "the uniquely optimal architecture," "four sensors are
proven sufficient," "universally minimal," or a claim that every excluded
sensor is useless. Excluded/deprioritized modalities (second-site PPG, leg
BioZ, thoracic BioZ/EIS, wrist temperature/light) were excluded for
*this* evaluated architecture on the evidence in §6, not declared useless in
general — see `results/final_wearable_architecture.json#exclusion_rationale`.

Source of record: [`results/final_wearable_architecture.json`](results/final_wearable_architecture.json).

## 4. Strongest evidence

**Wrist PPG+IMU → heart rate.** The historical comparison sometimes cited
for this project (~9.086 → 7.208 bpm, ≈20.6% relative reduction) used a
PPG-only baseline and a PPG+IMU model with substantially different parameter
counts (~8k vs ~29k) — it is **capacity-confounded** and is retained only as
a historical artifact, never as current governing evidence. Under a
**capacity-near-matched** comparison, synchronized IMU still shows a modest
incremental benefit beyond a capacity-matched PPG-only baseline (PPG-DaLiA,
+0.605 bpm, 5/5 seeds), and synchronized IMU also outperforms a
shuffled/control IMU condition. This finding was subsequently supported on
an independent **GalaxyPPG** cohort (corrected 18/24-participant cohort,
+0.834 bpm, 12/18 participants favor the PPG+IMU model) — external support,
though participant-level effects remain heterogeneous (6/18 participants
disfavor it). See `results/final_claim_ledger.json` (`ppg_plus_imu`,
`old_ppg_imu_headline_20_6_23_percent`, `galaxy_replication`) and
`results/final_tables/table_c_external_replication.json`.

**Frontal EEG+EOG → sleep stage.** Same-dataset controlled evidence
(Sleep-EDF) shows aligned EOG improving macro-F1 over EEG-only (+0.028,
4/5 seeds) and over a shuffled-EOG control (+0.032, 4/5 seeds), with
directionally consistent results on a small prospective secondary holdout
(n=8). This is same-dataset controlled support, **not** external
replication — see §7 on EOG and §10 on pending work.

## 5. Pareto rationale (no unique winner)

A formal multi-objective Pareto dominance analysis is **`COMPLETE`**.
Two architecture classes remain **Pareto-relevant** (neither dominates the
other on the evaluated evidence/burden axes): `MINIMAL_CORE` and
`CORE_PLUS_CONTEXT`. "Pareto-relevant" means non-dominated — it does not by
itself pick a winner. The Coordinator then **selected**
`CORE_PLUS_CONTEXT` from within that set, judging that EOG's sleep-staging
evidence justified its low incremental burden (it shares the EEG module's
electronics). This is a documented decision, not a mathematical proof that
`CORE_PLUS_CONTEXT` beats every alternative. Source:
[`results/stage4_formal_pareto_analysis.json`](results/stage4_formal_pareto_analysis.json).

## 6. Negative / mixed findings (preserved, not hidden)

Biological Minimalism deliberately keeps negative and mixed results in the
record rather than reporting only successes:

- **Second-site PPG (PTT).** A second PPG measurement site did not show
  stable aggregate benefit for HR/PTT estimation (worse by +1.462 MAE
  aggregate, n=4 held-out subjects) and the result is fragile to subject
  exclusion — deprioritized, not proof a second site never helps.
- **Leg BioZ (QDE V2).** Aggregate-negative but heterogeneous: 7 of 10
  subjects individually favor the additional-sensor model despite a
  negative aggregate mean. Excluded from the final architecture, not
  labeled useless.
- **Thoracic EIS (LBNP protocol).** Classified `COMPLETE_MIXED` — the sign
  of the effect reverses depending on whether one subject (of 12) is
  included. Excluded from the final architecture; not interpreted as a
  stable or uniform negative.
- **EEG × respiration interaction (sleep staging).** No stable evidence of
  synergy or antagonism (mixed-sign across seeds); not used as a basis for
  a joint EOG-respiration module.

See [`results/final_tables/table_d_negative_mixed_results.json`](results/final_tables/table_d_negative_mixed_results.json).

## 7. Conditional / bounded status of individual components

**EOG.** Included in the final architecture on same-dataset controlled
support (§4). It is **not** externally validated: a bounded, underpowered
n=7 diagnostic on an independent dataset (HMC) exists but does not establish
external replication in either direction. Full HMC external work (151
subjects) remains pending. Architecture inclusion is `FREEZE_CONDITIONALLY`
with an explicit revision trigger (a stable, majority-consistent negative
full-cohort result would reopen the decision).

**Sparse frontal EEG.** The current minimal-channel design point is
retained as the frozen engineering choice, **not** as a population-validated
minimization result. A bounded n=3 diagnostic on an independent dataset
(ds003838) confirms the data pipeline works but is inconclusive by design.
Full-cohort work (~65 subjects) remains pending. Also
`FREEZE_CONDITIONALLY` with an explicit revision trigger.

## 8. Digital Twin boundary

Status: **`ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED`**. The Digital Twin is a
conceptual system-architecture layer (a 153,801-parameter untrained
reference network) — not a trained, personalized, astronaut-calibrated, or
longitudinally validated model, and not a clinical validation of any kind.
See [`results/digital_twin_architecture_footprint.json`](results/digital_twin_architecture_footprint.json).

**Engineering burden.** Gate D is `CONDITIONALLY_READY`: bounded (Tier
0–2, component-datasheet/class-level) estimates exist for power (selected
per-module topology: 9.937 mW battery-side), battery-only mass (8.763 g),
contact/electrode count (9 most likely, range 9–14), and raw data rate
(~19.6 kbps) across the 3 modules (wrist/chest/head). These are engineering
*estimates*, not measured or vendor-sourced figures, and total system mass
beyond battery cells is not yet resolved (`SYSTEM_MASS_NOT_READY`). The
Coordinator accepted this bounded uncertainty as sufficient to close the
architecture decision; it does not mean the burden model is exact or final.
See [`results/final_tables/table_f_engineering_burden.json`](results/final_tables/table_f_engineering_burden.json).

## 9. Sensor & Data Honesty (dashboard demo)

No real sensor hardware is connected. The dashboard's **synthetic mode**
comes from `backend/app/engine/mock_data_engine.py`, a set of smooth
random-walk processes shaped by literature-*inspired* engineering
approximations (`backend/app/engine/physiology.py`) — not fitted or
validated against real subject data. Every number the dashboard displays and
every SHAP explanation it generates in this mode is computed live from that
transparent pipeline; nothing is scripted per scenario.

The dashboard's **dataset replay mode** instead transports previously
recorded PPG-DaLiA channels from one subject/session and feeds synchronized
8-second PPG+IMU windows to the validated heart-rate model described in §4.
This does not validate hardware timing, microgravity behavior, or clinical
accuracy. See [`docs/DATASET_REPLAY.md`](docs/DATASET_REPLAY.md).

## 10. Validation boundaries

- All governing evidence comes from **terrestrial** datasets (healthy or
  patient cohorts, or protocol-analog stressors such as LBNP for
  hypovolemia) — none of it is spaceflight or microgravity data.
- Simulated sensor-fault injection (single held-out subject, 114 conditions)
  characterizes model behavior under signal loss; it is **not** a hardware
  or spaceflight fault-tolerance validation.
- No astronaut physiological validation has been performed.
- Nothing in this repository constitutes clinical certification or flight
  certification.

## 11. Pending science and future work

- **HMC full cohort** (151 subjects; EOG external validity) —
  `LOWER_PRIORITY_EXTERNAL_WORK_PENDING`.
- **ds003838 full cohort** (~65 subjects; sparse-EEG channel-count
  validity) — `LOWER_PRIORITY_EXTERNAL_WORK_PENDING`.
- Vendor-specific BOM part selection, exact electrode montages, and a
  final battery/electronics topology decision (shared-hub vs. per-module)
  remain open engineering refinements within Gate D's accepted bounds.
- Spaceflight/microgravity validation and clinical/flight certification are
  out of scope for this project as it stands.

Neither pending item is required to honestly represent the current accepted
release — they are disclosed, not fabricated as complete.

## 12. Repository structure

```
biological-minimalism/
├── results/        Canonical machine-readable Stage-3/4/5 evidence, claim
│                    ledger, manifests, and tables — the actual source of
│                    truth (see §13).
├── docs/           Project Design Document, methodology notes, and the
│                    final project handoff (see §13). Also contains many
│                    historical/intermediate sprint documents (see §14).
├── paper/          IAC paper contracts (intro/methods/results/discussion/
│                    limitations) and the abstract fact sheet (paper/final/).
├── presentation/   Jury Q&A evidence pack, traced to the claim ledger.
├── ml/             Research-grade training/evaluation scaffolding, model
│                    architectures, and the Stage-5 validators (not used by
│                    the running dashboard demo) — see ml/README.md.
├── backend/        FastAPI + WebSocket dashboard API, mock data engine,
│                    physiology model, PyTorch inference, real SHAP.
├── frontend/       Next.js 15 / React 19 / TypeScript dashboard UI.
├── scripts/        Build scripts that generate the results/ artifacts
│                    (one script per artifact, e.g. build_final_claim_ledger.py).
├── datasets/       Where to obtain the real datasets used for evidence
│                    (PPG-DaLiA, GalaxyPPG, Sleep-EDF, HMC, ds003838, etc.)
│                    — none are bundled here.
├── dashboard/      Short architecture note only; the actual dashboard
│                    application is frontend/ + backend/.
├── docker-compose.yml
└── README.md       You are here.
```

## 13. Canonical sources / reproducibility

Start here for the full picture:

- **[`docs/BIOLOGICAL_MINIMALISM_FINAL_PROJECT_HANDOFF.md`](docs/BIOLOGICAL_MINIMALISM_FINAL_PROJECT_HANDOFF.md)**
  — the best human-readable final-state summary; if it and the JSON
  artifacts below ever disagree, the JSON artifacts win.
- **[`results/final_project_manifest.json`](results/final_project_manifest.json)**
  — the project-level source of truth: architecture, Pareto/Gate D/E state,
  pending science, and the full list of authoritative artifacts.
- **[`results/final_claim_ledger.json`](results/final_claim_ledger.json)**
  — every scientific claim area with its exact safe wording, evidence
  strength, numeric support, and prohibited stronger wording.
- **[`results/final_release_manifest.json`](results/final_release_manifest.json)**
  — the frozen hash registry, test results, and known limitations for this
  release candidate.

Note on scope: this root `README.md` is a human-readable overview and is
**not** itself one of the SHA256-hashed authoritative artifacts listed in
`final_project_manifest.json` / `final_release_manifest.json`. Editing it
does not require (and did not trigger) any change to those frozen manifests.

Reproduction command references, per-experiment reproducibility class, and
the clean-clone verification result are in
[`results/final_reproduction_manifest.json`](results/final_reproduction_manifest.json).
Fast, inexpensive Stage-5 consistency checks:

```bash
cd ml && python -m pytest tests/test_stage5_final_synthesis_consistency.py -v
cd ml && python -m pytest tests/test_stage5_final_release_freeze_hostile.py -v
```

## 14. Historical files

This repository preserves intermediate and historical artifacts for
provenance — that is intentional, not an oversight. You will encounter
older files (in `docs/`, `results/`, and elsewhere) containing statuses such
as `UNRESOLVED` or `NOT_READY`, or older experimental values such as the
capacity-confounded ~20.6% IMU figure discussed in §4. **These represent the
project's history, not its current state.** Always prefer the canonical
Stage-5 sources in §13 over any older document, including earlier versions
of this same README.

## 15. Running the demo

For a clean-machine / jury bring-up — including build-time API/WebSocket
configuration, CORS origin setup, health/connectivity checks, and failure-mode
behavior — follow [`docs/JURY_DEPLOYMENT_RUNBOOK.md`](docs/JURY_DEPLOYMENT_RUNBOOK.md)
and preflight with `python scripts/verify_jury_environment.py --root .`.

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API docs (Swagger UI): http://localhost:8000/docs

Or manually — backend (Python 3.11+):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (Node 20+), in a second terminal:

```bash
cd frontend && npm ci && npm run dev   # npm ci is reproducible from package-lock.json
```

Both run entirely offline once dependencies are installed. To enable real
recorded-data replay, see [`docs/DATASET_REPLAY.md`](docs/DATASET_REPLAY.md).

Backend/frontend test suites:

```bash
cd backend && .venv/bin/pytest -q          # or .venv/Scripts/pytest -q on Windows
cd frontend && npm run build                # strict TypeScript + Next.js build
```

## License / attribution

Research demonstrator for IAC 2026 — Haydarpaşa Lisesi team (F. Atila,
E. H. Sünbül, I. Y. Virdil, P. Özdemir). See
[`docs/PDD_Biological_Minimalism_IAC2026.md`](docs/PDD_Biological_Minimalism_IAC2026.md)
for full literature citations.
