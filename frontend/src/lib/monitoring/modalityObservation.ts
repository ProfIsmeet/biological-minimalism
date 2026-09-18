import type { FinalModality } from "@/lib/architecture";
import type { RawChannelBatch, SensorName, SensorReading } from "@/lib/types";

/**
 * Per-modality telemetry observation (master prompt §5.7) — kept distinct
 * from architecture membership (a static fact, see lib/architecture.ts
 * FINAL_SENSOR_INVENTORY) and from a single generic "sensor status". Ported
 * out of jury/FinalSensorLedger.tsx's original inline logic so
 * FinalSensorLedger and the live-monitoring signal stack can never silently
 * diverge on what "observed" means for a given modality/source.
 *
 * Grounded in the real backend contract, not assumed:
 * - Replay: PPG-DaLiA's default replay channel set is exactly {wrist_bvp,
 *   wrist_acc, chest_ecg, wrist_temp} (backend/app/data/ppg_dalia.py
 *   DEFAULT_REPLAY_CHANNELS). EEG is always in PPG_DALIA_UNAVAILABLE_CHANNELS.
 *   EOG has no channel concept in this dataset at all.
 * - Synthetic: only PPG and EEG have a live per-sensor health field
 *   (backend SensorName enum). Synthetic "ECG" is `vitals.ecg_like_waveform`,
 *   an explicitly derived charting waveform, not a modeled ECG channel — so
 *   it is never treated as an observed ECG modality. IMU and EOG have no
 *   synthetic field at all.
 */
const REPLAY_CHANNEL_KEY: Partial<Record<FinalModality, string>> = {
  PPG: "wrist_bvp",
  IMU: "wrist_acc",
  ECG: "chest_ecg",
};

const SYNTHETIC_HEALTH_KEY: Partial<Record<FinalModality, SensorName>> = {
  PPG: "ppg",
  EEG: "eeg",
};

export type ModalityObservationState =
  | "recorded_replay_observed"
  | "recorded_replay_waiting_for_samples"
  | "synthetic_observed"
  | "unavailable";

export interface ModalityObservation {
  modality: FinalModality;
  state: ModalityObservationState;
  /** Real channel name from the payload, or null when no channel concept exists for this modality/source. */
  channelName: string | null;
  /** Unit exactly as reported by the payload's channel metadata — never hardcoded. */
  unit: string | null;
  /** Short human label, e.g. "Recorded replay — channel present". */
  statusLabel: string;
  /** Only set when state === "unavailable". */
  unavailableReason: string | null;
  /** The raw channel batch when one exists, for chart rendering. */
  channelBatch: RawChannelBatch | null;
  /** Synthetic per-sensor health reading, when one exists (PPG/EEG only). */
  syntheticHealth: SensorReading | null;
}

export function deriveModalityObservation(
  modality: FinalModality,
  params: {
    isReplay: boolean;
    channels: RawChannelBatch[] | undefined;
    availableChannels: string[] | undefined;
    sensors: SensorReading[] | undefined;
  },
): ModalityObservation {
  const { isReplay, channels, availableChannels, sensors } = params;

  if (isReplay) {
    const channelName = REPLAY_CHANNEL_KEY[modality] ?? null;
    const listed = channelName ? Boolean(availableChannels?.includes(channelName)) : false;
    const channelBatch = channelName ? channels?.find((batch) => batch.channel_name === channelName) ?? null : null;

    if (!listed) {
      return {
        modality,
        state: "unavailable",
        channelName,
        unit: null,
        statusLabel: "Not reported by current telemetry",
        unavailableReason: channelName
          ? `${channelName} is not present in the active replay session.`
          : `No ${modality} channel exists in the current backend contract.`,
        channelBatch: null,
        syntheticHealth: null,
      };
    }

    // Prompt-2 corrective pass §5: a channel can be listed in
    // `available_channels` before a `RawChannelBatch` for the current
    // window has actually arrived in this snapshot. That is a genuinely
    // different (neutral, transient) state from the channel being absent —
    // it must not be labeled "unavailable", and it must not render a plot
    // without samples.
    if (!channelBatch) {
      return {
        modality,
        state: "recorded_replay_waiting_for_samples",
        channelName,
        unit: null,
        statusLabel: "Recorded replay — channel available; waiting for current-window samples",
        unavailableReason: null,
        channelBatch: null,
        syntheticHealth: null,
      };
    }

    return {
      modality,
      state: "recorded_replay_observed",
      channelName,
      unit: channelBatch.units,
      statusLabel: "Recorded replay — current samples available",
      unavailableReason: null,
      channelBatch,
      syntheticHealth: null,
    };
  }

  const healthKey = SYNTHETIC_HEALTH_KEY[modality] ?? null;
  const reading = healthKey ? sensors?.find((sensor) => sensor.sensor === healthKey) ?? null : null;
  return {
    modality,
    state: reading ? "synthetic_observed" : "unavailable",
    channelName: null,
    unit: null,
    statusLabel: reading
      ? `Synthetic demo channel — ${synthesisStatusLabel(reading.status)}`
      : "Not reported by current telemetry",
    unavailableReason: reading ? null : "Channel not present in the active source",
    channelBatch: null,
    syntheticHealth: reading,
  };
}

function synthesisStatusLabel(status: SensorReading["status"]): string {
  if (status === "offline") return "Unavailable";
  if (status === "degraded") return "Degraded";
  return "Nominal";
}
