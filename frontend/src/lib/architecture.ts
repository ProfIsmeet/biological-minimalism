/**
 * Canonical, static product copy and structural inventory for the FINAL
 * CORE_PLUS_CONTEXT architecture, grounded in
 * results/final_wearable_architecture.json (fetched live by
 * SelectedArchitecturePanel / api.getFinalWearableArchitecture()).
 *
 * This module holds only structural facts and approved wording that do not
 * change per request (modality/region/order, the exact required sentences).
 * It must never hold live values (availability, freshness, fault state) —
 * those come from the canonical data flow at render time. See master prompt
 * §11.4/§11.5.
 */

export const FINAL_ARCHITECTURE_ID = "CORE_PLUS_CONTEXT" as const;

export type FinalModality = "PPG" | "IMU" | "ECG" | "EEG" | "EOG";
export type FinalRegion = "Wrist" | "Chest" | "Frontal";

export interface FinalSensorInventoryEntry {
  modality: FinalModality;
  region: FinalRegion;
  order: number;
  description: string;
}

// Required §7.5 ledger ordering: PPG, IMU, ECG, EEG, EOG.
export const FINAL_SENSOR_INVENTORY: FinalSensorInventoryEntry[] = [
  { modality: "PPG", region: "Wrist", order: 1, description: "Optical pulse sensing" },
  { modality: "IMU", region: "Wrist", order: 2, description: "Motion context" },
  { modality: "ECG", region: "Chest", order: 3, description: "Cardiac electrical reference" },
  { modality: "EEG", region: "Frontal", order: 4, description: "Cortical activity" },
  { modality: "EOG", region: "Frontal", order: 5, description: "Ocular context" },
];

// Single canonical modality->color mapping (master prompt §5/§12/§14) — every
// operational and system-brief visual reuses this instead of redeclaring its
// own copy, so a color can never silently drift between surfaces.
export const MODALITY_COLOR: Record<FinalModality, string> = {
  PPG: "#56C5B5",
  IMU: "#7D9FD3",
  ECG: "#D97979",
  EEG: "#A58BD0",
  EOG: "#D0A25E",
};

export interface FinalModule {
  id: string;
  order: string;
  label: string;
  modalities: string;
  description: string;
}

// Required §7.3 vertical module sequence: Frontal, Chest, Wrist.
export const FINAL_MODULES: FinalModule[] = [
  { id: "frontal", order: "01", label: "Frontal module", modalities: "EEG + EOG", description: "Cortical activity with ocular context" },
  { id: "chest", order: "02", label: "Chest module", modalities: "ECG", description: "Cardiac electrical reference" },
  { id: "wrist", order: "03", label: "Wrist module", modalities: "PPG + IMU", description: "Optical pulse sensing with motion context" },
];

export const MINIMAL_CORE_SUMMARY = "PPG + IMU · ECG · frontal EEG";
export const CORE_PLUS_CONTEXT_SUMMARY = "PPG + IMU · ECG · frontal EEG + EOG";

// Exact required sentences (master prompt §2, §7, §16) — render verbatim.
export const EOG_DELTA_NOTE = "EOG is the sole modality added beyond MINIMAL_CORE.";
export const CONDITIONAL_SELECTION_STATEMENT =
  "CORE_PLUS_CONTEXT was selected as a conditional evidence–burden trade-off.";
export const PARETO_RELEVANCE_LIMITATION =
  "MINIMAL_CORE and CORE_PLUS_CONTEXT remain Pareto-relevant; the selected architecture is not presented as a unique mathematical optimum.";
export const BOUNDED_ESTIMATE_QUALIFIER =
  "Bounded engineering estimates — not measured or flight-qualified hardware.";
export const DASHBOARD_VS_RESULTS_STATEMENT =
  "Dashboard values demonstrate interface behavior and are not the source of scientific Results.";
export const DIGITAL_TWIN_SCOPE_LABEL = "Architecture-only concept — untrained and unvalidated.";
export const S14_SCOPE_STATEMENT = "The S14 replay is a single-participant stress test, not population validation.";
export const ERROR_METRIC_QUALIFIER =
  "Error metrics apply only to valid predictions; prediction availability is reported separately.";
export const BIOZ_EXCLUSION_STATEMENT =
  "Thoracic BioZ/EIS and leg BioZ were evaluated as candidate sensors but were not carried into the final CORE_PLUS_CONTEXT architecture.";
export const PPG_DALIA_EVIDENCE_STATEMENT =
  "The PPG-DaLiA HR model and robustness replay support the HR and fault-awareness evidence layer.";

// Presentation-only mapping for results/final_wearable_architecture.json's
// exclusion_rationale keys — labels + body region only. Evidence status,
// final disposition text, and provenance are read live from the artifact;
// a key absent from the artifact simply does not render (never invented).
//
// `evaluationRole` is deliberately worded as a neutral technical description
// of what was evaluated (sensing site/placement), never an inferred
// biological role (e.g. "fluid-shift context") that the underlying artifact
// does not itself assert as a measured finding (corrective-pass §8).
export const CANDIDATE_DISPOSITION_DISPLAY: Record<
  string,
  { label: string; region: string; evaluationRole: string; stage3FamilyId?: string }
> = {
  thoracic_bioz_eis: {
    label: "Thoracic BioZ/EIS",
    region: "Chest (thoracic)",
    evaluationRole: "Candidate bioimpedance sensing at the thoracic site",
    stage3FamilyId: "lbnp_thoracic_eis",
  },
  leg_bioz: {
    label: "Leg BioZ",
    region: "Leg",
    evaluationRole: "Candidate bioimpedance sensing at the leg site",
    stage3FamilyId: "qde_v2_leg_bioz",
  },
  second_site_ppg: {
    label: "Second-site PPG",
    region: "Secondary limb site",
    evaluationRole: "Candidate secondary PPG placement",
    stage3FamilyId: "ptt_second_ppg_site",
  },
  wrist_temperature_light: {
    label: "Wrist temperature + light",
    region: "Wrist",
    evaluationRole: "Candidate wrist temperature and light channels",
    // No Stage-3 evidence family evaluates this candidate (TIER_P_PENDING —
    // absence of governing evidence, not a negative result) — intentionally
    // no stage3FamilyId here.
  },
};

export const BIOZ_FINAL_DISPOSITION = "Not selected for CORE_PLUS_CONTEXT";
