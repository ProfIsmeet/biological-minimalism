# Ismet → Claude: Stage 2-4 Science Completion Handoff

**Verdict: `STAGE2_4_SCIENCE_COMPLETE_WITH_DATA_ACCESS_LIMITATIONS_READY_FOR_CLAUDE_CONTROLLED_INTEGRATION`**

Self-contained — Claude should need no chat history to act on this.

## 1. Repository state

Branch `stage2-4-science-owner-completion`, based on verified
`origin/stage2-4-expansion-science @ 0f1ba3be3d9275ae59f5d7ca951193a1f7109fdd`.
`main` untouched throughout at `b02c6db4434b22741077115786126a59643dc08b`.
Claude's `stage2-4-sleep-canonical @ d97b4d5` was read-only inspected, then
its final commit cherry-picked (verified purely additive, zero canonical
files touched) — never merged wholesale. `day12-post-remediation-integration
@ 52bd2ec` was read-only referenced, never merged.

## 2. What Claude should trust from this handoff

- **Sleep V2 corrected A/B**: unchanged, canonical, hash-verified untouched:
  `results/sleep_edf_primary_seedfix_v2.json`.
- **Sleep V2 corrected C**: NEW, real, complete:
  `results/sleep_edf_shuffled_eog_control_seedfix_v2.json`.
  B beats C by +0.0323 (4/5 seeds) — same direction/magnitude as A→B,
  genuine evidence of temporal-correspondence-driven EOG benefit.
- **Sleep V2 corrected interaction**: NEW, real, complete:
  `results/sleep_edf_interaction_resp_seedfix_v2.json`.
  `stability_classification: "approximately_additive_or_unresolved"`
  (interaction mean −0.0078, 3/5 seeds positive, 2/5 negative) — genuinely
  mixed, not resolved either way.
- **HMC bounded n=7 diagnostic**: NEW, real, but explicitly NOT canonical:
  `results/hmc_sleep_external_replication_stage3_bounded_n7.json`.
  Negative-leaning (B−A=−0.0313, 2/5 seeds favor B) at a tiny, 1-test-
  recording scale — do not cite this as "HMC results" without the bounded
  disclosure.
- **QDE V2** (from the prior expansion sprint, unchanged): negative-
  leaning, subject-2-dominated — `results/qde_v2_leg_bioz_stage2.json`.
- **ds003838 bounded n=3** (from the prior sprint, unchanged): access
  proven, inconclusive-by-design diagnostic —
  `results/ds003838_eeg_minimalism_stage3_bounded_diagnostic.json`.
- **GalaxyPPG / LBNP**: access UNBLOCKED this sprint (Zenodo reachable
  again). Real archives downloaded, MD5-verified, structure confirmed
  (24 / 16 subjects). A real GalaxyPPG cross-device UTC+9 timestamp bug was
  found and fixed (`ml/datasets/galaxyppg.py`) — R-peak reference-HR
  pipeline verified working end-to-end on real data. **Full A/B/C training
  was NOT run this sprint** (time-prioritized behind Sleep V2/HMC per
  explicit instruction) — no sensor-value claim exists for either dataset
  yet.

## 3. What Claude must NOT do with this

- Do not treat HMC's bounded n=7 result as the "HMC replication verdict."
- Do not treat GalaxyPPG/LBNP's unblocked access as if training happened.
- Do not merge V1 and V2 Sleep numbers, or Sleep-EDF and HMC numbers, into
  one combined claim.
- Do not promote Claude's own noncanonical A/B reproduction
  (`results/claude_noncanonical_sleep_edf_primary_seedfix_v2_reproduction.json`)
  over the canonical file — it remains supportive-only
  (`docs/CLAUDE_AB_REPRODUCTION_ADJUDICATION.md`).

## 4. Real bugs found and fixed this sprint (Claude should know these exist)

1. **HMC loader** (`ml/datasets/hmc_sleep.py`): derived-EOG channel marker
   never pulled in its two raw constituent channels — real `KeyError` on
   real data, fixed, regression test added.
2. **ds003838 loader** (prior sprint): `.set` files are MATLAB v7.3/HDF5,
   not classic-format — `mne.io.read_raw_eeglab` doesn't support it; fixed
   via direct `h5py` reading.
3. **GalaxyPPG cross-device sync**: Polar H10's `phoneTimestamp` is
   UTC+9 per the dataset's own README, not UTC like E4's — naive alignment
   produces a spurious ~9h gap; fixed with a documented −9h correction.
4. **A genuinely unexplained pre-existing untracked file** was found at
   this sprint's very start (`results/qde_v2_leg_bioz_stage2.json` on disk
   with no corresponding committed trainer) — moved aside, never used;
   every number in this handoff traces to a committed, deterministic,
   reproducibility-verified script.

## 5. External blockers (real, not bypassed)

- **PhysioNet TLS certificate expired mid-sprint** (verified via `openssl
  s_client`, `notAfter` in the past) — capped the HMC full-151 download at
  8 recordings. No `-k`/insecure bypass was used. Retry once PhysioNet
  rotates the cert (`docs/HMC_FULL_COHORT_CERT_EXPIRY_BLOCKER.md`).
- **Zenodo was unreachable for two entire prior sprints**, then resolved
  this sprint on one controlled recheck — treat as resolved unless it
  recurs.

## 6. Test suite state

`ml/tests/`: **405 passed, 0 failed, 0 skipped** (up from 365 at this
sprint's start — 40 new tests). `backend/`: **128 passed, 0 failed**
(unaffected, as expected — no backend code was touched this sprint).

## 7. Files Claude will want for integration

- `results/sleep_v2_complete_package.json` — one-stop A/B/C/interaction
  reference, builder script `ml/build_sleep_v2_complete_package.py`.
- `results/sensor_value_master_matrix_stage4.json` — 8-row master table,
  updated this sprint.
- `results/architecture_evidence_handoff_stage4.json` — unchanged,
  `final_architecture_status: UNRESOLVED`.
- `docs/STAGE2_4_SAFE_UNSAFE_CLAIMS.md` — exact safe-claim wording per
  experiment, updated with this sprint's real numbers.
- `docs/STAGE2_4_HOSTILE_REVIEW_ADDENDUM.md` — this sprint's specific
  findings, extends the prior sprint's `STAGE4_HOSTILE_SELF_REVIEW.md`.

## 8. Recommendation for controlled integration (recommendation only)

1. Integrate Sleep V2's C/interaction results additively into whatever
   Sleep V2 UI/paper/jury surfaces Claude's Stage 1A already built for
   corrected A/B — no existing artifact needs to change, only new ones
   need to be surfaced.
2. Do not surface HMC or GalaxyPPG/LBNP as "complete" anywhere user-facing
   yet — they are genuinely in-progress, honestly disclosed as such here.
3. Retry the HMC full-151 download once the PhysioNet certificate issue
   resolves (may already be fixed by the time Claude reads this — worth a
   quick recheck, same pattern as this sprint's Zenodo recheck).
4. GalaxyPPG/LBNP full A/B/C training is the next actionable science step,
   not blocked by anything except time — loaders and structure are ready
   (`ml/datasets/galaxyppg.py`; LBNP's `.mat` EIS-spectrum parsing is not
   yet written).
