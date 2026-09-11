# Stage 4 — Science Owner Handoff to Integration Owner

## 1. Accepted Stage-3 SHA

Branch `stage3-gate3-final-resolver-closure`, SHA
`5c381014af61e5d10d41223963831b25b9ff23e6`. Accepted state:
`STAGE3_CORE_AND_PRIORITY_SCOPE_VERIFIED_COMPLETE_WITH_LOWER_PRIORITY_EXTERNAL_WORK_PENDING`.
This SHA is frozen — never rewrite, amend, or rebase it, and never modify
its results in place.

## 2. Governance consumption rules

Resolve all current Stage-3 evidence through
`ml/stage3_science_resolver.py`, calling `resolve_current(family_id)`
(an integrity-verified alias of `resolve_and_verify`). Never read a
result file directly by guessed filename, and never call the private
`_resolve_current_unverified()` helper. The resolver fails closed against
historical, superseded, invalidated, noncanonical, pending, and
hash-corrupted artifacts.

## 3. Governing result summary

See `results/stage4_science_consumption_manifest.json` for the full
per-family detail (10 families: Sleep A/B, Sleep C, Sleep interaction,
PPG-DaLiA capacity-controlled, PTT second-site, QDE V2, GalaxyPPG
corrected full CV, LBNP corrected v2, HMC bounded diagnostic, ds003838
bounded diagnostic). Headline governing numbers:

- **PPG-DaLiA**: A_cap→B +0.605 bpm, C→B +0.776 bpm (5/5 seeds both).
- **GalaxyPPG**: participant A_cap→B +0.834268 bpm (12/18), C→B
  +0.916231 bpm (13/18); `EXTERNAL_REPLICATION_SUPPORTIVE`.
- **Sleep-EDF A/B/C**: B−A +0.0282, B−C +0.0323 (4/5 seeds both).
- **Sleep interaction**: −0.0078, mixed-sign seeds — unresolved.
- **PTT second site**: B−A +1.462 MAE (worse), n=4 test, fragile.
- **QDE V2 leg BioZ**: A−B −0.052, C−B −0.060 (aggregate disfavors B;
  7/10 subjects individually favor B) — heterogeneous.
- **LBNP thoracic EIS**: A−B −0.452 (sign-reverses w/o subject 9), C−B
  −1.293 (shrinks substantially w/o subject 9); `COMPLETE_MIXED`.
- **HMC bounded n=7**: B−A −0.031 (2/5 seeds) — inconclusive at this
  scale, not a negative external replication.
- **ds003838 bounded n=3**: inconclusive by design.

## 4. Sensor-value summary

See `results/stage4_scientific_sensor_value_matrix.json` for all 10
modalities. Architecture-implication tiers used
(`STRONGLY_SUPPORTED_CORE` / `SUPPORTED` / `CONTEXTUAL_LOW_BURDEN` /
`MIXED` / `DEPRIORITIZED` / `EXPERIMENTAL` / `PENDING_EXTERNAL_VALIDATION`)
are decision inputs, never `KEEP`/`REMOVE`.

## 5. Claim boundaries

See `results/stage4_science_claim_ledger.json` for exact safe wording,
strength, and prohibited stronger wording per claim area (14 claim
areas covering every major result plus Digital Twin, final architecture,
Pareto, and astronaut/microgravity applicability).

## 6. Explicit allowlist / 7. Explicit exclusion list

See `results/stage4_integration_science_allowlist.json`.

## 8. Pending HMC/ds003838 science

Both remain `LOWER_PRIORITY_EXTERNAL_WORK_PENDING`. HMC: 59 edf present,
58 complete recording pairs, 52 SHA256-verified, 1 partial (SN060); full
151-cohort training not started. ds003838: n=3 bounded diagnostic only;
full ~65-subject cohort needs ~93GB/~9.4h additional download, not
attempted. See `results/stage4_architecture_decision_inputs_science.json`
for which pending results have HIGH decision sensitivity (EOG's external
validity via HMC full; sparse-vs-full EEG via ds003838 full) versus LOW
(thoracic EIS, leg BioZ, second-site PPG — no currently-planned
Stage-3 experiment would resolve these further).

