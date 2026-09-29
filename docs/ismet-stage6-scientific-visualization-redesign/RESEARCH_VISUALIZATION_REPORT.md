# Research Visualization Report — Stage 6 Scientific Visualization Redesign

Covers Families E, F, G — `/system-brief` and `/research/experimental`.

## E — Architecture delta matrix (`ArchitectureDeltaMatrix.tsx`)

Replaces `ConditionalSelectionRadial`'s decorative SVG wedge diagram.
Rows: PPG, IMU, ECG, EEG, EOG (`FINAL_SENSOR_INVENTORY`). Columns:
modality, body region, MINIMAL_CORE membership, CORE_PLUS_CONTEXT
membership, delta, physiological role, incremental contacts, evidence
class. EOG is the sole "+ Added" delta, matching
`results/stage4_architecture_candidate_classes.json` exactly (MINIMAL_CORE
sensors: wrist PPG, wrist IMU, chest ECG, frontal EEG — EOG absent).
Both architectures remain presented as Pareto-relevant per the existing
`PARETO_RELEVANCE_LIMITATION` constant (reused, unmodified) — no claim of
a unique mathematical optimum is made anywhere in this component.

Burden figures (incremental contacts) are read live from the same
`api.getFinalWearableArchitecture()` call `ConditionalSelectionRadial`
already made — not a new network owner, not hardcoded. Static architecture
facts (membership, role, delta) do not depend on that live fetch resolving
— the table rows and membership columns render immediately from
`FINAL_SENSOR_INVENTORY`; only the burden-contacts cell shows "Not
available" until the live fetch resolves.

## F — Evidence/burden matrix (`CandidateDispositionMatrix.tsx`, enriched)

Rather than build a new component duplicating the already-real, real-data,
table-first `CandidateDispositionMatrix`, this family was satisfied by
adding two columns (numeric result & direction, population scope) sourced
from the bundled `table_d_negative_mixed_results.json` excerpt, joined by
candidate key. `wrist_temperature_light` — which has no governing
experiment (TIER_P_PENDING) — correctly shows "Not measured", never a
fabricated number or a 0. The pre-existing decorative
`ExperimentalDispositionOrbit` (rendering the identical
`exclusion_rationale` data as an SVG wedge diagram, immediately above this
same table) is unmounted.

**Negative evidence ≠ health fault:** the existing disposition badge
styling (`experimental` ochre color, not `jury-fault` red) is preserved
unchanged — this task did not touch that styling, avoiding any risk of
accidentally recoloring negative scientific evidence into a fault-red
presentation.

## G — Sensitivity/ablation small multiples (`SensitivitySmallMultiples.tsx`)

Four panels, one governing quantitative family each (never mixed units on
one axis — each `ChartFrame` wraps exactly one `SeriesPanel` with one
metric):

1. **PPG-DaLiA capacity-controlled IMU value** — MAE (bpm), lower-is-better,
   n=5 seeds, 3 series (A_cap/B/C).
2. **PTT per-subject heterogeneity** — delta MAE (bpm), lower-is-better,
   n=4 subjects. The sign-flip-on-s2-exclusion is rendered explicitly in
   the footer (`Aggregate WITH s2: ... (B_WORSE) · WITHOUT s2: ... (B_BETTER)`)
   — never concealed.
3. **Sleep-EDF primary A/B/C** — macro-F1, higher-is-better, n=5 seeds,
   n=3 test subjects, with the concentrated-in-one-subject caveat carried
   into the claim-boundary text.
4. **PPG-DaLiA per-subject/activity heterogeneity** — delta MAE (bpm),
   n=3 subjects.

Every panel: participant/seed-level dots (teal circles) + a sample-mean
diamond (ochre) — never an error-bar/whisker implying a confidence
interval the source data does not license. Uncertainty type explicitly
labeled per panel (`seed_sd` / `none`) via `uncertaintyLabel()`, matching
each source figure's own `uncertainty_meaning` field. Directionality
explicitly labeled via `directionalityLabel()`. Exact values available in
a semantic table beneath every panel, at parity with the plotted marks.

**Small-N discipline:** no panel implies population validation — every
summary sentence states the exact sample unit ("held-out subject (n=4)",
"training seed (n=5)"), matching the source artifacts' own `sample_unit`
fields verbatim.

## No historical/superseded result promoted

Every number in Families E/F/G traces to an entry `results/final_figure_manifest.json`
or `results/final_tables/*.json` marks as governing (see
`SCIENTIFIC_SOURCE_ADJUDICATION.md`). No older, individually-attractive
`results/*.json` file was read in place of its manifest-cited governing
export.
