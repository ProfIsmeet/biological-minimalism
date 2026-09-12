# Operational Cost Methodology v1

**Status:** Day 5 operational-cost contract. Pareto-ready on the cost side only. No Pareto frontier, dominance result, sensor ranking, or final architecture selection is produced here.

## 1. Purpose

This methodology represents what a candidate sensing component physically and operationally adds to the Biological Minimalism architecture. It keeps power, mass, physical contact, module complexity, compute, bandwidth, and observable burden proxies separate and provenance-bearing. Its purpose is to support a later multi-objective join with a reviewed scientific marginal-value contract—not to manufacture a single answer before both inputs are defensible.

## 2. Why there is no weighted cost score

Mill watts, grams, body contact regions, modules, latency, and electrode requirements are not naturally commensurable. A weighted sum would encode unreviewed value judgments about crew burden, energy, reliability, and performance. Version 1 therefore provides no weights, normalization, cost score, utility score, or ranking. A later approved method may analyze non-dominated configurations while retaining the original dimensions and units.

## 3. Component taxonomy

The stable `component_id` names a candidate sensing addition, not a procurement choice. Each component separately records:

- sensing modality and channels;
- physical sensing site;
- body contact region implications;
- physical module context;
- experimental sensor identity, if a dataset established it;
- candidate final hardware identity, which remains null until selected;
- wearable versus cabin-context category;
- linked scientific experiment IDs.

The initial scientifically mapped IDs are `wrist_imu` and `second_ppg_site`. Placeholders—`wrist_ppg`, `ecg_chest`, `thoracic_bioz`, `skin_temperature`, `light_sensor`, `frontal_eeg`, and `leg_bioz`—reserve vocabulary without assigning scientific value or hardware costs.

## 4. Physical module versus modality

A modality is not automatically a module. PPG, IMU, and temperature may share a wrist enclosure, power source, MCU, and radio. ECG and thoracic BioZ may share parts of a chest module or electrode arrangement. Conversely, one modality can require multiple physical sites. The catalog therefore never derives module count from modality count.

## 5. Marginal versus total cost

Every quantity declares a `basis` of `marginal` or `total`. Marginal cost is defined relative to an explicit baseline integration context. For `wrist_imu`, the reference context is an already-existing wrist PPG module; adding the colocated accelerometer adds no body contact region, sensing site, electrode, or independent module in that context. This does not say a standalone IMU wearable is free. For `second_ppg_site`, one additional physical optical site is structurally known, while module and body-region counts remain unresolved.

## 6. Power

Power may eventually include acquisition, analog front end, interface, and attributable processing. A value must identify operating mode, duty cycle, component identity, whether it is typical or maximum, and whether supporting electronics are included. The final components and duty cycles are not frozen, so Day 5 leaves hardware power null. Dataset acquisition-system power is not substituted for candidate wearable power.

## 7. Mass

Mass distinguishes bare component, assembled sensing submodule, and finished wearable increment including PCB, interconnect, enclosure, attachment, and allocated battery. No final hardware is selected, so Day 5 leaves mass null rather than presenting IC mass as finished-module mass.

## 8. Contact-region burden

The catalog distinguishes:

- body contact regions;
- physical sensing sites inside a region;
- electrodes, optical contacts, or adhesive surfaces;
- continuous versus intermittent contact.

`wrist_imu` uses the existing wrist contact region under the reference colocation assumption. `second_ppg_site` adds one physical/optical sensing site, but whether that constitutes a new body region depends on the final mechanical architecture and remains unknown.

## 9. Module count

`additional_module_count` is a structural marginal quantity, independent of modality count. It is zero for the colocated wrist-IMU reference context. It is unknown for the second PPG site because the site might share electronics and enclosure or require a separate assembly. Total configuration module count is deferred until a configuration and module boundary are frozen.

## 10. Contact and electrode count

Counts may include electrodes, optical contact sites, emitters, photodiodes, adhesive surfaces, and cables when the architecture supports an exact statement. They are not converted into discomfort. The current PTT comparison establishes one additional optical contact site, but it does not freeze exact emitters, detector count, electrode count, attachment, or wiring.

## 11. Compute

Software-side quantities can be exact when committed code/artifacts support them. Day 5 records:

