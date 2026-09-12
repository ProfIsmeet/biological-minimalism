# Claude Scientific Handoff (Day 11-14)

Branch: `day11-14-scientific-parallel`, based on verified canonical
`origin/day10-canonical-integration` @ `e414ef5`. Does not modify `main`,
your Day-11 engineering branch, or the canonical integration branches
directly.

## What's new (files)

**Statistics**: `docs/STATISTICAL_REPORTING_STANDARD_DAY11.md`,
`results/statistical_unit_audit_day11.json`.

**Sensitivity (all read-only, from existing checkpoints/results)**:
`results/ppg_dalia_sensitivity_day11.json`, `results/ptt_sensitivity_day11.json`,
`results/sleep_edf_sensitivity_day11.json`,
`results/sleep_n3_extended_diagnostic_day11.json`,
`results/sleep_interaction_sensitivity_day11.json`.

**Tables/figures**: `results/scientific_master_table_day11.json`,
`results/paper_tables/` (5 tables, CSV+JSON), `results/figure_sources/`
(9 figures). All built programmatically
(`ml/build_scientific_master_table.py`, `ml/build_paper_science_tables.py`,
`ml/build_figure_sources.py`) - re-run these after any canonical result
changes rather than hand-editing.

**Clean-clone + reproduction guide**:
`docs/CLEAN_CLONE_REPRODUCTION_DAY13.md`,
`results/clean_clone_reproduction_day13.json`,
`docs/SCIENTIFIC_REPRODUCTION_GUIDE.md`.

**Checkpoint archival fix (real gap found and closed)**: the 10 Day-10
interaction checkpoints were NOT externally durable before this sprint.
New archive `biological_minimalism_checkpoints_day14.tar.gz` (GitHub
Release `day14-checkpoint-archive-v1`, verified byte-identical) covers
them; the Day-8 archive was not touched.
`results/final_checkpoint_inventory_day14.json` now shows 60/60
externally archived. **If your systems track ever needs the interaction
checkpoints, retrieve them from this new release, not the Day-8 one.**

**Paper package**: `docs/FURKAN_SCIENTIFIC_SOURCE_PACKAGE_DAY13.md` -
Methods/Results/Sensitivity/Reproducibility/Interaction/Limitations plus
a paper-safe claim bank (SAFE/UNSAFE/FUTURE) and exact table references.

**Freeze candidate**: `results/scientific_freeze_candidate_day14.json`
(status `SCIENTIFIC_FREEZE_CANDIDATE_READY_WITH_LIMITATIONS`),
`results/scientific_freeze_manifest_day14.json` (37-file hash chain).

**Hostile review**: `docs/HOSTILE_SCIENTIFIC_REVIEW_DAY14.md` - a
skeptical self-audit with an explicit claim-strength matrix. Worth reading
before citing any number in dashboard/jury copy.

## Exact items to integrate

- If your Research Mode / dashboard surfaces any PPG-DaLiA, PTT, or Sleep
  number, prefer sourcing it from `results/scientific_master_table_day11.json`
  or the paper tables (`results/paper_tables/`) rather than re-deriving it
  - they're the single source of truth going forward.
- If your checkpoint-retrieval tooling only knows about the Day-8 release,
  it needs to also know about `day14-checkpoint-archive-v1` for the
  interaction checkpoints.
- `results/sensor_marginal_value_contract.json`, `evidence_matrix`, and
  `experiments.*` were NOT changed by this sprint (no canonical value
  edits) - safe to keep whatever you currently read from it.

## Exact items NOT to reinterpret

- Do not upgrade any evidence-strength category based on the Day-11
  sensitivity analyses - they confirm/refine existing findings, they do
  not create new claims.
- Do not treat the interaction result as "no interaction" or "synergy
  found" - it is `approximately_additive_or_unresolved`, stated exactly
  that way everywhere.
- Do not merge Sleep primary (n=3) and secondary (n=8) into a pooled
  headline anywhere in UI copy.
- Do not describe the clean-clone test as a fully from-scratch dataset
  re-download - it used a verified-hash-matched file copy for raw data;
  say so if you cite it.
- Do not change the numpy version pin in `ml/requirements.txt` without
  re-running the reproduction checks - it's currently an intentionally
  disclosed gap, not yet "fixed."

## Full test suite

236 (Day 10) + this sprint's targeted tests, run and passing before push
- see the final report's Tests section for exact counts.
