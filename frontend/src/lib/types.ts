/**
 * Types mirroring the backend's pydantic schemas 1:1 (see
 * backend/app/schemas/). Field names match the JSON the API actually
 * returns — keep these in sync by hand if the backend schemas change.
 */

export type MissionMode = "earth_orbit" | "lunar_surface" | "deep_space" | "solar_event";

export type SensorName = "eeg" | "ppg" | "temperature" | "bioimpedance";

export type SensorStatus = "nominal" | "degraded" | "offline";

export type DataSourceType = "synthetic" | "dataset_replay";

export type ReplayPlaybackState = "unloaded" | "paused" | "playing" | "ended";

export type ReplayFaultType =
  | "modality_dropout"
  | "packet_loss"
  | "frozen_sensor"
  | "additive_noise"
  | "saturation";

export type ReplayFaultTarget = "ppg" | "imu" | "both";

export interface ReplayFaultConfig {
  fault_type: ReplayFaultType;
  target: ReplayFaultTarget;
  severity: number;
  seed: number;
}

export interface ReplayFaultState {
  active: boolean;
  fault_type: ReplayFaultType | null;
  target: ReplayFaultTarget | null;
  target_channels: string[];
  affected_channels: string[];
  severity: number | null;
  seed: number | null;
  dropped_samples: Record<string, number>;
  parameters: Record<string, number | string | number[] | string[]>;
}

export interface ChannelMetadata {
  name: string;
  sample_rate_hz: number;
  device: string;
  role: string;
  axes: string[];
  units: string;
}

export interface TelemetrySourceMetadata {
  source_type: DataSourceType;
  display_label: string;
  dataset_name: string | null;
  subject_id: string | null;
  replay_position_seconds: number | null;
  duration_seconds: number | null;
  playback_state: ReplayPlaybackState | null;
  playback_speed: number | null;
  end_behavior: string | null;
  license: string | null;
  source_url: string | null;
  available_channels: string[];
  unavailable_channels: string[];
}

export interface RawChannelBatch {
  dataset_name: string;
  subject_id: string;
  channel_name: string;
  device: string;
  role: string;
  axes: string[];
  units: string;
  sample_rate_hz: number;
  sample_start_index: number;
  start_timestamp_seconds: number;
  end_timestamp_seconds: number;
  samples: number[] | number[][];
}

export type ModelInferenceStatus =
  | "warming_up"
  | "available"
  | "input_unavailable"
  | "model_unavailable"
  | "error";

export interface HeartRateInferenceState {
  status: ModelInferenceStatus;
  message: string;
  required_window_seconds: 8;
  required_channels: ["wrist_bvp", "wrist_acc"];
}

export interface HeartRateModelProvenance {
  dataset_name: "PPG-DaLiA";
  subject_id: string;
  window_index: number;
  window_start_seconds: number;
  window_duration_seconds: number;
  input_channels: ["wrist_bvp", "wrist_acc"];
  model_id: string;
  checkpoint_path: string;
  checkpoint_sha256: string;
  fault_injection: ReplayFaultState | null;
}

export interface HeartRateModelPrediction {
  prediction_type: "heart_rate";
  value: number;
  unit: "bpm";
  normalized_model_output: number;
  evidence_level: "AI_ESTIMATED";
  uncertainty: null;
  provenance: HeartRateModelProvenance;
}

export interface VitalsSnapshot {
  heart_rate_bpm: number | null;
  hrv_rmssd_ms: number | null;
  respiration_rate_bpm: number | null;
  blood_pressure_systolic_mmhg: number | null;
  blood_pressure_diastolic_mmhg: number | null;
  ppg_waveform: number[];
  ecg_like_waveform: number[];
  ecg_waveform: number[];
}

export interface CognitiveSnapshot {
  cognitive_load: number;
  fatigue: number;
  circadian_stability: number;
  eeg_attention: number;
  eeg_band_powers: Record<string, number>;
}

export interface SpaceAdaptationSnapshot {
  fluid_shift_risk: number;
  autonomic_balance: number;
  thermal_stability: number;
}

export interface SensorReading {
  sensor: SensorName;
  status: SensorStatus;
  signal_quality: number;
}

export interface SensorHealthSnapshot {
  sensors: SensorReading[];
}

export interface AIConfidenceSnapshot {
  overall_confidence: number;
  sensor_contribution: Record<string, number>;
}

