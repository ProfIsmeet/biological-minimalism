# LBNP Thoracic EIS — Real Results (Stage 3, Priority 2)

**Status: `COMPLETE_NEGATIVE`.** Trainer: `ml/train_lbnp_thoracic_eis.py`.
Result: `results/lbnp_thoracic_eis_stage3.json`. Loader:
`ml/datasets/lbnp_impedance.py`.

## Real eligibility finding (this sprint)

Only **12 of 16** subjects have valid (non-NaN) pleth data — a real,
predeclared data-quality exclusion, found by direct inspection of
`raw_labchart_data.mat` (subjects at struct indices 0–3 have `pleth`
entirely NaN; indices 4–15 have complete real pleth). This is a genuine
reduction from the paper/metadata-reported n=16 to a smaller,
actual-file-verified usable cohort of **n=12** — the third real cohort-size
correction this project has made after such actual-file audits (QDE,
ds003838, and now LBNP).

Native rate confirmed this sprint: ECG/pleth/MAP are natively **1000 Hz**
(derived from `ts`'s real inter-sample delta, previously unverified per
Stage 1B's own audit).

## Frozen A/B/C

- **A**: ECG + pleth simple time/frequency features (10-dim).
- **B**: A + real thoracic EIS (log-magnitude + phase at all 100 real
  frequencies, 200-dim additional).
- **C**: B-dimensional, EIS-stage correspondence deranged within subject.

Target: real LBNP pressure stage (mmHg), step-function looked up at each
real EIS spectrum's own timestamp (confirmed timebase-compatible with the
ECG/pleth recording in the prior sprint). Metric: MAE (mmHg), LOSO (n=12).

## Exact results (subject-macro MAE, mmHg)

| Condition | Mean MAE |
|---|---|
| A (ECG+pleth) | 27.62 |
| B (+thoracic EIS) | 29.86 |
| C (+deranged EIS) | 29.83 |

**A−B = −2.24** (B is worse; only **3/12 subjects favor B over A**).
**C−B = −0.033** (B and C are essentially identical — the model performs
the same whether the EIS spectrum is correctly aligned or temporally
deranged; **6/12 favor B over C**, essentially a coin flip).

## Per-subject sensitivity (real, disclosed in full)

| Subject (0-based idx) | A−B | C−B |
|---|---|---|
| 4 | **+43.31** | +36.73 |
| 5 | −0.70 | +0.09 |
| 6 | −2.34 | +2.37 |
| 7 | **−36.46** | −25.95 |
| 8 | −8.97 | −2.25 |
| 9 | −1.36 | −1.20 |
| 10 | +1.92 | +1.36 |
| 11 | −14.41 | −10.89 |
| 12 | −1.72 | +0.10 |
| 13 | +0.20 | +3.27 |
| 14 | −3.12 | −0.70 |
| 15 | −3.20 | −3.35 |

**Subjects 4 and 7 are extreme, opposite-direction outliers** (+43.3 and
−36.5 respectively) — roughly canceling in the aggregate mean, which masks
a genuinely bimodal, highly heterogeneous population rather than a
uniformly mild negative effect. This is disclosed explicitly, not averaged
away.

## Interpretation — real, clear negative result

Thoracic EIS did not add information beyond ECG+pleth for LBNP-stage
estimation in this cohort, under this frozen protocol. The fact that B and
C perform nearly identically is itself informative: it suggests that
whatever the ridge model extracts from the 200 EIS-derived features is not
meaningfully dependent on the EIS spectrum's true temporal alignment to
the stage — consistent with (though not proof of) the EIS features simply
adding capacity/noise rather than real stage-discriminative information at
this small n and with this simple feature representation.

Per the frozen protocol's negative-result policy, this is retained in
full, not reframed, not fixed by trying alternative frequency-band
selections after seeing this outcome, and not used to justify excluding
any subject.

## Safe claim

"Under a real, frozen LOSO protocol (n=12, the actual-file-verified usable
cohort), thoracic EIS did not add predictive information about LBNP-stage
beyond ECG+pleth alone — a real negative result for this specific
sensor/target/protocol combination."

## Unsafe claims (not made)

"Thoracic EIS is useless for hypovolemic-stress monitoring in general."
"This proves central hypovolemia cannot be detected via impedance." Any
microgravity/astronaut/spaceflight equivalence (this is a terrestrial LBNP
protocol). Any claim about the abdominal or arm EIS sites (out of scope,
not tested).
