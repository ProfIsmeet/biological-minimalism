# Pareto Readiness — Day 6

## Decision

- Global Pareto ready: **NO**
- Target-specific Pareto ready: **NO**
- Structural descriptive assessment available: **YES**
- Formal Pareto authorized: **NO**

The decision rule exists, but the evidence matrix is incomplete and the two available marginal-value studies are not comparable ranking coordinates.

## Exact blockers

1. Scientific benefit is validated only for two heart-rate additions, from different datasets, populations, baselines, and model families.
2. Deployable average power/energy is absent for optical sensing, the scientifically compatible IMU rate, BioZ, EEG, and the second PPG site.
3. Component, PCB/module, and finished wearable masses are unquantified for all components.
4. ECG, thoracic BioZ, EEG, and leg BioZ electrode montages and sharing/allocation remain unresolved.
5. Final MCU, memory, radio, battery, regulator, enclosure, and attachment identities/allocations remain open.
6. HRV, respiration, BP/PAT, workload, fatigue, sleep/circadian, and fluid targets lack frozen project validation.

## Defensible limited conclusion

Within the frozen PTT heart-rate experiment only, the second PPG site worsened aggregate error while adding one physical and optical sensing site. This is a target- and experiment-specific structural observation. It does not authorize global sensor removal, a final architecture winner, or comparison with the PPG-DaLiA IMU benefit magnitude.

## Next evidence needed

Measure selected-hardware state power at the scientifically compatible rates; freeze duty schedules; weigh components, assembled modules, and finished wearables separately; resolve electrode/optical interfaces and shared resources; benchmark memory/workspace and latency on the selected embedded target; and run target-specific marginal/robustness experiments under predeclared protocols.

Machine-readable component-level readiness is in `results/pareto_readiness_day6.json`.