- PPG-DaLiA Model A: 8,065 parameters;
- PPG-DaLiA Model B: 29,089 parameters; marginal increase 21,024;
- PTT Model A: 8,289 parameters;
- PTT Model B: 8,625 parameters; marginal increase 336;
- per-window scalar input values for each added component.

These are deterministic research-model properties. They are not desktop power measurements, embedded memory guarantees, runtime feasibility claims, or inference latency. Latency stays null because no controlled paired benchmark was frozen.

## 12. Bandwidth and data rate

When native sample rates and channel counts are frozen, raw scalar sample throughput is derived as:

`sample rate × scalar channel count`.

The wrist IMU adds `32 Hz × 3 = 96 scalar samples/s`. The second PPG site adds `500 Hz × 3 = 1,500 scalar samples/s`. Per 8-second model window, these are 768 and 12,000 added scalar values respectively. These figures exclude bit depth, framing, timestamps, compression, retransmission, and protocol overhead. Because a future ADC/storage bit depth is not frozen, bit rate remains null.

## 13. Operational mode and duty cycle

The schema supports continuous, periodic, intermittent, event-driven, and unresolved operation. Dataset recordings do not freeze future wearable schedules. Both current entries therefore use `unresolved` and preserve duty-cycle percentage as null. A future daily energy value must not be calculated until both operating power and duty cycle are supported.

## 14. Comfort and burden proxy policy

No numerical comfort score is permitted without validated human evidence. The catalog uses observable proxies instead: contact regions, physical sites, electrodes/optical contacts, adhesive or head-worn requirements, additional modules, cables/links, and continuous/intermittent wear. These proxies remain separate and are not silently weighted.

## 15. Provenance and evidence levels

Every known number cites one or more evidence records. Evidence levels are:

- `measured`: measured by the project under a documented condition;
- `manufacturer_spec`: an official component specification;
- `literature_estimate`: peer-reviewed or authoritative literature;
- `derived`: deterministic calculation from cited known values;
- `architectural_count`: a direct structural count under an explicit context;
- `unknown`: no defensible value.

Each evidence record stores the source reference, artifact/component identity, operating condition, value characterization, version/date, and assumptions. Day 5 uses only committed project artifacts and explicit architectural contexts; it does not nominate representative ICs as final hardware.

## 16. Shared-hardware accounting

Each component has a `shared_hardware` record naming a shared module where appropriate, stating the integration context, allocation status, and double-counting risk. `naive_addition_allowed` is false for every current entry. A later configuration total must allocate shared enclosure, battery, MCU, radio, AFE, electrodes, and interconnect exactly once. If allocation cannot be supported, the total remains non-additive or unknown.

## 17. Unknown and null policy

Unknown means unavailable—not zero. An unknown quantity contains no `value`, `minimum`, `typical`, or `maximum`, uses evidence level `unknown`, and cites no numerical provenance. API and UI validation preserve this invariant. Zero is allowed only as a known structural count with architectural provenance, such as zero additional contact regions for the colocated wrist-IMU reference context.

## 18. Cross-component comparability

Only quantities with the same meaning, basis, unit, operating condition, and inclusion boundary are directly comparable. Research-sensor properties are not candidate-hardware costs. Marginal and total quantities are not mixed. Component-level power is not compared with finished-module power without an explicit boundary. Ranges are engineering ranges, not confidence intervals, and are not converted to point estimates.

## 19. Future Pareto integration

The future join key is `component_id`. The reviewed scientific contract is expected to provide target, experiment ID, benefit metrics, direction, provenance, and claim boundaries. The operational side supplies preserved cost dimensions. Only after both contracts are reviewed and frozen may a separate process construct multi-objective rows and test non-dominance. Until then `scientific_benefit` remains null and the system produces no frontier, dominance, rank, or keep/remove recommendation.

## 20. Current limitations

- Exact final sensor, AFE, MCU, battery, radio, enclosure, electrodes, and optical components are not frozen.
- Hardware power, mass, duty cycle, embedded latency, embedded memory, and protocol bit rate remain unknown.
- Architectural zero counts apply only to their stated integration baselines.
- Dataset devices establish experimental identity, not candidate wearable cost.
- No validated comfort study or hardware reliability probability is available.
- Phase 5 fault results are not converted into hardware failure probabilities.
- The scientific marginal-value contract from Ismet Day 5 is not yet integrated, so no benefit/cost join or Pareto analysis is performed.
