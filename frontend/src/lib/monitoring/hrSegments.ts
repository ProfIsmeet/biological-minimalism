/**
 * Pure HR-ring categorical segment mapping, split out of HRInferenceCore.tsx
 * (master prompt 3A §10/§19) so scripts/verify-monitoring-state.ts can
 * assert the SRC/PPG/IMU/OUT on/off mapping — including the PPG-fault
 * interruption case — without rendering the component.
 */
export interface HrSegment {
  key: "source" | "ppg" | "imu" | "model";
  abbr: "SRC" | "PPG" | "IMU" | "OUT";
  label: string;
  on: boolean;
  faulted: boolean;
}

export function computeHrSegments(params: {
  sourceConfirmed: boolean;
  ppgAvailable: boolean;
  imuAvailable: boolean;
  modelOutputAvailable: boolean;
  ppgFaulted: boolean;
  imuFaulted: boolean;
}): HrSegment[] {
  return [
    { key: "source", abbr: "SRC", label: "Source confirmed", on: params.sourceConfirmed, faulted: false },
    { key: "ppg", abbr: "PPG", label: "PPG input", on: params.ppgAvailable, faulted: params.ppgFaulted },
    { key: "imu", abbr: "IMU", label: "IMU input", on: params.imuAvailable, faulted: params.imuFaulted },
    { key: "model", abbr: "OUT", label: "Model output", on: params.modelOutputAvailable, faulted: false },
  ];
}
