import type { FinalModality } from "@/lib/architecture";
import { computeAccelerationMagnitude } from "./formatMonitoringValue";
import type { ModalityObservation } from "@/lib/monitoring/modalityObservation";

export interface PlotSeries {
  values: number[];
  unit: string | null;
  transform: string | null;
  /** Grounded in RawChannelBatch.sample_rate_hz — null when no such channel exists (e.g. synthetic PPG). */
  sampleRateHz: number | null;
  /** Grounded in RawChannelBatch.start_timestamp_seconds — never fabricated for sources without real timing metadata. */
  startTimestampSeconds: number | null;
  endTimestampSeconds: number | null;
}

function isMatrix(samples: number[] | number[][]): samples is number[][] {
  return Array.isArray(samples) && Array.isArray(samples[0]);
}

/**
 * Resolves what, if anything, can be honestly plotted for a modality. Only
 * PPG has a legitimate synthetic waveform (`vitals.ppg_waveform`); IMU, ECG,
 * EEG, and EOG have no synthetic waveform payload in the current backend
 * contract, so they render an explicit unavailable reason instead of a
 * placeholder line (master prompt §9.4). Final ECG stays unavailable in
 * synthetic mode rather than repurposing `ecg_like_waveform`, which the
 * backend schema itself documents as a derived charting waveform, not a
 * measured ECG channel.
 *
 * Extracted out of components/monitoring/FinalSignalStack.tsx (Prompt-2
 * corrective pass §3) so it is a plain, JSX-free module the deterministic
 * verification script can import directly — a .tsx file that pulls in
 * WaveformChart/recharts cannot be loaded under plain Node type-stripping.
 */
export function resolvePlotSeries(
  modality: FinalModality,
  isReplay: boolean,
  observation: ModalityObservation,
  syntheticPpgWaveform: number[] | undefined,
): PlotSeries | null {
  if (isReplay) {
    if (!observation.channelBatch) return null;
    const { samples, units, sample_rate_hz, start_timestamp_seconds, end_timestamp_seconds } = observation.channelBatch;
    if (modality === "IMU" && isMatrix(samples)) {
      return {
        values: computeAccelerationMagnitude(samples),
        unit: units,
        transform: "Derived acceleration magnitude",
        sampleRateHz: sample_rate_hz,
        startTimestampSeconds: start_timestamp_seconds,
        endTimestampSeconds: end_timestamp_seconds,
      };
    }
    if (!isMatrix(samples)) {
      return {
        values: samples,
        unit: units,
        transform: null,
        sampleRateHz: sample_rate_hz,
        startTimestampSeconds: start_timestamp_seconds,
        endTimestampSeconds: end_timestamp_seconds,
      };
    }
    return null;
  }
  if (modality === "PPG" && syntheticPpgWaveform?.length) {
    return {
      values: syntheticPpgWaveform,
      unit: null,
      transform: null,
      sampleRateHz: null,
      startTimestampSeconds: null,
      endTimestampSeconds: null,
    };
  }
  return null;
}
