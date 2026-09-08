# Test Taxonomy (audit M3 / §39)

The test suite mixes two kinds of test that must not be conflated. A stored-JSON
assertion is **not** a reproduction — it only checks that a committed artifact is
internally consistent with what the code expects, not that re-running the
pipeline reproduces the number.

## 1. Artifact-consistency tests

Load a committed artifact and assert its shape/values against the code's
expectations. They catch drift and mislabeling but do **not** re-run training or
inference. Examples:

- `backend/tests/test_research_api.py` — adapter projects committed result JSON
- `backend/tests/test_engineering_readiness.py` — typed projection of frozen inputs
- `backend/tests/test_reproducibility_panel.py` — typed status derivation (adversarial)
- `ml/tests/test_sensor_marginal_value_contract.py` — contract field consistency
- `ml/tests/test_day11_part2_engineering.py` — builder-output arithmetic/labels
- `ml/tests/test_day11_14_scientific_parallel.py::test_freeze_manifest_hashes_*` —
  hashes committed artifacts (canonical text hash), a consistency check
- `ml/tests/test_hash_provenance_policy.py` — hash-policy equivalence
- `ml/tests/test_claim_consistency_traceability.py` — traceability field/route existence

## 2. Executable-reproduction tests / verifiers

Actually re-execute a computation and compare to the frozen result. These are
the ones that justify a "reproduces" claim.

- `ml/verify_*.py` — reload frozen checkpoints, re-evaluate, compare (now all
  exit nonzero on mismatch, audit M9/§38)
- `ml/build_checkpoint_archive.py` + `ml/tests/test_checkpoint_archive_guards.py` —
  package, re-hash from inside the archive, verify membership + exit codes
- `ml/tests/test_ppg_dalia_cache_provenance.py` — exercises the cache reader's
  provenance verification (rejects mismatch, warns legacy)

## Rule

When describing coverage, say "artifact-consistent" for group 1 and
"reproduced" only for group 2. The reproducibility panel (`/research/summary`)
already distinguishes these: `canonical`/`robustness` components reflect
executable reproduction recorded in `results/day10_scientific_reproduction.json`,
while the panel's own status derivation is an artifact-consistency projection.
