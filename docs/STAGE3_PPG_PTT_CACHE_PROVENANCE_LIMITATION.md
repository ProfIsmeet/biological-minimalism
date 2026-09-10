# Section 30 remediation — PPG/PTT cache-provenance: documented remaining limitation

**Status: `DOCUMENTED_LIMITATION_NOT_FULLY_REMEDIATED_THIS_SPRINT`**, per the
master prompt's own explicit fallback ("PPG/PTT cache-provenance repair or
explicit documentation of remaining limitation if full remediation is
infeasible").

## The real gap

`ml/datasets/ppg_dalia.py::preprocess_subject()` and
`ml/datasets/pulse_transit_time_ppg.py::preprocess_record()` both cache
windowed tensors to a small `.npz` file keyed only by `subject_id`
(and `activity`, for PTT), and are idempotent purely on **path existence**:

```
if cache_path.exists():
    return cache_path
```

The cached `.npz` stores no raw-file content hash and no
preprocessing-code-version stamp. If the raw source file or the
`preprocess_subject`/`preprocess_record` windowing logic changes after a
cache file already exists, the stale cache is silently reused with no
detection or warning — the cache has no way to know it is stale.

`ml/datasets/cache_provenance.py` already defines the schema that would fix
this (`CacheProvenance`: `raw_file_sha256`, `preprocessing_version`,
`split_version`, `created_by_commit`, etc.), but by its own docstring it was
explicitly written spec-only and never wired into any existing loader
("Not wired into any existing loader by this sprint... avoiding touching
shared loader infrastructure while Claude's Stage 1A integration is in
flight").

## Why this is not fully remediated this sprint

`ppg_dalia.py` and `pulse_transit_time_ppg.py`'s cache read/write contract
underlies multiple already-completed, frozen, reported results (PPG-DaLiA
capacity control, PTT site ablation/sensitivity). Retrofitting content-hash
validation into the cache format mid-sprint, while GalaxyPPG's corrected
full-CV heavy job is running under this sprint's own one-heavy-job-at-a-time
rule, carries a real risk of either (a) silently changing which cached
windows get reused for an in-flight or future re-run, or (b) requiring a
full cache-invalidation and re-preprocessing pass to backfill provenance
fields into every existing `.npz`, which is itself non-trivial compute this
sprint's resource rule does not have room for alongside GalaxyPPG.

## What IS true today (partial mitigation, already in place)

- The cache write path already refuses to cache a **mislabeled** file: e.g.
  `preprocess_subject` raises if the pickle's own `subject` field does not
  match the requested `subject_id` ("refusing to cache a mislabeled file").
  This catches the most severe class of silent corruption (wrong subject's
  data cached under the wrong ID), even without full content-hash
  provenance.
- No PPG-DaLiA or PTT raw source file has been re-downloaded or modified at
  any point in this project's history since its cache was first built (this
  is an operational fact about how this session has actually been run, not
  a structural guarantee from the code) — so in practice, for every result
  currently reported in this repository, cache staleness has not actually
  occurred. This is a claim about this session's real history, not a
  property enforced by the code, and should not be relied on going forward.

## Recommended future remediation (not done this sprint)

Wire `CacheProvenance` into both loaders' cache-write path (store the
dataclass's `to_dict()` alongside the windowed arrays in the `.npz`, keyed
under a reserved array name e.g. `_provenance_json`), and have the
cache-read path recompute the raw file's SHA256 and compare against the
stored `raw_file_sha256`, raising on mismatch rather than silently
returning stale data. This should be scheduled as its own small, isolated
task (not bundled with a heavy-compute sprint) so any resulting
cache-invalidation/re-preprocessing pass can be resourced and verified on
its own.
