# LBNP Impedance Protocol (Stage 1B)

**Classification: GO_WITH_LIMITATIONS**

Full machine-readable facts: `results/lbnp_actual_file_audit_stage1b.json`,
`results/lbnp_protocol_stage1b.json`.

## Scientific purpose

Does thoracic electrical impedance spectroscopy add information about
progressive central hypovolemic stress beyond ECG + pleth, using an
externally-controlled LBNP chamber protocol?

## Public/paper cohort reconciliation

18 subjects enrolled; **16 with complete usable data** (2 excluded for
impedance instrumentation issues, per the paper). This project's eligibility
table uses **16**, not the paper's 18-subject enrollment figure, per the
explicit instruction not to silently borrow the larger number. Zenodo raw
file access was blocked this sprint (network egress timeout) — whether the
public release contains exactly 16 or 18 subjects' files is flagged as a
mandatory first Stage-2 check.

## LBNP levels — corrected from the master prompt's example

Actual verified stages: **0, 15, 30, 45, 60, 70, 80, 90, 100 mmHg** (not
just 0/15/30/45/60 as the prompt's placeholder suggested) — each held ~5
minutes with ~48s transitions. Analysis focus: 0–60 mmHg (clinically occult
range), matching the source paper.

## Critical EIS semantics

100 logarithmically-spaced frequencies, 100 Hz–1 MHz, is the **excitation
frequency axis**, not a sampling rate. Spectra are acquired roughly **once
per minute per site** — a per-stage snapshot (~5 spectra per ~5-minute
stage), not a continuous waveform. Frozen representation: full spectrum,
thoracic site only.

## Major leakage threat: protocol time

LBNP pressure increases monotonically, so elapsed time/sequence
index/timestamp could trivially encode the stage. A frozen feature-cleaning
barrier excludes these fields from the model input, enforced by an
automated test. This does **not** remove the real physiological co-variation
with the protocol — that covariation is the phenomenon under study — only
the non-physiological metadata shortcut is excluded.

## Frozen A/B/C

- **A**: ECG + pleth.
- **B**: A + thoracic EIS (full spectrum).
- **C**: B architecture, EIS stage correspondence deranged within subject.

## Target representation: ordinal MAE (mmHg), not F1

Chosen because LBNP stages are a genuinely ordered progression — macro-F1
would treat a 0-vs-60 mmHg confusion the same as a 45-vs-60 mmHg confusion.

## Secondary target: MAP

Usable only as a separately preregistered secondary analysis, with MAP
removed from inputs and LBNP-stage then also excluded from that secondary
run's inputs — never merged into the primary headline result.

## Claim limits

Even a positive result never establishes hemorrhage-volume estimation,
dehydration liters, microgravity fluid shift, clinical diagnosis, or
astronaut validation — see
`docs/STAGE1B_EXPANSION_FORBIDDEN_CLAIMS.md`.
