# Research Mode — Jury-Facing Flow Spec (Day 8)

Turns `/research` into the primary evidence demo for the paper and jury. This spec defines the
flow and case-study displays. Backend endpoints already serve the frozen evidence
(`backend/app/api/routes/research.py`); the PENDING cards are backed by
`results/sleep_secondary_holdout_pending.json`. Frontend wiring of the PENDING cards is the one
remaining implementation step (see §Recommended wiring); nothing here fabricates evidence.

## The 8-step flow (per experiment)

1. **Research question** — target, baseline configuration, candidate sensor change.
2. **Real evidence** — dataset, held-out population, metric, replication, capacity fairness, negative controls.
3. **Heterogeneity** — subjects, classes, activities, sensitivity analyses.
4. **Marginal value** — positive / negative / neutral / heterogeneous (explicit tag).
5. **Operational burden** — body region, module, contact, power, mass, compute, unknowns.
6. **Claim boundary** — what is supported vs unsupported.
7. **Architecture status** — retain / conditional / deprioritize / future-evidence-required (from `architecture_decision_matrix.json`).
8. **Global readiness** — Pareto NOT_READY, with the blocker breakdown.

## Three visually distinct case studies

### Case 1 — IMU → HR (positive, capacity-controlled)
Show: original A→B (~20.6% raw), capacity control A_cap, corrected smaller effect (A_cap→B ~0.605,
C→B ~0.776 bpm, 5/5), shuffled-IMU control, activity heterogeneity, and the **"not pure 20.6%"**
caveat. Architecture status: **CONDITIONAL_FOR_TARGET**.

### Case 2 — second PPG → HR (heterogeneous negative)
Show: aggregate negative, s2 sensitivity, 2 better / 2 worse subjects, and the training-seed vs
population-replication distinction. Architecture status: **DEPRIORITIZE_FOR_TARGET** (not removal).

### Case 3 — EOG → sleep (positive, preliminary; controls pending)
Show as **frozen**: baseline A (0.7473), aligned B (0.7693), 4/5 seeds, primary n=3.
Show as **PENDING cards** (never as numbers): shuffled C / B>C, per-subject SC4011 dominance, and
the prospective secondary holdout — each labeled `PENDING_EXTERNAL_SCIENTIFIC_INTEGRATION`.
Architecture status: **FUTURE_EVIDENCE_REQUIRED**.

## Pending secondary-holdout support (schema-driven, no future numbers)

The UI reads `results/sleep_secondary_holdout_pending.json`:
- primary vs secondary cohort distinction
- support / weaken / contradict outcome vocabulary
- per-subject secondary results
All populated with `pending`/`null` until Ismet's branch is integrated. **Rule: never render
`null` as `0`.**

## User-visible claim boundaries (must always be on screen)

- Cross-dataset magnitudes are NOT comparable (MAE vs macro-F1).
- No astronaut/microgravity validation; spaceflight is motivation only.
- Digital Twin is architecture-only, untrained, unvalidated.
- Final architecture is UNRESOLVED / Pareto NOT_READY.

## Recommended wiring (next implementation step, scoped)

Add a `PendingEvidenceCard` to `frontend/src/components/research/ResearchMode.tsx` Case 3 that
fetches the pending artifact (or a thin `GET /research/sleep-pending` endpoint reading
`results/sleep_secondary_holdout_pending.json`) and renders each pending item as a labeled
placeholder. No frozen numbers change. This was intentionally left unwired this sprint to avoid
an unverified frontend build; the existing frozen Case 3 remains correct and honest as-is.
