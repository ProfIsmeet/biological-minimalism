# Jury-Defense Master Bank — Biological Minimalism (IAC 2026)

Evidence-backed answers. Every answer distinguishes **proven** / **supported-with-limitations** /
**proposed** / **future**. No marketing bluff. Numbers trace to committed artifacts.

## Claim ladder (use this to avoid upgrading weak evidence)

- **Tier 1 — strongest (replicated + control-supported):** capacity-controlled IMU→HR benefit
  (5/5 seeds, shuffled-IMU control); the honest NOT_READY architecture result.
- **Tier 2 — supported but limited (single dataset / heterogeneous):** second-PPG→HR heterogeneous
  negative; EOG→sleep modest positive (3 subjects, preliminary; controls pending).
- **Tier 3 — demonstrated in software:** dashboard, replay, synthetic fault-injection flow.
- **Tier 4 — proposed:** Biological Digital Twin, astronaut deployment, final wearable, power/mass.

---

## The 5 most dangerous attacks (and the strongest answers)

1. **"This is just ordinary sensor ablation."** — No: it pairs each ablation with a capacity/
   architecture control, a negative (shuffled) control, subject/heterogeneity decomposition, an
   operational-burden model, and an explicit decision gate that *refuses* to select when evidence
   is incomplete. The contribution is the disciplined refusal, not the ablations.
2. **"The IMU result is just model capacity."** — Partly, and we measured it: a capacity-matched
   PPG-only control (A_cap) recovers most of the raw A→B gap; the residual capacity-controlled
   benefit (A_cap→B ~0.605, C→B ~0.776 bpm) is small but 5/5 seeds. We never claim the raw ~20.6%
   as pure IMU value.
3. **"You call it a space project with no microgravity data."** — Correct; spaceflight is
   **motivation, not validation**. Every artifact prohibits astronaut/microgravity claims. The
   contribution is a terrestrial, reproducible *method* for deciding sensing burden.
4. **"Why publish NOT_READY — isn't that a failure?"** — It is the honest result and the point:
   the method declines to fabricate a Pareto frontier when power/mass/interaction/BOM evidence is
   incomplete. A method that only ever says "yes" is not a method.
5. **"The sleep result is 3 subjects."** — Yes; it is Tier 2, preliminary, effect ≈ seed SD. The
   shuffled-EOG control and per-subject decomposition, plus a prospective secondary holdout, are
   the specified next evidence and are pending integration — we show them as pending, not as results.

---

## The 25 questions

1. **Why "Biological Minimalism" with many candidate sensors?** — Minimalism is the *decision
   principle* (justify each component's target-specific value against its human burden), not a
   count. *Proven method; architecture proposed.*
2. **Why isn't the final architecture selected?** — Interaction evidence is unavailable, burden
   (power/mass/BOM) is incomplete, and cross-dataset metrics are incomparable; the gate returns
   UNRESOLVED. *Proven (gate logic).* `results/architecture_decision_matrix.json`.
3. **Why did the original four-sensor idea change?** — Evidence replaced assertion: one-at-a-time
   marginal experiments showed value is target-specific and heterogeneous, so a fixed four-sensor
   claim was not defensible. *Supported.*
4. **Wasn't the IMU result mostly model capacity?** — Largely; measured via A_cap control. Residual
   IMU-information benefit is small but replicated. *Tier 1, with limitation.*
5. **What is the clean IMU result now?** — Capacity-matched C→B ~0.776 bpm and A_cap→B ~0.605 bpm
   MAE, 5/5 seeds; **not** the raw ~20.6%. *Proven within PPG-DaLiA.*
6. **Why does shuffled IMU help?** — It supplies context/energy the model exploits even without
   temporal synchronization, so synchronization explains only part of the gain — which is exactly
   why the shuffled control matters. *Proven (control present).*
7. **Doesn't PTT depend entirely on s2?** — The aggregate direction is s2-dominated (OOD high-HR
   subject); descriptively removing s2 flips it. We keep s2 per protocol and report the sensitivity.
   *Supported, bounded.* `results/ptt_sensitivity_analysis.json`.
8. **Why keep a negative PTT result?** — Because the method must publish negatives; hiding them
   would make the positives meaningless. *Method principle.*
9. **Why is Sleep-EDF only 3 primary test subjects?** — First experiment for this target; a
   subject-disjoint 12/3/3 split. It is preliminary; a secondary holdout is pending. *Tier 2.*
10. **Why is the sleep result dominated by SC4011?** — Per-subject decomposition (pending
    integration from the ML branch) indicates concentration in SC4011; we present it as pending,
    not as a frozen number. *Future/pending.*
11. **Why does shuffled-EOG matter?** — It is the matched negative control separating real ocular
    information from added-channel capacity; B>C is the meaningful comparison. *Pending integration.*
12. **Is EOG now proven necessary?** — No. Modest, preliminary, 3 subjects; necessity is not
    claimed. *Supported-limited.*
13. **Where is the Digital Twin?** — Architecture-only, untrained, unvalidated; a synthetic demo
    exists. *Proposed.* `results/digital_twin_architecture_footprint.json`.
14. **Why call this a space project without microgravity data?** — Motivation vs validation; no
    microgravity claim is made anywhere. *Scope statement.*
15. **Where is the wearable?** — No final BOM/module is frozen; burden is modeled with explicit
    unknowns. *Proposed.*
16. **Where is power reduction?** — Not claimed; only component-IC operating points exist; average
    power is `unknown`. *Future.*
17. **Where is mass reduction?** — Not claimed; incremental finished mass is missing. *Future.*
18. **Why no Pareto frontier?** — Incomparable metrics + missing power/mass + no interaction
    evidence; a frontier would be fabricated. *Proven (NOT_READY).* `results/pareto_readiness_blockers.json`.
19. **Why no uncertainty?** — The models are point estimators; no calibrated uncertainty head
    exists, and we say so. *Limitation, honest.*
20. **Why publish NOT_READY?** — It is the honest gate output; see the 5-attack answer 4. *Proven.*
21. **Why are metrics across datasets not compared?** — MAE (bpm) and macro-F1 on different
    populations are not rankable coordinates; the artifacts prohibit it. *Method principle.*
22. **What is actually novel?** — A reproducible, control-anchored, burden-aware decision gate that
    refuses unjustified sensor selection, applied across regression and classification targets.
23. **How is this different from ordinary sensor ablation?** — See attack 1: controls + burden +
    heterogeneity + refusal gate + provenance/traceability.
24. **Why should an IAC jury care?** — Sensing burden is a real operational constraint in
    spaceflight; a method that decides burden honestly is more useful than an over-claimed suite.
25. **What is the next experiment before deployment?** — A factorial interaction experiment
    (baseline/+A/+B/+A+B) on one target, plus the sleep secondary holdout, plus a frozen module BOM
    to quantify average power and finished mass. *Future.*