export interface LiveMetricsSnapshot {
  timestamp: number;
  source: TelemetrySourceMetadata;
  channels: RawChannelBatch[];
  heart_rate_prediction: HeartRateModelPrediction | null;
  heart_rate_inference: HeartRateInferenceState | null;
  fault_injection: ReplayFaultState | null;
  mission_mode: MissionMode | null;
  mission_day: number | null;
  vitals: VitalsSnapshot | null;
  cognitive: CognitiveSnapshot | null;
  space_adaptation: SpaceAdaptationSnapshot | null;
  sensor_health: SensorHealthSnapshot | null;
  ai_confidence: AIConfidenceSnapshot | null;
}

export interface DigitalTwinSystemScore {
  system: string;
  baseline_score: number;
  current_score: number;
  delta: number;
}

export interface DigitalTwinState {
  mission_day: number;
  milestone_label: string;
  narrative: string;
  systems: DigitalTwinSystemScore[];
  overall_adaptation: number;
}

export interface FeatureContribution {
  feature: string;
  value: number;
  shap_value: number;
  direction: "increased_risk" | "decreased_risk" | "neutral";
}

export interface AIExplanation {
  target: "ai_confidence" | "fatigue_risk";
  summary_text: string;
  base_value: number;
  predicted_value: number;
  contributions: FeatureContribution[];
  generated_at: number;
}

export interface SimulationStateResponse {
  mission_mode: MissionMode;
  sensor_status: Record<SensorName, SensorStatus>;
}

export interface DataSourceStatus {
  source_type: DataSourceType;
  dataset_configured: boolean;
  dataset_name: string | null;
  subject_id: string | null;
  replay_position_seconds: number | null;
  duration_seconds: number | null;
  playback_state: ReplayPlaybackState | null;
  playback_speed: number | null;
  end_behavior: string | null;
  channels: ChannelMetadata[];
  fault_injection: ReplayFaultState;
}

export interface AvailableSubjectsResponse {
  dataset_name: string;
  subjects: string[];
}

export type ResearchAvailability = "available" | "unavailable";
export type ResearchResultClass =
  | "positive_marginal_value"
  | "negative_marginal_result"
  | "robustness_characterization";
export type MarginalDirection = "improved" | "worsened" | "mixed" | "not_applicable";

export interface ResearchMetricEstimate {
  mean: number | null;
  sd: number | null;
  n: number | null;
  unit: string;
}

export interface ResearchConfiguration {
  configuration_id: string;
  label: string;
  description: string;
  sensing: string[];
  metrics: Record<string, ResearchMetricEstimate>;
}

export interface ResearchScope {
  subjects: string[];
  held_out_subjects: string[];
  evaluation_windows: number;
  activities: string[];
  evidence_level: "experimental_evaluation";
  environment_scope:
    | "terrestrial_free_living"
    | "terrestrial_controlled"
    | "analog"
    | "simulation"
    | "spaceflight";
  cohort_note: string;
}

export interface ResearchMarginalResult {
  baseline_configuration_id: string;
  candidate_configuration_id: string;
  added_sensing: string;
  metric: string;
  delta: ResearchMetricEstimate;
  direction: MarginalDirection;
  paired_replicates: number | null;
  candidate_improved_count: number | null;
  candidate_worsened_count: number | null;
  notes: string[];
}

export interface ResearchBreakdownEntry {
  entry_id: string;
  label: string;
  dimensions: Record<string, string | number | boolean | null>;
  configuration_metrics: Record<string, Record<string, ResearchMetricEstimate>>;
  delta: ResearchMetricEstimate | null;
}

export interface ResearchBreakdown {
  breakdown_id: string;
  kind: string;
  title: string;
  entries: ResearchBreakdownEntry[];
}

export interface ResearchCheckpointIdentity {
  run_id: string;
  model_id: string;
  sha256: string;
  size_bytes: number;
}

export interface ResearchProvenance {
  source_artifact: string;
  supporting_artifacts: string[];
  dataset_version: string | null;
  split_identity: string | null;
  model_identity: string[];
  checkpoints: ResearchCheckpointIdentity[];
  experiment_version: string | null;
}

export interface ResearchClaimBoundaries {
  supported: string[];
  unsupported: string[];
  limitations: string[];
}

export interface ResearchOperationalCosts {
  sensor_contact_regions: number | null;
  additional_module_count: number | null;
  power_estimate: number | null;
  mass_estimate: number | null;
  compute_estimate: number | null;
  comfort_burden: number | null;
}

export interface ResearchExperiment {
  experiment_id: string;
  title: string;
  research_question: string;
  dataset: string;
  target: string;
  status: "complete";
  result_class: ResearchResultClass;
  outcome_summary: string;
  scope: ResearchScope;
  configurations: ResearchConfiguration[];
  marginal_result: ResearchMarginalResult | null;
  breakdowns: ResearchBreakdown[];
  provenance: ResearchProvenance;
  claim_boundaries: ResearchClaimBoundaries;
  operational_costs: ResearchOperationalCosts;
}

