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

---

## Day 8/9 Canonical Integration — Updated Sleep Answers

After merging Ismet's shuffled-EOG control, per-subject decomposition, and prospective
secondary holdout, the strongest defensible answers to the sleep line of attack are:

**Q: "Sleep is only 3 subjects."**
Correct for the *primary* frozen test (n=3), and we disclose it is dominated by one subject
(SC4011). We did not enlarge or re-split the primary test. Instead we prospectively froze a
*separate* 8-subject secondary cohort (SC4181–SC4251), subject-disjoint from train/val/test,
before evaluation, and evaluated the existing frozen checkpoints with **zero retraining**. The
direction reproduced (A→B 5/5 seeds; 6/8 subjects B>A). Primary and secondary are reported
**separately** — never pooled into an "n=11" test.

**Q: "Your result depends on SC4011."**
For the primary n=3 test, yes — and we say so (`global_result_dominated_by_one_subject=true`).
The secondary holdout is the answer: its effect is *not* single-subject-dominated (largest
subject SC4221 ≈ 41% of the summed effect, not ~100%), so the secondary cohort materially
strengthens the finding's robustness.

**Q: "Where is the negative control?"**
Integrated. Model C = EEG + EOG shuffled within-subject/within-partition, capacity-identical to
B. Aligned B beats shuffled C in **5/5 seeds** in both the primary and the secondary evaluation,
while A→C is ≈ neutral. The benefit depends on *temporal alignment*, not the mere presence of an
EOG-shaped input.

**Q: "Does EOG really provide timing information?"**
That is exactly what the shuffled control isolates: destroying EOG↔EEG temporal alignment removes
the benefit. This is evidence for aligned ocular *timing* information, offered as support — not
causal proof.

**Q: "Did the secondary holdout use retraining?"**
No. The 15 frozen checkpoints (A/B/C × seeds 42–46) were reloaded unmodified; no training, no
tuning, no outcome-based seed selection. Reproducibility artifact shows 5/5 exact macro-F1 match.

**Q: "Why is N3 worse?"**
Disclosed, not hidden. In the secondary cohort N3 per-class F1 regresses (B−A ≈ −0.043) while REM
gains strongly (+0.150). A read-only confusion diagnostic (no retraining) shows it is a
*precision* effect: B over-labels true N2 epochs as N3, so N3 precision drops (~0.50→0.43) even
though N3 recall improves (~0.85→0.88). We do not invent physiology beyond this observation.

**Q: "Is this independent replication?"**
No — and we never claim it. Evidence strength stays **replicated-with-control** with a
**prospective_secondary_holdout_supported** qualifier. It is same-dataset (Sleep-EDF cassette),
terrestrial. Independent-dataset / cross-population replication remains explicitly unsupported.

### Strongest five claims (current)
1. Aligned EOG improved 5-class sleep macro-F1 in the primary test **and** a prospectively-frozen
   8-subject secondary holdout (same dataset), A→B 5/5 seeds in the secondary.
2. A capacity-identical shuffled-EOG control is worse than aligned EOG in **5/5 seeds** in both
   evaluations → benefit depends on temporal alignment.
3. Capacity-controlled IMU HR benefit persists after A_cap matching (A_cap→B ~0.605 bpm, C→B
   ~0.776 bpm, 5/5 seeds).
4. Checkpoint archival is externally durable and independently re-verified (SHA `5e0661a6…`, 50
   checkpoints, 0 raw datasets).
5. Every live claim is artifact-traceable; the consistency checker passes with 0 issues.

### Strongest five limitations (current)
1. Sleep evidence is single-dataset, terrestrial; not independent-dataset replication.
2. Primary sleep effect is SC4011-dominated; secondary benefit is broader but not uniform (2/8
   near-zero/negative).
3. N3 regresses in the secondary cohort (precision effect, disclosed).
4. Final architecture is **UNRESOLVED**; formal Pareto is **NOT_READY** (no power/mass/BOM).
5. Interaction evidence is only **partial** — one controlled EEG×EOG×Resp pair was tested (approximately additive/unresolved); marginal-value experiments still do not prove a globally minimal sensor set.

## Day 10 — Reproducibility & interaction Q&A

**Q21: "Can your results actually be reproduced?"**
Yes, from frozen artifacts. Every checkpoint-based canonical result (PPG-DaLiA capacity control + multiseed, PTT A/B, Sleep primary + secondary A/B/C) was re-evaluated from the frozen checkpoints with **exactly zero** numerical difference; the full 114-condition robustness sweep reproduced within a documented float32 tolerance (max 7.6e-6 bpm). Overall `SCIENTIFIC_REPRODUCTION_PASS`.

**Q22: "Did you re-run them under the same environment?"**
Yes. We verified the training/evaluation stack field-by-field against the frozen manifest (Python 3.13.0, PyTorch 2.6.0+cpu, NumPy 2.5.2, SciPy 1.18.1, scikit-learn 1.9.0, MNE 1.12.1, WFDB 4.3.1, pandas 3.0.5) → `EXACT_FROZEN_ENVIRONMENT`. No package was changed to force a match. (The separate Mac integration env is never used to produce a scientific result.)

**Q23: "How do you know the raw datasets are identical?"**
All 266 raw input records used by the canonical experiments (PPG-DaLiA 16, PTT 198, Sleep primary 36, Sleep secondary 16) are fingerprinted; 266/266 present, **0 raw files committed to git**.

**Q24: "Did you test sensor interactions?"**
Once, cleanly. We predeclared and ran a capacity-fair (112 params/channel) EEG × EOG × Resp factorial on Sleep-EDF (M0/M_A/M_B/M_AB, 5 seeds).

**Q25: "What did the EOG×Resp interaction show?"**
An interaction term of **+0.0031 ± 0.0434** macro-F1 (2/5 seeds positive): approximately additive / unresolved. Adding both EOG and respiration did not show a stable extra benefit beyond their individual effects under this model and dataset.

**Q26: "Does a near-zero interaction mean interactions don't matter?"**
No. This is one candidate pair, one target, one dataset, one model family. It does **not** prove sensor interactions are absent in general, and it is **not** an EOG+Resp synergy claim. It is honest, bounded methodological evidence, not a headline result.

**Q27: "Is this independent replication now?"**
No. It is **independent re-evaluation from frozen artifacts** on the same stack. Same-team, same-machine reproduction — not an independent-dataset or independent-lab replication. We say so explicitly.

**Q28: "What is the physical cost of adding EOG?"**
Horizontal EOG needs **2 lateral-ocular sensing electrodes** (interpretation-independent). Under a shared-reference head-module architecture it reuses the existing ADS1299-class reference/bias and adds **no new module** (standalone interpretation: 3–4 contacts, possibly a new front-end). Incremental power and mass are **NOT_READY** — not zero, not quantified. The EOG contact burden is not free, which is why EOG stays CONDITIONAL.

**Q29: "Why is N3 worse with EOG?"**
Descriptively: in the secondary cohort aligned EOG raises N3 recall (0.853→0.884) but lowers N3 precision (0.499→0.430) because it produces ~605 more N2→N3 false positives; REM gains strongly. We report this as a read-only diagnostic and do **not** offer a physiological causal explanation.

**Q30: "Why is Pareto still NOT_READY after all this work?"**
Because reproducibility strengthens confidence but does not supply the missing engineering axes: cross-target metrics remain incomparable (HR MAE vs sleep macro-F1), system average power and system mass are unquantified, the full module BOM/allocation is unselected, and interaction coverage is only partial. `FORMAL_PARETO_NOT_READY` is the honest status.
