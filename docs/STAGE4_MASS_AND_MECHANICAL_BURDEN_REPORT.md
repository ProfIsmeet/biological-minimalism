# Stage 4 Mass and Mechanical Burden Report

Source of truth: `results/stage4_engineering_readiness.json` (`mass` block).
Extends `results/reference_mass_readiness_day11_part2.json`, which left every
module at **Tier0** (unknown — component package dimensions known for several
parts, but package mass not published, no PCB/battery/enclosure/electrode
selection). This report advances the wrist, chest, and head modules to
**Tier2** (electronics-subassembly estimate) using generic engineering
allowances. **No vendor mass data and no measurement exist anywhere in this
report — Tier3/Tier4 are not claimed.**

## Tier achieved and evidence class

All new mass numbers are `ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE` —
generic small-IC/PCB/enclosure/strap allowances, not vendor-published part
mass and not a CAD/mechanical-design estimate. Per the Day-11 Part-2 tier
definitions:

- **Tier0** — unknown (previous state, all modules)
- **Tier1** — component/package-only known (not claimed here — no vendor
  package mass data was used)
- **Tier2** — electronics-subassembly estimate ← **this report's level**
- **Tier3** — reference module mechanical estimate (requires CAD/geometry — NOT_READY)
- **Tier4** — prototype measured mass (NOT_READY)

## Body-region / module mass breakdown

| Module | Component ICs | PCB | Battery | Enclosure | Attachment | Wiring | **Module total** |
|---|---|---|---|---|---|---|---|
| Wrist (`wrist_module`) | 0.040 g (4 ICs × 10 mg) | 0.6 g | 0.293 g | 3.0 g | 4.0 g (elastomer strap) | 0.2 g | **8.133 g** |
| Chest (`chest_module`) | 0.020 g (2 ICs) | 0.8 g | 0.293 g | 2.0 g | 3.0 g (adhesive patch set) | 0.8 g | **6.913 g** |
| Head (`head_module`) | 0.010 g (1 IC) | 0.7 g | 0.293 g | 2.5 g | 3.5 g (headband + peri-ocular ext.) | 0.6 g | **7.603 g** |
| Leg (`leg_module`, EXPERIMENTAL) | 0.010 g (1 IC) | 0.5 g | 0.293 g | 1.5 g | 3.0 g (strap) | 0.5 g | 5.803 g — **excluded from system total** (rule 47) |

Battery reference: 150 mAh / 3.7 V Li-Po class (0.555 Wh), 190 Wh/kg reference
energy density → **0.293 g per module instance**. This is a per-module battery
assumption (each module carries its own reference cell) because the module
boundary question (shared hub vs. standalone per-module electronics) remains
open, per Day-11 Part-2's own `optical_site_evaluation_branch` note — this
report does not resolve that boundary, it characterizes mass under the
conservative "each module is self-powered" assumption.

## Contact / electrode burden (preserved from Day-11 Part-2, unchanged)

- ECG: 2-channel montage (count/materials still OPEN beyond the frozen 2-ch AFE point).
- EEG: montage count still OPEN; only the +2 EOG increment is defensible.
- **EOG incremental mass: 0.4 g** (`ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE`) — 2 ocular
  electrodes (0.15 g each) + 2 leads (0.05 g each) **only**. Shares the head
  module's AFE, battery, and enclosure entirely — this is the *entire*
  incremental mass EOG adds (rule 66: shared-resource credit made explicit).
- Thoracic/leg BioZ: electrode count/material remain MISSING (same as Day-11 Part-2; not advanced by this report).

## System mass — PARTIAL

**System mass, base topology excluding leg module: 30.533 g** (wrist 8.133 g +
chest 6.913 g + head 7.603 g — sum, minor rounding at the artifact's 3-decimal
precision; leg module characterized at 5.803 g but excluded from every system
total, rule 47).

**Status: `PARTIAL`**, not `READY` — because:
- every contributing figure is a generic engineering allowance, not a vendor
  or measured value (no Tier3/Tier4 evidence anywhere);
- inter-module wiring harness beyond the per-module allowance is not modeled;
- the `optical_site_evaluation_branch` module boundary (shared/tethered/standalone)
  remains OPEN, so its mass is not included in any total;
- manufacturing tolerance/process mass and adhesive/gel consumables beyond
  the modeled patch allowance are not included.

## Unresolved mechanical items

- CAD-level PCB area/stackup for any module (would be required for Tier3).
- Vendor package mass for any of the 9 stable-component-ID sensing ICs (would be required for Tier1/Tier2 upgrade to vendor-sourced).
- Final electrode materials/adhesive chemistry for ECG/EEG/BioZ.
- Whether the system uses one shared battery/hub or per-module batteries (this report assumed the latter, conservatively).
- Leg-module and second-PPG-site inclusion decision (both remain explicitly excluded pending architecture selection).
