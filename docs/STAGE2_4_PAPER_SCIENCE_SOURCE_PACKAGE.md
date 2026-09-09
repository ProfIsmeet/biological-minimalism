# Stage 2-4 Paper-Safe Scientific Source Package

For Furkan/Claude's paper integration — Methods/Results facts and
table-ready numbers only. Not the paper itself; Claude integrates.

## Methods additions this sprint

- Sleep V2 corrected shuffled-EOG control (C): H1-corrected seeding,
  isolated `control_shuffle_seed` (run_seed+200,000), capacity-identical to
  B (verified assertion).
- Sleep V2 corrected interaction: frozen formula
  `M_AB − M_A − M_B + M0`, M0/M_A reused from corrected A/B (equivalence
  independently verified via source comparison), capacity-fairness
  safeguard (constant 112-parameter per-channel cost, verified not
  asserted-only).
- HMC bounded n=7 diagnostic: same architecture/protocol as Sleep-EDF A/B/C,
  applied to a 7-recording subset of the full 151-recording frozen cohort.

## Results — table-ready numbers

**Sleep V2 (5 seeds each, macro-F1):**

| | A | B | C |
|---|---|---|---|
| Mean | 0.7365 | 0.7647 | 0.7324 |
| SD (ddof=1) | 0.0279 | 0.0116 | 0.0472 |

B−A = +0.0282 (4/5). B−C = +0.0323 (4/5). A−C = −0.0041 (3/5 favor C, ≈0).

**Sleep V2 interaction (5 seeds each, macro-F1):**

| | M0 | M_A | M_B | M_AB |
|---|---|---|---|---|
| Mean | 0.7365 | 0.7647 | 0.7425 | 0.7630 |

Interaction term mean = −0.0078 (SD 0.0363), classification
`approximately_additive_or_unresolved`.

**HMC bounded n=7 (5 seeds each, macro-F1):**

| | A | B | C |
|---|---|---|---|
| Mean | 0.4562 | 0.4249 | 0.4169 |

B−A = −0.0313 (2/5 favor B, negative-leaning).

## Negative results (report in full, not summarized away)

- QDE V2: aggregate B worse than A, single-subject-dominated (subject 2).
- HMC bounded n=7: B worse than A (bounded, non-canonical scale).
- Sleep V2 interaction: genuinely mixed sign (3 positive / 2 negative seeds).

## Limitations (carry into the paper's limitations section)

- HMC full-151-cohort replication blocked by an external PhysioNet TLS
  certificate expiry — not yet resolved as of this sprint.
- GalaxyPPG/LBNP: access resolved, structure verified, no training result
  yet exists for either.
- ds003838: n=3 bounded diagnostic only.
- All new experiments remain single-dataset (Sleep V2) or bounded-n
  (HMC/ds003838) — no claim of broad external validation.

## Dataset lineage (unchanged from Stage 1B, referenced here for convenience)

See `results/dataset_lineage_stage1b.json`.

## Terrestrial/spaceflight boundary

None of this sprint's real results (Sleep V2 C/interaction, HMC bounded
n=7, GalaxyPPG/LBNP structure) involve spaceflight or microgravity data.