export interface ResearchExperimentSummary {
  experiment_id: string;
  title: string;
  research_question: string;
  dataset: string;
  target: string;
  status: "complete";
  result_class: ResearchResultClass;
  outcome_summary: string;
  held_out_subject_count: number;
  source_artifact: string;
}

export interface ResearchExperimentEnvelope {
  experiment_id: string;
  availability: ResearchAvailability;
  experiment: ResearchExperiment | null;
  error: string | null;
}

export interface ResearchExperimentSummaryEnvelope {
  experiment_id: string;
  availability: ResearchAvailability;
  summary: ResearchExperimentSummary | null;
  error: string | null;
}

export interface ResearchProjectSummary {
  experiment_count: number;
  available_count: number;
  unavailable_count: number;
  experiments: ResearchExperimentSummaryEnvelope[];
  statement: string;
}

export type CostEvidenceLevel =
  | "measured"
  | "manufacturer_spec"
  | "literature_estimate"
  | "derived"
  | "architectural_count"
  | "unknown";
export type CostAvailability = "known" | "unknown";
export type CostValueKind = "exact" | "range";
export type CostBasis = "marginal" | "total";
export type OperationMode = "continuous" | "periodic" | "intermittent" | "event_driven" | "unresolved";

export interface OperationalQuantity {
  availability: CostAvailability;
  value_kind: CostValueKind;
  value: number | null;
  minimum: number | null;
  typical: number | null;
  maximum: number | null;
  unit: string;
  basis: CostBasis;
  evidence_level: CostEvidenceLevel;
  provenance_ids: string[];
  notes: string[];
}

export interface CostEvidenceRecord {
  evidence_id: string;
  evidence_level: CostEvidenceLevel;
  title: string;
  source_reference: string;
  component_or_artifact_identity: string;
  operating_condition: string;
  value_characterization: string;
  version_or_date: string | null;
  assumptions: string[];
}

export interface SharedHardwareContext {
  shared_module_id: string | null;
  integration_context: string;
  incremental_vs_standalone: string;
  allocation_status: string;
  double_counting_risk: string;
  naive_addition_allowed: false;
}

export interface OperationalCostComponent {
  component_id: string;
  label: string;
  status: "scientifically_mapped" | "architecture_placeholder";
  category: "wearable" | "cabin_context";
  sensing_modality: string;
  channels: string[];
  physical_site: string;
  architecture_role: string;
  operation_mode: OperationMode;
  duty_cycle: OperationalQuantity;
  experimental_sensor_identity: string | null;
  candidate_hardware_identity: string | null;
  scientific_experiment_ids: string[];
  dimensions: Record<string, OperationalQuantity>;
  operational_burden_proxies: string[];
  reliability_exposure: string[];
  shared_hardware: SharedHardwareContext;
  assumptions: string[];
  unknowns: string[];
}

export interface ScientificJoinContract {
  join_key: "component_id";
  expected_scientific_fields: string[];
  cost_contract_status: string;
  scientific_contract_status: string;
  scientific_benefit: null;
  allowed_future_outputs: string[];
  prohibited_current_outputs: string[];
}

export interface OperationalCostCatalog {
  schema_version: string;
  catalog_id: string;
  title: string;
  methodology_path: string;
  generated_from_commit: string;
  evidence: CostEvidenceRecord[];
  components: OperationalCostComponent[];
  scientific_join_contract: ScientificJoinContract;
}

export interface OperationalCostCatalogEnvelope {
  availability: ResearchAvailability;
  catalog: OperationalCostCatalog | null;
  error: string | null;
}

export interface OperationalCostComponentEnvelope {
  component_id: string;
  availability: ResearchAvailability;
  component: OperationalCostComponent | null;
  error: string | null;
}

export interface ParetoReadyInput {
  component_id: string;
  operational_cost_component_id: string;
  scientific_experiment_ids: string[];
  target: string | null;
  scientific_benefit: null;
  join_status: string;
}

export const MISSION_MODES: { value: MissionMode; label: string }[] = [
  { value: "earth_orbit", label: "Earth Orbit" },
  { value: "lunar_surface", label: "Lunar Surface" },
  { value: "deep_space", label: "Deep Space" },
  { value: "solar_event", label: "Solar Event" },
];

export const SENSOR_NAMES: { value: SensorName; label: string }[] = [
  { value: "eeg", label: "Wireless EEG" },
  { value: "ppg", label: "PPG" },
  { value: "temperature", label: "Peripheral Temperature" },
  { value: "bioimpedance", label: "Bio-impedance" },
];
