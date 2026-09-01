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
}

export interface AvailableSubjectsResponse {
  dataset_name: string;
  subjects: string[];
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
