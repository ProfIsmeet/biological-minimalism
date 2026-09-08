# ds003838 EEG Channel Minimalism Protocol (Stage 1B)

**Classification: GO_WITH_LIMITATIONS**

Full machine-readable facts: `results/ds003838_metadata_audit_stage1b.json`,
`results/ds003838_protocol_stage1b.json`.

## Scientific purpose

How much workload-related information is lost when high-density research
EEG is reduced to a sparse, wearable-compatible EEG subset?

## Actual-file verification (real, not paper-abstract-only)

Directly fetched `participants.tsv` (86 rows), `dataset_description.json`,
and one representative subject's (sub-032) BIDS sidecars from the OpenNeuro
GitHub mirror this sprint. **65/86 subjects have usable EEG** — confirmed
two independent ways that agree exactly: the README's own enumerated
21-subject exclusion list, and an independently computed count from
`participants.tsv`'s `EEG_excluded` column. 83/86 have usable ECG/PPG.

EEG facts read directly from a real `*_eeg.json` sidecar: **63 channels,
1000 Hz, actiCHamp, FCz reference, Fpz ground, 50 Hz power line (not 60
Hz — checked, not assumed)**. Target: externally-imposed 5/9/13-digit
sequence length, from real per-digit-position trigger codes in
`events.tsv`/`events.json`.

## Resource reality check

Git-annex object pointer sizes give a **real, measured** per-subject
footprint: ~1.47 GiB (memory task) + ~45 MiB (rest task) per subject. For
all 65 usable-EEG subjects, that's **~96–99 GB** for EEG-only download —
meaningfully smaller and more actionable than the prior research audit's
rough ~250 GB estimate. The rest task isn't needed for this protocol and
can be skipped entirely.

## Frozen sparse channel set: AF7, AF8, TP9, TP10

This is the **exact Muse consumer-headband electrode montage** — tying the
"wearable-compatible subset" framing to a real shipping product's real
geometry rather than an arbitrary guess. All four channels were confirmed
present in ds003838's real montage before freezing this choice. Not
reconsidered after results.

## Frozen A/B/C

- **A**: sparse EEG (AF7, AF8, TP9, TP10).
- **B**: full 63-channel montage.
- **C**: full-montage architecture; the 59 non-A channels temporally
  deranged **across trials, within subject** (A's 4 channels stay real).

## Model fairness

A channel-wise shared encoder (identical per-channel weights, fixed-width
aggregation) keeps A and B's total parameter count nearly identical — only
channel count differs, avoiding giving B a raw-capacity advantage.

## Metric

Primary: Macro-F1 (3-class). Secondary: balanced accuracy, ordinal error
(the 5/9/13 classes have a natural order).

## Claim limits

See `docs/STAGE1B_EXPANSION_FORBIDDEN_CLAIMS.md` — most notably: no claim
that four channels "capture cognition" or generalizes beyond this task.
