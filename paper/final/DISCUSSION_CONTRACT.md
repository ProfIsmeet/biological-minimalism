# Discussion Contract

## Heterogeneous modality value

No included modality showed uniform benefit across all subjects. Wrist IMU's
GalaxyPPG benefit is real in aggregate but 6/18 participants disfavor it;
EOG's sleep-staging benefit gains strongly on REM but regresses on N3 in the
secondary cohort. Reporting these distributions, not just aggregates, is
part of the claim, not a caveat appended afterward. `[claim_id: ppg_plus_imu, galaxy_replication, eog_incremental_value]`

## Evidence-driven architecture selection, not a target count

CORE_PLUS_CONTEXT was reached by testing each candidate modality against a
capacity-matched, temporally-aligned baseline on held-out subjects, then
weighing the resulting evidence against physical burden via a formal Pareto
analysis — not by deciding on "four sensors" in advance and finding
justification after the fact. `[claim_id: sensor_minimalism_framing, final_architecture, pareto]`

## The value of negative evidence

Second-site PPG, leg BioZ, and thoracic EIS all failed to show a stable
aggregate benefit. Reporting these results is what makes the positive
results credible: a project that only ever reports positive findings cannot
be distinguished from one that never tested anything rigorously.
`[claim_id: second_site_ppg, leg_bioz, thoracic_eis]`

## Terrestrial limitation

Every governing dataset in this project is terrestrial. LBNP is a
protocol-analog for hypovolemic stress, not a spaceflight or microgravity
experiment. Terrestrial evidence, physiological plausibility, and
spaceflight validation are kept as separate tiers throughout this project
and are never collapsed into one another. `[claim_id: astronaut_microgravity_applicability]`

## Pending HMC / ds003838

Both remain lower-priority external work, explicitly not required for this
release. Their absence is disclosed, not concealed, and both feed
predefined Gate E revision triggers rather than being silently deferred.
`[claim_id: hmc, ds003838]`

## Conditional architecture freeze

Gate D (engineering burden) is CONDITIONALLY_READY, accepted by the
Coordinator as bounded uncertainty rather than resolved to exact figures.
Gate E freezes EOG inclusion and sparse-EEG channel count CONDITIONALLY,
each with an explicit, predefined revision trigger tied to the pending
full-cohort results above. `[claim_id: final_architecture, engineering_burden]`

## Future spaceflight validation requirement

Terrestrial evidence and bounded engineering estimates are a necessary but
explicitly insufficient basis for a flight-qualified system. Spaceflight
validation, vendor-sourced BOM finalization, and full-cohort external
replication are required before any claim of flight readiness.
`[claim_id: astronaut_microgravity_applicability, engineering_burden]`
