# Statistical Reporting Audit — SD Convention (Master Review, Reviewer A)

**Finding:** every existing multi-seed standard-deviation figure in this
project (`ml/train_ppg_dalia_imu_multiseed.py`, `ml/train_ptt_ppg_site_ablation.py`)
was computed with `np.std()`'s default `ddof=0` (population standard
deviation). For n=5 independent training-seed samples, the conventional
choice when *estimating* variability from a small sample is the **sample
standard deviation** (`ddof=1`, Bessel's correction), which is
systematically larger by a factor of `sqrt(n/(n-1))` — for n=5, ≈1.118x.

## What was audited

`ml/audit_sd_convention.py` reads the raw per-seed values already stored
in the two frozen artifacts below and recomputes both conventions from
them — it does **not** modify either file:

- `results/ppg_dalia_imu_multiseed_replication.json`
- `results/ptt_ppg_site_ablation.json`

Output: `results/sd_convention_audit.json` (a new, separate, additive
artifact).

## Measured difference

| Metric | ddof=0 (as originally reported) | ddof=1 (recommended) |
|---|---|---|
| PPG-DaLiA Model A MAE SD | 0.2306 | 0.2578 |
| PPG-DaLiA Model B MAE SD | 0.1566 | 0.1751 |
| PPG-DaLiA Model C MAE SD | 0.2044 | 0.2286 |
| PTT Model A MAE SD | 1.0384 | 1.1610 |
| PTT Model B MAE SD | 0.4114 | 0.4599 |

The ratio is consistently ≈1.118 (=√(5/4)) across every figure, exactly as
expected for n=5. **No qualitative conclusion in either experiment changes**
— every seed-direction count, every mean effect size, and every
`replication_status`/`marginal_status` classification was based on the
mean and the seed-direction count, never on the SD value crossing a
significance threshold. This audit is a reporting-precision fix, not a
result reversal.

## Migration strategy (what was changed vs. preserved)

- **Preserved unchanged**: `results/ppg_dalia_imu_multiseed_replication.json`
  and `results/ptt_ppg_site_ablation.json` — their `sd` fields keep their
  original `ddof=0` values, exactly as reported at the time.
- **Added, not overwritten**: `results/sd_convention_audit.json` —
  ddof=0 and ddof=1 side by side, recomputed from the same raw per-seed
  numbers, with an assertion that the recomputed ddof=0 value matches the
  originally-stored value exactly (a correctness check on this audit
  itself).
- **New reporting convention going forward**: `ml/train_ppg_dalia_capacity_control.py`
  (this sprint's new experiment) reports **both** conventions directly in
  its own output, with sample SD (`ddof=1`) as the primary recommended
  figure. Any future multi-seed experiment script should do the same.

## What this audit explicitly does NOT do

- Does not fabricate a confidence interval or p-value — n=5 is too small
  for either to be meaningful, and none was computed before or after this
  audit.
- Does not re-run any inferential test merely because the SD figure
  changed.
- Does not alter any seed-direction count, mean effect, or
  evidence-strength classification in `results/sensor_marginal_value_contract.json`
  — those were never derived from the SD value.