## 9. Architecture remains unresolved

`final_architecture_status = UNRESOLVED`. `formal_pareto = NOT_READY`.
Verified directly against `results/architecture_evidence_handoff_stage4.json`
and `results/stage3_science_completion_manifest.json` as of this handoff.

## 10. What Integration Owner MAY do next

- Consume verified Stage-3 science via the resolver.
- Integrate it into backend/API/frontend.
- Update Research Mode and dashboard presentation using the claim ledger's
  exact safe wording.
- Wire claim traceability referencing this package's artifacts.
- Update engineering evidence with the science decision inputs.
- Use `results/stage4_architecture_decision_inputs_science.json` and the
  sensor-value matrix for architecture *analysis* (not selection).
- Create an integrated Stage-4 candidate.

## 11. What Integration Owner MUST NOT do

- Train or retrain any model, or rerun any scientific experiment.
- Resume HMC or ds003838 download/training.
- Override any Science Owner classification (e.g. `COMPLETE_MIXED`,
  `EXTERNAL_REPLICATION_SUPPORTIVE`).
- Substitute a historical/invalidated/superseded/noncanonical artifact
  for a governing one.
- Promote either pending HMC or ds003838 result to a full-cohort claim.
- Declare a final architecture or a completed Pareto frontier.
- Promote the Digital Twin beyond "conceptual, synthetic, not
  longitudinally validated."

## 12. Science-facing Stage-4 synthesis (for future paper/jury integration — not a final paper)

- **Strongest positive result**: PPG-DaLiA's capacity-controlled IMU
  benefit (A_cap→B +0.605 bpm, 5/5 seeds) — a clean, capacity-matched
  comparison, the methodological gold standard in this package.
- **Strongest independent replication**: GalaxyPPG's corrected full
  6-fold CV (participant A_cap→B +0.834 bpm, 12/18 favor B) — an
  independent device/subject family from PPG-DaLiA, with real,
  disclosed heterogeneity rather than a suspiciously clean result.
- **Important negative result**: LBNP thoracic EIS (`COMPLETE_MIXED`,
  negative-leaning) — real n=12 experiment under a corrected,
  protocol-compliant design, showing no stable incremental value for the
  tested target.
- **Important mixed result**: QDE V2 leg BioZ — aggregate mean disfavors
  the addition, yet 7/10 individual subjects favor it; a genuine
  aggregate-vs-per-subject tension, not resolved by more modeling.
- **Evidence downgraded after better control**: the historical
  ~20.6%/23% PPG+IMU headline used unequal model capacities (Model A
  8,065 params vs Model B 28,865/29,089 params); under a capacity-matched
  re-analysis the real effect is smaller (+0.605 bpm) — a concrete
  example of a control materially changing a scientific claim's strength.
- **Example of heterogeneity**: GalaxyPPG's 6/18 subjects who favor the
  no-IMU baseline, disclosed rather than smoothed into a clean aggregate.
- **Why minimalism is evidence-driven, not arbitrary sensor deletion**:
  every modality in this package was tested against a capacity-matched
  and/or deranged/shuffled control, evaluated at the subject level (not
  just pooled windows), and classified according to what the data
  actually showed — supportive (PPG+IMU), same-dataset-bounded (EOG),
  mixed (leg BioZ, LBNP EIS), or negative-leaning (second-site PPG) —
  rather than a uniform "more sensors is better" or "fewer sensors is
  better" prior.

**Central storyline** (preserve this framing, do not simplify it):
Biological Minimalism evaluates whether each sensing modality contributes
measurable incremental value after controlling for model capacity,
temporal correspondence, biological subject separation, and
heterogeneity. Some modalities retain value under stronger controls and
external replication (wrist IMU), while others become mixed, negative,
or deprioritized (thoracic EIS, leg BioZ, second-site PPG), and some
remain genuinely open pending further external validation (EOG, sparse
EEG). This has **not** established that "four sensors are enough" or any
similarly compressed claim — do not let Stage 4 or later paper drafts
collapse this into that.
