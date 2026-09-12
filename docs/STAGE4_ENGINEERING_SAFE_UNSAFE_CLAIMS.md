# Stage 4 Engineering Safe/Unsafe Claim Ledger

Governs how the Stage-4 engineering artifacts (`results/stage4_engineering_readiness.json`
and the four reports in this directory) may and may not be cited in the paper,
jury materials, or any dashboard copy.

## Safe claims

- "The base-topology reference system's engineering-assumption average power
  is approximately 7.2 mW (battery-side), under an explicit set of stated
  operating and duty-cycle assumptions — not a measured or guaranteed figure."
- "PPG LED average power is modeled separately from AFE floor power; combined,
  the wrist module's reference power is ≈0.79 mW under the stated LED scenario."
- "The base-topology reference mass estimate (wrist + chest + head modules) is
  approximately 30.5 g, using generic electronics-subassembly mass allowances
  — not vendor-sourced or measured mass (Tier2, not Tier3/Tier4)."
- "The base-topology raw data rate is approximately 19.6 kbps, explicitly
  excluding the deprioritized second-PPG-site branch (28.5 kbps) and the
  experimental leg-BioZ branch."
- "MCU, radio, regulator, and battery are reference-class selections
  (`REFERENCE_SELECTED`, `final=false`) with attached engineering-assumption
  operating points — not final, vendor-approved components."
- "Final architecture remains UNRESOLVED; formal Pareto analysis remains
  NOT_READY. This artifact advances evidence readiness, not a selection."

## Unsafe claims (must never be made from this evidence)

| Unsafe claim | Why it's unsafe | What this artifact actually supports |
|---|---|---|
| "The system consumes 7.2 mW." (stated as fact, no qualifiers) | Every contributing value is `ENGINEERING_ASSUMPTION`, not measured; omitting that turns an assumption into a fact | "≈7.2 mW **under stated engineering assumptions**, base topology only" |
| "7.2 mW is the minimum/guaranteed power draw." | Confuses an assumption-based reference scenario with a guaranteed lower bound (rule 35 — the same H7 error this project already corrected once for MAX86141) | It is a **reference scenario**, not a minimum or maximum |
| "The final wearable weighs 30.5 g." | 30.5 g is a `Tier2` generic-allowance estimate for 3 of 5 modules, excluding leg module, wiring harness, and the unresolved second-PPG-site boundary — not a finished, measured, or final design mass | "≈30.5 g **reference electronics-subassembly estimate**, base topology, Tier2 evidence" |
| "Four sensors were selected for the final system." | No architecture has been selected; sensor decisions remain target-specific (`CONDITIONAL_FOR_TARGET`, `DEPRIORITIZE_FOR_TARGET`, `EXPERIMENTAL`, `UNRESOLVED`), never a whole-system final selection (rule 79) | The reference topology has 9 stable component IDs; none is "the final BOM" |
| "The system data rate is 48 kbps." | The historical 48,068 bps figure silently included the deprioritized second-PPG-site branch (59% of the total) — see HW-1 correction in the data-rate report | "≈19.6 kbps base topology; +28.5 kbps optional second-PPG-site branch, reported separately" |
| "Digital Twin learns the astronaut's baseline." | Present-tense claim of an accomplished, validated capability; no training or validation has occurred in this project's scope | "Would support future longitudinal personalization when sufficient repeated subject-specific data are available" — conceptual, synthetic, untrained, unvalidated |
| "EEG/EOG head-AFE power is a verified datasheet value." | Explicitly an order-of-magnitude engineering estimate — Day-11 Part-2 and this environment both lack access to verify the exact ADS1299 power-dissipation table row | "An engineering assumption pending exact datasheet or bench-measurement verification" |
| "Regulator efficiency is measured at 85%." | 0.85 is a reference assumption for a generic buck/high-efficiency-LDO class, not a measured or vendor-specified figure for a selected part | "An engineering assumption for the reference regulator class" |
| "This BOM is final." / "This BOM is flight-ready." | Every line in `docs/STAGE4_REFERENCE_BOM_READINESS.md` is `final=false` | "`PARTIAL_REFERENCE_BOM`, `not_a_final_bom=true`" |

## Enforcement note

This ledger is a citation discipline document, not a code-level structural
checker. `docs/STAGE4_CONTROLLED_INTEGRATION_READINESS_CONTRACT.md` and the
existing `ml/check_claim_consistency.py` (per its own documented M4
limitation — verifies existence, not numerical correctness) remain the
software-level guards; this ledger is the human-facing reference for
whoever writes paper/jury copy from these artifacts.
