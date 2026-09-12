# Sleep-EDF V1/V2 Citation Mapping (Stage 1A, Day 12)

Purpose: tell Furkan (paper) and jury-prep exactly which Sleep-EDF Primary
A/B number to cite going forward, without having to reconstruct the H1
remediation history. See `docs/CLAUDE_H1_H2_SCIENTIFIC_REMEDIATION_HANDOFF.md`
and `results/sleep_scientific_remediation_day12.json` for the full technical
account; this file is the short citation-facing summary.

## Rule of thumb

**Cite V2 (corrected) for Primary A/B.** Cite V1 (historical) only when
explicitly discussing reproducibility history or the H1 remediation itself.
**Never mix a V2 number with a V1 number in the same delta or ratio** — see
"Forbidden combinations" below.

## Mapping table

| Quantity | Historical V1 | Corrected V2 | Current status |
|---|---|---|---|
| Primary A (EEG-only) mean macro-F1 | 0.7473 | 0.7365 | **Cite V2** |
| Primary B (EEG+EOG) mean macro-F1 | 0.7693 | 0.7647 | **Cite V2** |
| B − A (mean) | +0.0220 | +0.0282 | **Cite V2** |
| Favorable seeds (B > A) | 4/5 | 4/5 | Same under both |
| SC4011 subject delta (dominant) | +0.0489 | +0.0838 | **Cite V2**; dominance pattern preserved |
| SC4081 subject delta | +0.0080 | +0.0045 | **Cite V2**; small under both |
| SC4131 subject delta | +0.0091 | +0.0009 | **Cite V2**; small under both |
| Shuffled-EOG control C (B vs C) | 5/5 seeds favor B (historical protocol) | — | `PENDING_SEEDFIX_V2_FOLLOWUP` — cite V1, labeled historical |
| Interaction M_B / M_AB | approximately_additive_or_unresolved (historical protocol) | — | `PENDING_SEEDFIX_V2_FOLLOWUP` — cite V1, labeled historical |
| Secondary holdout (n=8, A→B) | 5/5 seeds, zero retraining | — | Historical protocol only; not yet seed-corrected. Cite as historical/secondary, do not imply it is V2. |
| Checkpoints (Primary A/B) | 10 historical, externally archived | 10 new `seedfix_v2`, **local only, not externally archived** | Both exist; do not report "70 externally archived" |
| Resp native sample rate | (previously misstated as 100 Hz) | 1 Hz (H2, metadata-only) | **Always cite 1 Hz native**; 100 Hz is the resampled training-grid rate, not native bandwidth |

## Forbidden combinations

Do **not** construct or cite any of the following — they mix two different
seeding protocols and are scientifically invalid, not merely inconvenient:

- "Corrected B minus historical C" (V2 B − V1 C).
- "Corrected interaction" using V2 A/B legs with V1 M_B/M_AB legs.
- "70 checkpoints, all externally archived" (60 historical is; the 10 V2
  checkpoints are local-only this sprint — see
  `results/checkpoint_inventory_post_remediation_stage1a.json`).
- "The full Sleep A/B/C experiment has been rerun under the corrected seed
  protocol" (only A/B was).
- "All Sleep checkpoints are seed-controlled reproducible" (only the 10 new
  `seedfix_v2` ones are; the historical checkpoints predate the corrected
  protocol).

## Suggested paper/jury sentence (safe, exact values from the artifact)

> Under the corrected seed-before-model-initialization protocol, EEG+aligned
> EOG improved primary-cohort mean macro-F1 relative to EEG-only from
> approximately 0.7365 to 0.7647 (+0.0282), with B outperforming A in 4/5
> corrected runs. The effect is heterogeneous across subjects (SC4011
> dominant), consistent with the historical (pre-correction) result. A
> corrected shuffled-EOG control and corrected interaction estimate remain
> pending follow-up; the historical shuffled-EOG control and interaction
> result remain available as historical evidence only.

## Machine-readable source

`backend/app/research/catalog.py::_build_sleep_v1_v2_comparisons` and
`_build_sleep_v1_v2_version_state_breakdown` implement this table in code —
the `/research` API's `sleep-edf-eeg-eog-ablation` experiment exposes it as
`marginal_result.controlled_comparisons` (roles `SEED_CORRECTED_PREFERRED_V2`,
`HISTORICAL_PRE_SEEDFIX_V1_RESULT`, `SEED_CORRECTION_PENDING_FOLLOWUP`) and
the `sleep_v1_v2_version_state` breakdown.
