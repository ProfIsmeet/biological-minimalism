# Claude A/B Reproduction — Adjudication

**Verdict: ACCEPTED AS SUPPORTIVE REPRODUCIBILITY EVIDENCE. NOT PROMOTED TO
CANONICAL. CANONICAL JSON UNCHANGED (byte-identical hash verified before and
after import: `84efdc3f1d8636950c275dceb60da2979aeff841`).**

## Canonical (governing, Ismet-generated, Windows/torch build)

`results/sleep_edf_primary_seedfix_v2.json`:

- A (baseline EEG) mean = 0.7364866682288819, sd(ddof=1) = 0.02788511
- B (candidate EEG+EOG) mean = 0.7646892437262166, sd(ddof=1) = 0.01155095
- B−A mean = 0.028202575497334757
- 4/5 seeds favor B

## Claude's fresh reproduction (Mac, torch 2.14.0)

`results/claude_noncanonical_sleep_edf_primary_seedfix_v2_reproduction.json`:

- A mean = 0.733906766976478
- B mean = 0.7645271717211548
- B−A mean = 0.030620404744676755
- 4/5 seeds favor B

## Adjudication

| | Canonical | Claude repro | Diff |
|---|---|---|---|
| A mean | 0.73649 | 0.73391 | 0.00258 |
| B mean | 0.76469 | 0.76453 | 0.00016 |
| B−A mean | 0.02820 | 0.03062 | 0.00242 |
| Favorable seeds | 4/5 | 4/5 | same |

Per-seed max absolute difference ≈ 0.0084 macro-F1 (per Claude's own
handoff, independently plausible given the magnitude of the aggregate
diffs above). **Direction and favorable-seed count are identical.** The
numerical drift is consistent with cross-platform floating-point/BLAS
differences (Windows torch build vs. Mac torch 2.14.0) — the same class of
non-bit-exact-but-direction-preserving drift this project has already
documented elsewhere (e.g., the H1 remediation's own corrected-vs-original
comparison), not evidence of a protocol defect in either run.

**Decision**: the canonical Ismet-lineage `sleep_edf_primary_seedfix_v2.json`
remains the governing corrected A/B result. Claude's reproduction is
retained as a second, independent-platform confirmation of the same
direction and favorable-seed count — genuinely useful supportive evidence,
not a replacement, not averaged in, not cherry-picked for a better number.
The 10 reproduction checkpoints (gitignored, hashes in
`results/claude_to_ismet_science_transfer_manifest.json`) are not adopted
as canonical checkpoints; they remain `NONCANONICAL_PENDING_ISMET_REVIEW`
artifacts available for anyone who wants a second-platform loadability
check.
