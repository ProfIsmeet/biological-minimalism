/**
 * Types mirroring the backend's pydantic schemas 1:1 (see
 * backend/app/schemas/). Field names match the JSON the API actually
 * returns — keep these in sync by hand if the backend schemas change.
 */

export type MissionMode = "earth_orbit" | "lunar_surface" | "deep_space" | "solar_event";

export type SensorName = "eeg" | "ppg" | "temperature" | "bioimpedance";

export type SensorStatus = "nominal" | "degraded" | "offline";

export interface VitalsSnapshot {
  heart_rate_bpm: number;
  hrv_rmssd_ms: number;
  respiration_rate_bpm: number;
  blood_pressure_systolic_mmhg: number;
  blood_pressure_diastolic_mmhg: number;
  ppg_waveform: number[];
  ecg_like_waveform: number[];
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
  mission_mode: MissionMode;
  mission_day: number;
  vitals: VitalsSnapshot;
  cognitive: CognitiveSnapshot;
  space_adaptation: SpaceAdaptationSnapshot;
  sensor_health: SensorHealthSnapshot;
  ai_confidence: AIConfidenceSnapshot;
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
