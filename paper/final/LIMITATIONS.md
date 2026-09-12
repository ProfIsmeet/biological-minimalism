# Limitations

Explicit, per master prompt Part 31. Every item cites its governing
`claim_id` or artifact — this list must not be softened in paper/jury text.

1. **Terrestrial datasets only.** No governing result uses spaceflight or microgravity data. `[claim_id: astronaut_microgravity_applicability]`
2. **Small held-out biological cohorts in some experiments.** E.g. PPG-DaLiA capacity control n=15 (3 held-out test subjects per seed group); second-site PPG n=4 held-out; thoracic EIS n=12/16 eligible. See `results/final_tables/table_a_modality_evidence.json` for exact n per experiment.
3. **Incomplete HMC full-cohort replication.** Only a bounded n=7 diagnostic exists against a 151-subject cohort (59 downloaded, 52 SHA-verified); full-cohort training is a compute/time-budget-limited item, lower priority, not run. `[claim_id: hmc]`
4. **Incomplete ds003838 full-cohort experiment.** Only a bounded n=3 diagnostic exists; the full cohort requires ~93GB / ~9.4h additional download, not attempted. `[claim_id: ds003838]`
5. **Bounded engineering assumptions.** Power/mass/data-rate/contact figures are component-datasheet or class-level estimates (Tier 0-2), not measured or vendor-sourced; no target operating duration exists in the project; module-level total mass beyond battery cells is `SYSTEM_MASS_NOT_READY`. `[claim_id: engineering_burden]`
6. **Digital Twin unvalidated longitudinally.** The Digital Twin is an untrained, unvalidated architecture proposal — no trained checkpoint, no validated multi-target performance, no runtime/energy/latency measurement. `[claim_id: digital_twin]`
7. **Architecture conditionality.** EOG inclusion and sparse-EEG channel count are both frozen `FREEZE_CONDITIONALLY` under Gate E, with explicit predefined revision triggers tied to pending HMC/ds003838 full-cohort results — not an unconditional final decision. `[claim_id: final_architecture]`
8. **No unique mathematical Pareto winner.** MINIMAL_CORE remains Pareto-relevant alongside CORE_PLUS_CONTEXT; the selection is a documented Coordinator judgment call, not a proof of optimality. `[claim_id: pareto]`
9. **GalaxyPPG data-quality correction.** An earlier GalaxyPPG analysis was invalidated by a reference-ECG signal-quality defect affecting 6/24 subjects; only the corrected 18-subject analysis is current governing evidence — any external citation of the earlier numbers is stale. `[claim_id: galaxy_replication]`
10. **Reproducibility is not uniform across experiments.** Some results are checkpoint-reproducible from an archived, SHA256-verified checkpoint; others require an external dataset download not committed to the repo; none currently fall in a "historically unverifiable / missing bytes" state, but that class is explicitly defined and tracked. See `results/final_reproduction_manifest.json`.
