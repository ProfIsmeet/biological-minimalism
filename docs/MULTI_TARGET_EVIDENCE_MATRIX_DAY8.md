# Multi-Target Scientific Evidence Matrix (Accelerated Day 8)

Human-readable summary of `results/sensor_marginal_value_contract.json`
(methodology v1.2.0). **Do not rank rows against each other by raw metric
magnitude** — MAE (bpm) and macro-F1 are different metrics for different
tasks; see `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md` SS10.

## Target: Heart rate (PPG-DaLiA) — wrist IMU added to wrist PPG

| Field | Value |
|---|---|
| Original A/B/C (single seed) | A 9.090, B 7.032, C 7.957 bpm MAE |
| Multi-seed (5 seeds) | A 9.086±0.258, B 7.208±0.175, C 7.984±0.229 (sample SD) |
| **Capacity-control result** | A_cap 7.813±0.423 — **~68% of the original A→B gap was capacity, not IMU information** |
| Genuine IMU benefit (capacity-controlled) | 0.605±0.310 bpm, 5/5 seeds |
| Synchronization increment (C→B, unaffected) | 0.776±0.254 bpm, 5/5 seeds |
| Subject heterogeneity | 3/3 held-out subjects favor candidate (consistent) |
| Activity heterogeneity | 8/9 activities favor candidate; `table_soccer` is a stable negative case |
| Evidence strength | `replicated-within-dataset` (revised rationale, see contract) |
| Prohibited claims | Astronaut/microgravity validation; that this is a clean "pure IMU information" result (it no longer is — see capacity revision); cross-dataset MAE ranking |

## Target: Heart rate (PTT) — second physical PPG site

| Field | Value |
|---|---|
| Aggregate (5 seeds) | A 17.540±1.161, B 19.003±0.460 (sample SD) MAE |
| Seed stability | 5/5 seeds favor baseline (candidate consistently worse in aggregate) |
| Subject heterogeneity | 2/4 held-out subjects favor candidate |
| **s2 sensitivity** | Excluding s2 **flips** the aggregate direction (B becomes better); excluding any other subject does not |
| Evidence strength | `replicated-within-dataset` (seed-level), but subject-level evidence is genuinely small (n=4) and heterogeneous |
| Prohibited claims | That a second PPG site is globally harmful/unnecessary; cross-dataset MAE ranking against PPG-DaLiA |

## Target: Sleep stage (5-class, Sleep-EDF) — EOG added to EEG

| Field | Value |
|---|---|
| Aggregate (5 seeds) | Baseline 0.7473±0.0244, Candidate 0.7693±0.0132 macro-F1 |
| Seed stability | 4/5 seeds favor candidate (1 near-tie) |
| Class heterogeneity | Every class improves or is flat; largest gains in N1, REM; none regresses |
| Capacity | Avoided by design (1.35% parameter difference) — not a repeat of the PPG-DaLiA confound |
| Evidence strength | `preliminary` (first experiment for this target/dataset, no negative control yet) |
| Prohibited claims | Astronaut/microgravity sleep validation; EOG necessity; any macro-F1-vs-MAE numeric comparison |

## Cross-target observations (descriptive only, not a ranking)

- All three experiments are now built on the SAME rigor discipline:
  frozen predeclaration before training, subject-disjoint split, 5-seed
  replication, capacity-fairness discipline (retrofitted for PPG-DaLiA,
  designed-in from the start for Sleep-EDF), sample-SD (ddof=1) reporting,
  and independent checkpoint-reproducibility verification.
- Two of three experiments (PPG-DaLiA IMU, Sleep-EDF EOG) show a positive
  but heterogeneous/modest direction once properly scrutinized (capacity
  control; near-tie seed). One (PTT second site) shows a negative
  aggregate that is itself subject-heterogeneous and s2-sensitive. **None
  of the three should be read as a clean, unqualified "sensor X helps/
  hurts."**
- No experiment yet measures interaction effects between two candidate
  components — see `docs/SENSOR_INTERACTION_LIMITATION.md`.

## What is UNVALIDATED (not estimated)

Workload, fatigue, blood pressure, fluid shift, circadian stability — no
marginal-value experiment exists for any of these targets in this project
as of Day 8.
