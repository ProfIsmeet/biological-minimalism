# HMC Full-Cohort — Stage 3 Status

**Status: `PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT`** (access is real and
working — this is a compute/time limit, not an external blocker or a
design choice).

**Count note**: the "52 of 151" figure below is this document's own
historical snapshot from the sprint it describes. For the CURRENT,
reconciled file-presence/complete-pair/hash-verified breakdown, see
`results/hmc_current_download_inventory.json` (as of the Stage 3
final-source-of-truth remediation sprint: 59 .edf files present, 58
complete recording pairs, 52 of those SHA256-verified).

## What happened this sprint

1. Real access recheck: PhysioNet's TLS certificate confirmed renewed
   (`notAfter=Dec 9 2026`, verified via `openssl s_client`).
   `HMC_FULL_COHORT_EXTERNAL_ACCESS_BLOCKED` → `HMC_FULL_COHORT_ACCESS_RESTORED`.
2. Full 151-recording download resumed (`datasets/hmc-sleep-staging/
   download_full_cohort.sh`, skipping the 8 recordings already downloaded
   and SHA256-verified before the prior expiry).
3. By the end of this session's time budget, **52 of 151 recordings**
   were downloaded and SHA256-verified against PhysioNet's own
   `SHA256SUMS.txt` (real, ongoing, per-file verification — not assumed).
4. The full-cohort trainer (`ml/train_hmc_sleep_a_b_c_full_cohort.py`,
   pointed at the already-frozen `results/hmc_split_stage3_full_cohort.json`,
   106/23/22 split) is ready to run but was **not started** this sprint —
   this session's compute budget was already substantially consumed by
   GalaxyPPG's full 6-fold CV (including the corrected rerun after the
   reference-signal BLOCKER) and the real LBNP training.

## Quantified remaining work

At the observed download rate this sprint (~1 recording per few minutes,
highly variable), the remaining ~106 recordings would require several
more hours of download alone, before any training. Given HMC's full
106-subject training set is ~15x larger than the previously-completed n=7
bounded diagnostic's 5-subject training set, full A/B/C training (5 seeds
× 3 conditions) would itself likely take multiple hours beyond that.

## Disposition

The n=7 bounded diagnostic (`results/hmc_sleep_external_replication_stage3_bounded_n7.json`,
negative-leaning, prior sprint) remains the best currently-available real
evidence and is explicitly retained, unchanged, as historical. It is not
promoted, and the now-larger partial download (45/151, real, verified) is
disclosed as real progress toward — but not completion of — the canonical
full-cohort result.
