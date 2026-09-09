# Sleep V2 Corrected Interaction (EEG × EOG × Resp) — Real Results

Trainer: `ml/train_sleep_edf_interaction_resp_seedfix_v2.py` (Claude-
authored, cherry-picked, independently audited before running). Result:
`results/sleep_edf_interaction_resp_seedfix_v2.json`. 5 real seeds
(42-46), corrected H1 seeding order throughout.

## M0/M_A equivalence — independently verified, not just trusted

M0 and M_A are the existing corrected V2 A/B checkpoints
(`results/sleep_edf_primary_seedfix_v2.json`), reused rather than
retrained. This sprint independently verified the equivalence claim by
directly comparing source files (`ml/tests/test_stage2_sleep_c_and_interaction_transferred.py::
test_m0_ma_equivalence_independently_verified_same_hyperparameters`):
the original Day-10 interaction script and the corrected V2 primary script
both use the identical `SleepStageClassifier` class,
`EPOCHS=20/BATCH_SIZE=64/LR=0.001/EMBEDDING_DIM=32` hyperparameters, and
the same frozen primary subject split — the only axis of variation is the
H1 seeding-order fix, which V2 already corrects. **Accepted.**

## Capacity-fairness safeguard — passed

The trainer aborts with a `RuntimeError` if the per-channel parameter cost
is not constant across M0→M_A, M0→M_B, M_B→M_AB. It did not abort — the
constant per-channel cost was verified as **112 parameters**, confirming
M_B and M_AB are not confounded by uneven capacity scaling.

## Resp provenance — correctly carried, not regressed

`resp_rate_provenance` in the result: native 1 Hz, 100 Hz common/model
grid via FFT-based upsampling — explicitly NOT described as "native 100
Hz," per the H2 correction.

## Exact results (macro-F1, 5 seeds)

| Model | Mean | SD (ddof=1) |
|---|---|---|
| M0 (EEG only) | 0.7365 | 0.0279 |
| M_A (EEG+EOG) | 0.7647 | 0.0116 |
| M_B (EEG+Resp) | 0.7425 | 0.0199 |
| M_AB (EEG+EOG+Resp) | 0.7630 | 0.0255 |

| Benefit (vs M0) | Mean | SD (ddof=1) |
|---|---|---|
| A (EOG) | +0.0282 | 0.0308 |
| B (Resp) | +0.0061 | 0.0162 |
| AB (EOG+Resp) | +0.0265 | 0.0162 |

**Interaction term** (`M_AB − M_A − M_B + M0`): mean **−0.0078**, SD
0.0363, **3/5 seeds positive, 2/5 negative**.

## Stability classification (frozen rule, not chosen post hoc)

`approximately_additive_or_unresolved` — `|mean| = 0.0078` is well below
`0.5 × SD = 0.0182`, so the frozen classification rule places this result
in the "unresolved" bucket rather than forcing a super- or sub-additive
label. This is the honest, real outcome of the frozen formula — not
adjusted or reinterpreted to produce a cleaner story.

## Interpretation

Resp alone (Benefit B, +0.0061) is small and much weaker than EOG alone
(Benefit A, +0.0282) — consistent with H2's disclosed hypothesis that
Resp's 1 Hz native bandwidth limits its standalone information content.
Adding Resp on top of EOG (Benefit AB, +0.0265) is essentially the same as
EOG alone, suggesting Resp contributes little additional information once
EOG is already present — but with only 5 seeds and a genuinely mixed-sign
interaction term (3 positive, 2 negative), this project does **not** claim
a resolved synergy or redundancy relationship. The honest, frozen-rule
conclusion is `approximately_additive_or_unresolved`.

## Historical (V1) comparison — kept separate

`results/sleep_edf_interaction_resp_day10.json` (V1, mixes the original
buggy-seed-order M0/M_A with V1's own M_B/M_AB) remains completely
unchanged. No V1/V2 mixing occurred in this document or its underlying
result.
