# HMC Stage 2: Bandwidth-Driven Reduced-Cohort Deviation (frozen before any HMC file was opened)

**Status: PROTOCOL DEVIATION, FROZEN BEFORE OUTCOME INSPECTION.**

## What this documents

`docs/HMC_SLEEP_EXTERNAL_REPLICATION_PROTOCOL_STAGE1B.md` and
`results/hmc_protocol_stage1b.json` (Stage 1B, commit `fe32384`, inspected
read-only from `origin/stage1b-dataset-expansion-prep`, NOT merged) freeze a
design against the **full 151-recording** HMC Sleep Staging cohort
(PhysioNet v1.1, 15.7 GB uncompressed).

This integration clone's outbound bandwidth to PhysioNet was directly
measured during the Sleep-EDF Stage-2 download (this session, same host,
same network path) at approximately 150-250 KB/s sustained. At that rate,
15.7 GB would require roughly 18-24 hours of continuous download - not
feasible within this session's real-time bound.

## Deviation

Rather than fabricate full-cohort results or claim HMC is "inaccessible"
when it is not, this session downloads a **reduced, sequentially-selected
subset of 12 recordings** (~1.2 GB, real PhysioNet HMC data, byte-verified
against `SHA256SUMS.txt`) and runs the FULL Stage-1B-frozen A/B/C protocol
(same EEG derivation C4/M1, same EOG derivation E1/M2-E2/M2, same corrected
H1 seed order, same control-C design, same primary metric) on that subset.

**This is a disclosed reduction in cohort size, not a change to the
scientific design.** Every other element of `results/hmc_protocol_stage1b.json`
(channel choice, stage mapping, seed protocol, control-C definition,
capacity-fairness design, primary/secondary metrics, forbidden-claims list)
is preserved unchanged.

## Selection rule (decided BEFORE downloading or opening any HMC file)

Sequential RECORDS order (`https://physionet.org/files/hmc-sleep-staging/1.1/RECORDS`,
which lists SN001, SN002, SN003, ... in ascending numeric order with no
outcome-related information available at selection time - subject IDs
carry no known relationship to sleep-stage distribution or data quality).
First 12 recordings, split by continuing the same sequential order into
train/val/test:

- **train (8):** SN001, SN002, SN003, SN004, SN005, SN006, SN007, SN008
- **val (2):** SN009, SN010
- **test (2):** SN011, SN012

Frozen split artifact: `results/hmc_split_stage2.json`.

## Consequence for claim strength

A 12-recording pilot is **not** a full independent-family replication at
the power Stage 1B's frozen 151-recording design intended. Stage 3's final
verdict language must reflect this explicitly (e.g.
`PARTIAL_REPLICATION_REDUCED_COHORT` / `UNRESOLVED_REDUCED_COHORT` rather
than an unqualified `REPLICATED_DIRECTION`), and the eventual
full-151-recording HMC run remains an explicit open item for the controlled
Claude+Ismet integration (this deviation does not retire or supersede
Stage 1B's full-cohort design - it is a session-bandwidth-bounded pilot
under it).

## What would change this

If a future session has materially better bandwidth or more time, the full
151-recording (or a larger reduced-N) cohort should be run against the
same frozen `results/hmc_protocol_stage1b.json` design, and this pilot's
results retained as a smaller, earlier, disclosed data point rather than
silently discarded.
