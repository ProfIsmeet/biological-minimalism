# Final-Freeze Readiness Checklist (Day 8/9)

Prepares the repository for eventual final scientific freeze. **Do not freeze yet** — the sleep
shuffled control, per-subject decomposition, and secondary holdout are still pending integration
(`docs/DAY8_9_INTEGRATION_STATE.md`). Status: ☐ open · ◐ partial · ☑ done.

## Git
- ☑ Canonical branch identified (`day7-accelerated-integration` @ `230bd65`); systems work on `day8-9-systems-readiness`.
- ☑ Working tree clean at each commit.
- ◐ No raw datasets committed — verify `.gitignore` covers `datasets/*/` payloads before freeze.
- ☑ No accidental outputs staged (only intended docs/results).
- ☐ Tag strategy: reserve `vX.Y-final-freeze` for after Ismet integration; do NOT tag now.

## Scientific artifacts
- ☑ Result JSONs present for all three experiments + capacity/sensitivity/robustness.
- ☑ Methodology contract (`results/sensor_marginal_value_contract.json`) present.
- ◐ Provenance hashes — re-verify the SHA chain after any regeneration (contract→operational→decision-inputs→join).
- ☑ Checkpoint manifests present (`results/checkpoint_*`); external archival schema staged (pending).
- ☑ Dataset manifests present (`datasets/DATASET_MATRIX.md`).
- ☐ Environment manifest — confirm a frozen `requirements`/lockfile snapshot before freeze.

## Dashboard
- ☑ No hardcoded science values on live surfaces (consistency checker passes).
- ☑ No stale claims (checker: 0 issues).
- ◐ API-backed — Research Mode Case 3 PENDING cards not yet wired (documented; existing frozen view correct).

## Paper
- ☑ All current numbers traceable to an artifact (`results/claim_traceability.json`).
- ☑ Figure plan references only artifact-backed data (`docs/FURKAN_PAPER_SUPPORT_DAY8.md`).
- ☑ All claims bounded (safe/unsafe/future claim bank).

## Reproducibility
- ☑ Checkpoint SHAs recorded; ◐ external durability pending Ismet.
- ☐ Environment pin (Python + node versions) captured for freeze.
- ◐ Dataset access instructions present; verify no payloads tracked.
- ☑ Split files committed for each experiment.
- ☑ Code version recorded per experiment (commit hashes in provenance).
- ☑ Artifact SHAs in the decision-inputs source list.

## Blocking before freeze
1. Integrate `day8-sleep-strengthening-ml` (shuffled control + per-subject) and re-verify.
2. Integrate `day9-sleep-secondary-holdout-ml` outcome.
3. Obtain verifiable external checkpoint-archive location + SHA.
4. Re-run: backend suite, `python3 ml/check_claim_consistency.py`, all builders, frontend lint+build.
5. Confirm `.gitignore` excludes raw dataset payloads; capture environment pins; then tag.
