# Claude H1/H2 Scientific Remediation Handoff (Day 12)

Branch: `day12-sleep-scientific-remediation`, based on your verified
`day12-14-ismet-support-audit` @ `f2d895e`. Claude must not independently
reinterpret H1/H2 — this document states the exact conclusions.

## H1 conclusion

**Real bug, confirmed by reproduction probe, closed for Primary A/B with
updated numbers.** Every Sleep-EDF trainer constructed the model before
seeding torch's RNG, so the recorded seed never controlled initial
weights (only DataLoader order and the already-isolated EOG shuffle were
actually seed-controlled). A bounded, corrected-seed retraining
diagnostic for Primary A/B (10 new checkpoints, 5 seeds each) preserves
every qualitative conclusion exactly: same direction (+), same 4/5
seed-favor count, same SC4011-dominated subject pattern, same REM-driven
class pattern. Numbers shift modestly (expected — genuinely different,
correctly-seeded models), historical numbers are not deprecated.

**Not yet re-diagnosed**: the shuffled-EOG control (C) and the
interaction experiment (M_B/M_AB) — disclosed scope limitation, not a
silent gap (`PENDING_FOLLOWUP` in
`results/scientific_freeze_candidate_post_audit_day12.json`).

## H2 conclusion

**Real documentation/provenance bug, fully closed, zero data impact.**
Resp oro-nasal is natively 1 Hz (verified from the EDF header), not
100 Hz. MNE upsamples it to the 100 Hz common grid via FFT-based
resampling on load. The interaction training script has always used
`preload=True`, so the arrays used to train M_B/M_AB are exactly what
this correction describes — no retraining was needed or performed.

## Old vs. corrected numbers

| | Original (canonical, unchanged) | Corrected (new, confirmatory) |
|---|---|---|
| Primary A (EEG) macro-F1 mean | 0.7473 | 0.7365 |
| Primary B (EEG+EOG) macro-F1 mean | 0.7693 | 0.7647 |
| A→B delta | +0.0220 (4/5 seeds) | +0.0282 (4/5 seeds) |
| SC4011 delta | +0.0489 | +0.0838 |
| SC4081 delta | +0.0080 | +0.0045 |
| SC4131 delta | +0.0091 | +0.0009 |

Both rows are valid. `results/sleep_edf_eeg_eog_ablation.json` remains
canonical; `results/sleep_edf_primary_seedfix_v2.json` is the preferred
citation going forward if you want the more rigorously seed-provenanced
version, but using the original is not wrong.

## Which artifacts remain historical / become preferred

- **Remain historical, unchanged, still valid**: every existing Sleep-EDF
  result artifact and all 60 previously-archived checkpoints.
- **New, preferred-if-you-want-fully-seed-controlled-provenance**:
  `results/sleep_edf_primary_seedfix_v2.json` + its 10 new checkpoints
  (not yet externally archived — see Remaining Risks).
- **New, diagnostic-only, not a result artifact**:
  `results/sleep_seed_initialization_audit_day12.json`.

## Does Research Mode / the interaction panel need to change?

**No number needs to change.** If you want to add provenance transparency:
- Research Mode could optionally footnote that Primary A/B has a
  corrected-seed confirmatory version available (link
  `sleep_edf_primary_seedfix_v2.json`), but this is optional, not required.
- The interaction panel should incorporate the H2 bandwidth caveat if it
  currently describes Resp as "100 Hz" anywhere — check for this specific
  string; the source docs (`INTERACTION_EXPERIMENT_FEASIBILITY_DAY10.md`,
  `INTERACTION_EXPERIMENT_RESULTS_DAY10.md`) are already corrected.

## New safe wording

- "Resp oro-nasal is natively sampled at 1 Hz and represented on the same
  100 Hz grid as EEG/EOG via FFT-based resampling" — safe, exact.
- "Primary Sleep-EDF results were confirmed under a corrected,
  fully-seed-controlled retraining diagnostic" — safe, exact (for A/B
  only — do not extend this sentence to C or the interaction experiment).
- Do NOT say "the shuffled-EOG control has also been re-verified under
  corrected seeding" — it has not, this sprint.
- Do NOT say "Resp provides equivalent information to EEG/EOG" — it does
  not; its native bandwidth is much lower despite equal tensor length.

## Freeze status

`SCIENTIFIC_FREEZE_CANDIDATE_READY_WITH_LIMITATIONS` (restored from
`HOLD_PENDING_H1_H2`, held internally at this sprint's start). See
`results/scientific_freeze_candidate_post_audit_day12.json`.

## Files to merge

All new, additive files on `day12-sleep-scientific-remediation` — no
existing canonical artifact was modified in place except the two
documentation corrections (visible strikethrough, not silent edits) in
`docs/INTERACTION_EXPERIMENT_FEASIBILITY_DAY10.md` and
`docs/INTERACTION_EXPERIMENT_RESULTS_DAY10.md`, and the purely-additive
metadata constants in `ml/datasets/sleep_edf.py`.

## Remaining risk to flag

The 10 new `seedfix_v2` checkpoints are **not yet externally archived**
(they exist locally, gitignored, same as every checkpoint in this
project). Follow the same pattern as the Day-8/Day-14 GitHub Release
archives before relying on them from a fresh clone.
