# Reproducibility index

Single entry point for reproducing this project's evidence. Nothing here regenerates
a missing historical checkpoint and relabels it "original."

## 1. Checkpoint inventory (§14.1 / §14.2)

Machine-readable: **`results/checkpoint_inventory.json`** — regenerate with
`python ml/build_checkpoint_inventory.py`.

Current state (as inventoried):

| Metric | Value |
|---|---|
| Checkpoints referenced by committed artifacts | 26 |
| Present locally | 1 |
| Missing (gitignored / not archived) | 25 |
| SHA256 verified (of present) | 1 |
| SHA256 mismatched | 0 |

- The one **present, verified** checkpoint is the operational replay model
  `ml/checkpoints/model_b_ppg_plus_imu_ppg_dalia.pt`
  (SHA `c53a3458…`, pinned and enforced at load time in
  `backend/app/ml/ppg_dalia_hr.py::EXPECTED_CHECKPOINT_SHA256`). It is the single
  checkpoint the running system depends on.
- The 25 **missing** checkpoints are the PPG-DaLiA multi-seed (15) and PTT (10)
  per-seed weights. Their declared SHA256/size are recorded in the source artifacts
  and mirrored in the inventory, but the weight files are gitignored (`ml/checkpoints/*`)
  and are not currently archived anywhere durable.

## 2. Archival plan / handoff (§14.3)

No durable object store is configured in-repo, and uploading weights or raw datasets
requires credentials/authorization not available to this automated sprint. Therefore
this is a **precise handoff**, not an upload:

1. From a machine that still has the 25 weight files, confirm each file's SHA256/size
   against `results/checkpoint_inventory.json` (declared vs actual).
2. Archive the verified files to the team's durable store (e.g. a release asset bundle
   or institutional storage) under the exact POSIX paths in the inventory.
3. Record the archive location + retrieval instructions back into the inventory's
   `archival_status` on the next update.
4. Never re-train to "recreate" a missing historical checkpoint and present it as the
   original — a re-run is only a *new* checkpoint (see reconstructability below).

**Reconstructability:** deterministic training scripts exist
(`ml/train_ppg_dalia_imu_multiseed.py`, `ml/train_ptt_ppg_site_ablation.py`), but a
re-run is not guaranteed bit-identical unless environment + data are fully pinned, so
regenerated weights must be labeled as regenerations.

## 3. Environment freeze (§14.4)

- **Backend** (`backend/requirements.txt`): mostly pinned with `==`; `numpy` uses a
  bounded range. PyTorch is pinned to `torch==2.6.0` deliberately (see README's PyTorch
  note). *Recommended:* generate a hash-bearing lock (`pip-compile`/`uv pip compile`)
  without upgrading versions during the freeze.
- **ML** (`ml/requirements.txt`): largely unpinned — the weakest link. *Recommended:*
  pin exact versions used to produce the committed artifacts before archival, again
  without upgrading.
- **Frontend**: use the committed lockfile if present; do not bump versions during a
  freeze.
- Do **not** upgrade dependencies as part of freezing; pin what was actually used.

## 4. Dataset checksum manifests (§14.5)

Raw datasets are **never committed**. Integrity is verified against upstream-provided
checksums; a repository-side manifest records only the identity of files consumed:

- **PPG-DaLiA:** see `datasets/ppg-dalia/README.md` for download + verification.
- **PTT PPG:** see `datasets/ptt-ppg/README.md`; upstream ships `SHA256SUMS.txt`
  covering all 66 records (198 WFDB files + 67 CSV entries). Verify against it before
  preprocessing.
- A committed manifest should store, per dataset: source URL + version/DOI, license,
  the upstream checksum-file identity, and the frozen split artifact path — not the raw
  bytes.

## 5. Provenance chains (do not break)

`results/pareto_decision_inputs.json` embeds the SHA256 of the scientific contract,
operational catalog, and robustness artifact and re-verifies them at read time
(`backend/app/research/decision_inputs.py`). If you regenerate any of those, regenerate
the decision-inputs join in the same commit, or the research API will report the join
as `unavailable`. The frozen robustness SHA is additionally pinned as a constant.
