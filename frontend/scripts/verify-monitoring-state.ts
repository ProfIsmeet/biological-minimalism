/**
 * Deterministic verification for the frontend/src/lib/monitoring/* helpers
 * (Prompt-2 corrective pass §3). This is not a scientific artifact and
 * produces no output consumed by the application — every value below is a
 * TEST FIXTURE invented for this script, not real telemetry, not a real
 * dataset, and not a real backend response.
 *
 * Run with:
 *   node --experimental-strip-types --no-warnings scripts/run-verify-monitoring-state.mjs
 * (from the `frontend/` directory)
 *
 * This imports and exercises the actual production helpers under
 * src/lib/monitoring/ — none of their logic is reimplemented here. The only
 * production file touched to make this possible was extracting
 * `resolvePlotSeries` out of the JSX component that used to own it
 * (components/monitoring/FinalSignalStack.tsx) into the plain
 * lib/monitoring/plotSeries.ts module, since a .tsx file that imports
 * recharts cannot be loaded under plain Node type-stripping.
 */

import { deriveTransportState, deriveReplaySessionState, replaySessionStateLabel } from "../src/lib/monitoring/runtimeState";
import { deriveSourceLabel, deriveConnectionLabel } from "../src/lib/monitoring/sourceState";
import {
  sourceIdentityFromStatus,
  sourceIdentityFromSnapshot,
  snapshotMatchesConfirmedSource,
} from "../src/lib/monitoring/sourceIdentity";
import {
  derivePredictionAvailability,
  predictionAvailabilityLabel,
  inferenceStatusLabel,
  deriveFaultSummaryLabel,
  computeCurrentWindowAbsoluteDifference,
} from "../src/lib/monitoring/inferenceState";
import {
  deriveFaultAwareInferenceView,
  NO_INFERENCE_STATUS_YET_MESSAGE,
  SOURCE_DISCONNECTED_MESSAGE,
  WAITING_FOR_CONFIRMED_FRAME_MESSAGE,
} from "../src/lib/monitoring/faultAwareInferenceView";
import { deriveModalityObservation } from "../src/lib/monitoring/modalityObservation";
import { resolvePlotSeries } from "../src/lib/monitoring/plotSeries";
import {
  computeAccelerationMagnitude,
  downsampleForDisplay,
  formatFaultTypeLabel,
} from "../src/lib/monitoring/formatMonitoringValue";

import type { ConnectionStatus } from "../src/store/missionStore";
import type {
  DataSourceStatus,
  LiveMetricsSnapshot,
  RawChannelBatch,
  ReplayFaultState,
  HeartRateModelPrediction,
  HeartRateInferenceState,
  SensorReading,
} from "../src/lib/types";

// ---------------------------------------------------------------------------
// Tiny inline check harness (no Jest/Vitest — see corrective prompt §3).
// ---------------------------------------------------------------------------

let passed = 0;
let failed = 0;
const failures: string[] = [];

function check(name: string, condition: boolean, detail?: string): void {
  if (condition) {
    passed += 1;
  } else {
    failed += 1;
    failures.push(detail ? `${name} — ${detail}` : name);
  }
}

function checkEqual<T>(name: string, actual: T, expected: T): void {
  check(name, actual === expected, `expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
}

function checkIncludes(name: string, haystack: string, needle: string): void {
  check(name, haystack.includes(needle), `expected "${haystack}" to include "${needle}"`);
}

function checkNotIncludes(name: string, haystack: string, needle: string): void {
  check(name, !haystack.includes(needle), `expected "${haystack}" to NOT include "${needle}"`);
}

// ---------------------------------------------------------------------------
// Fixture builders. FIXTURE_* naming makes it unmistakable these are not
// real subjects/datasets/checkpoints if this file is ever read out of
// context. `as unknown as T` casts are used deliberately to avoid hand-
// populating every field of these large production interfaces — the fields
// exercised by the helpers under test are always populated explicitly.
// ---------------------------------------------------------------------------

function fixtureDataSourceStatus(overrides: Partial<DataSourceStatus>): DataSourceStatus {
  return {
    source_type: "synthetic",
    dataset_configured: true,
    dataset_name: null,
    subject_id: null,
    replay_position_seconds: null,
    duration_seconds: null,
    playback_state: null,
    playback_speed: null,
    end_behavior: null,
    channels: [],
    fault_injection: fixtureFault({ active: false }),
    ...overrides,
  } as unknown as DataSourceStatus;
}

function fixtureSnapshot(overrides: Record<string, unknown>): LiveMetricsSnapshot {
  return {
    timestamp: 0,
    source: {
      source_type: "synthetic",
      display_label: "FIXTURE",
      dataset_name: null,
      subject_id: null,
      replay_position_seconds: null,
      duration_seconds: null,
      playback_state: null,
      playback_speed: null,
      end_behavior: null,
      available_channels: [],
      unavailable_channels: [],
      ...((overrides.source as Record<string, unknown>) ?? {}),
    },
    channels: [],
    heart_rate_prediction: null,
    heart_rate_inference: null,
    fault_injection: null,
    mission_mode: null,
    mission_day: null,
    vitals: null,
    cognitive: null,
    space_adaptation: null,
    sensor_health: null,
    ai_confidence: null,
    ...overrides,
  } as unknown as LiveMetricsSnapshot;
}

function fixtureFault(overrides: Partial<ReplayFaultState>): ReplayFaultState {
  return {
    active: false,
    fault_type: null,
    target: null,
    target_channels: [],
    affected_channels: [],
    severity: null,
    seed: null,
    dropped_samples: {},
    parameters: {},
    ...overrides,
  } as unknown as ReplayFaultState;
}

function fixturePrediction(overrides: Partial<HeartRateModelPrediction>): HeartRateModelPrediction {
  return {
    prediction_type: "heart_rate",
    value: 72.5,
    unit: "bpm",
    normalized_model_output: 0,
    evidence_level: "AI_ESTIMATED",
    uncertainty: null,
    provenance: {
      dataset_name: "PPG-DaLiA",
      subject_id: "FIXTURE_SUBJECT",
      window_index: 0,
      window_start_seconds: 0,
      window_duration_seconds: 8,
      input_channels: ["wrist_bvp", "wrist_acc"],
      model_id: "FIXTURE_MODEL",
      checkpoint_path: "FIXTURE_PATH",
      checkpoint_sha256: "FIXTURE_SHA",
      fault_injection: null,
    },
    ...overrides,
  } as unknown as HeartRateModelPrediction;
}

function fixtureInference(overrides: Partial<HeartRateInferenceState>): HeartRateInferenceState {
  return {
    status: "available",
    message: "FIXTURE",
    required_window_seconds: 8,
    required_channels: ["wrist_bvp", "wrist_acc"],
    ...overrides,
  } as unknown as HeartRateInferenceState;
}

function fixtureChannelBatch(overrides: Partial<RawChannelBatch>): RawChannelBatch {
  return {
    dataset_name: "PPG-DaLiA",
    subject_id: "FIXTURE_SUBJECT",
    channel_name: "wrist_bvp",
    device: "FIXTURE_DEVICE",
    role: "physiological",
    axes: ["bvp"],
    units: "device units",
    sample_rate_hz: 64,
    sample_start_index: 0,
    start_timestamp_seconds: 0,
    end_timestamp_seconds: 1,
    samples: [1, 2, 3],
    ...overrides,
  } as unknown as RawChannelBatch;
}

function fixtureSensorReading(overrides: Partial<SensorReading>): SensorReading {
  return { sensor: "ppg", status: "nominal", signal_quality: 0.9, ...overrides } as unknown as SensorReading;
}

// ===========================================================================
// Transport and source
// ===========================================================================

checkEqual("transport: connected synthetic", deriveTransportState("open" as ConnectionStatus), "connected");
checkEqual("transport: connecting synthetic", deriveTransportState("connecting" as ConnectionStatus), "connecting");
checkEqual("transport: disconnected synthetic", deriveTransportState("closed" as ConnectionStatus), "disconnected");

checkEqual("source label: connected synthetic", deriveSourceLabel({ connectionStatus: "open", isReplay: false }), "SYNTHETIC DEMO");
checkEqual("source label: replay confirmed (connected + isReplay)", deriveSourceLabel({ connectionStatus: "open", isReplay: true }), "RECORDED REPLAY");
checkEqual("source label: unavailable source (disconnected replay)", deriveSourceLabel({ connectionStatus: "closed", isReplay: true }), "UNAVAILABLE");
checkEqual("connection label: connecting", deriveConnectionLabel("connecting"), "CONNECTING");
checkEqual("connection label: disconnected", deriveConnectionLabel("closed"), "DISCONNECTED");

{
  // Confirmed-source identity + fail-closed matching (corrective §2).
  const syntheticStatus = fixtureDataSourceStatus({ source_type: "synthetic", subject_id: null });
  const replayStatusS1 = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "FIXTURE_S1" });

  const syntheticSnapshot = fixtureSnapshot({ source: { source_type: "synthetic", subject_id: null } });
  const replaySnapshotS1 = fixtureSnapshot({ source: { source_type: "dataset_replay", subject_id: "FIXTURE_S1" } });
  const replaySnapshotS2 = fixtureSnapshot({ source: { source_type: "dataset_replay", subject_id: "FIXTURE_S2" } });

  check("identity: synthetic confirmed + matching synthetic frame", snapshotMatchesConfirmedSource(syntheticSnapshot, syntheticStatus));
  check("identity: synthetic confirmed + LATE replay frame is rejected", !snapshotMatchesConfirmedSource(replaySnapshotS1, syntheticStatus));
  check("identity: replay S1 confirmed + LATE synthetic frame is rejected", !snapshotMatchesConfirmedSource(syntheticSnapshot, replayStatusS1));
  check("identity: replay S1 confirmed + matching replay S1 frame", snapshotMatchesConfirmedSource(replaySnapshotS1, replayStatusS1));
  check("identity: replay S1 confirmed + frame from a DIFFERENT subject (S2) is rejected", !snapshotMatchesConfirmedSource(replaySnapshotS2, replayStatusS1));
  check("identity: no REST status yet + synthetic frame is provisionally trusted", snapshotMatchesConfirmedSource(syntheticSnapshot, null));
  check("identity: no REST status yet + replay frame is provisionally trusted", snapshotMatchesConfirmedSource(replaySnapshotS1, null));
  check("identity: authoritative status exists but no snapshot at all → not confirmed", !snapshotMatchesConfirmedSource(null, replayStatusS1));

  const s1Identity = sourceIdentityFromStatus(replayStatusS1);
  checkEqual("sourceIdentityFromStatus: replay subject carried through", s1Identity?.subjectId, "FIXTURE_S1");
  const syntheticIdentity = sourceIdentityFromSnapshot(syntheticSnapshot);
  checkEqual("sourceIdentityFromSnapshot: synthetic subjectId is always null", syntheticIdentity?.subjectId, null);

  // Prompt-2B corrective §7: explicit proof that a mismatched snapshot
  // carrying an ACTIVE fault and a valid prediction is still rejected in
  // full — a consumer reading through useConfirmedSnapshot() gets `null`,
  // never a stale fault or prediction from the wrong subject.
  const mismatchedSnapshotWithFaultAndPrediction = fixtureSnapshot({
    source: { source_type: "dataset_replay", subject_id: "FIXTURE_S2" },
    fault_injection: fixtureFault({ active: true, target: "ppg", fault_type: "modality_dropout", severity: 1 }),
    heart_rate_prediction: fixturePrediction({ value: 999 }),
  });
  check(
    "identity: mismatched snapshot with active fault + prediction is fully rejected",
    !snapshotMatchesConfirmedSource(mismatchedSnapshotWithFaultAndPrediction, replayStatusS1),
  );
}

// ===========================================================================
// Replay state
// ===========================================================================

checkEqual(
  "replay state: dataset unavailable",
  deriveReplaySessionState({ datasetConfigured: false, isReplaySource: false, playbackState: null, selectedSubjectId: null, pendingAction: null, requestError: null }),
  "dataset_unavailable",
);
checkEqual(
  "replay state: subject unselected",
  deriveReplaySessionState({ datasetConfigured: true, isReplaySource: false, playbackState: null, selectedSubjectId: null, pendingAction: null, requestError: null }),
  "subject_unselected",
);
checkEqual(
  "replay state: loading",
  deriveReplaySessionState({ datasetConfigured: true, isReplaySource: false, playbackState: null, selectedSubjectId: "FIXTURE_S1", pendingAction: "load", requestError: null }),
  "loading",
);
checkEqual(
  "replay state: ready",
  deriveReplaySessionState({ datasetConfigured: true, isReplaySource: true, playbackState: "unloaded", selectedSubjectId: "FIXTURE_S1", pendingAction: null, requestError: null }),
  "ready",
);
checkEqual(
  "replay state: playing",
  deriveReplaySessionState({ datasetConfigured: true, isReplaySource: true, playbackState: "playing", selectedSubjectId: "FIXTURE_S1", pendingAction: null, requestError: null }),
  "playing",
);
checkEqual(
  "replay state: paused",
  deriveReplaySessionState({ datasetConfigured: true, isReplaySource: true, playbackState: "paused", selectedSubjectId: "FIXTURE_S1", pendingAction: null, requestError: null }),
  "paused",
);
checkEqual(
  "replay state: completed",
  deriveReplaySessionState({ datasetConfigured: true, isReplaySource: true, playbackState: "ended", selectedSubjectId: "FIXTURE_S1", pendingAction: null, requestError: null }),
  "completed",
);
checkEqual(
  "replay state: request error",
  deriveReplaySessionState({ datasetConfigured: true, isReplaySource: true, playbackState: "paused", selectedSubjectId: "FIXTURE_S1", pendingAction: null, requestError: "FIXTURE network failure" }),
  "error",
);
checkEqual("replay state label: playing", replaySessionStateLabel("playing"), "Playing");
checkEqual("replay state label: dataset_unavailable", replaySessionStateLabel("dataset_unavailable"), "Dataset unavailable");

// ===========================================================================
// Prediction and inference
// ===========================================================================

checkEqual(
  "prediction availability: valid replay prediction",
  derivePredictionAvailability({ connected: true, isReplay: true, prediction: fixturePrediction({}) }),
  "available",
);
checkEqual(
  "prediction availability: missing replay prediction",
  derivePredictionAvailability({ connected: true, isReplay: true, prediction: null }),
  "unavailable_no_prediction",
);
checkEqual(
  "prediction availability: synthetic not applicable",
  derivePredictionAvailability({ connected: true, isReplay: false, prediction: null }),
  "not_applicable",
);
checkEqual(
  "prediction availability: disconnected",
  derivePredictionAvailability({ connected: false, isReplay: true, prediction: fixturePrediction({}) }),
  "not_applicable",
);
checkEqual("prediction availability label: available", predictionAvailabilityLabel("available"), "Valid prediction for the current window");

checkEqual("inference status: warming up", inferenceStatusLabel(fixtureInference({ status: "warming_up" }), true), "Model is warming up");
checkEqual("inference status: input unavailable", inferenceStatusLabel(fixtureInference({ status: "input_unavailable" }), true), "Required PPG + IMU input window is unavailable");
checkEqual("inference status: model unavailable", inferenceStatusLabel(fixtureInference({ status: "model_unavailable" }), true), "HR model is unavailable");
checkEqual("inference status: inference error", inferenceStatusLabel(fixtureInference({ status: "error" }), true), "Inference error");
checkEqual("inference status: null + replay (waiting, not synthetic)", inferenceStatusLabel(null, true), "No inference status reported yet for the current replay session");
checkEqual("inference status: null + synthetic", inferenceStatusLabel(null, false), "Not applicable in synthetic demo mode");

checkEqual("current-window difference: missing reference returns null (estimate present)", computeCurrentWindowAbsoluteDifference(72, null), null);
checkEqual("current-window difference: missing estimate returns null (reference present)", computeCurrentWindowAbsoluteDifference(null, 70), null);
checkEqual("current-window difference: real pair returns correct absolute difference", computeCurrentWindowAbsoluteDifference(75, 70), 5);
checkEqual("current-window difference: real pair, order-independent magnitude", computeCurrentWindowAbsoluteDifference(60, 65), 5);

// ===========================================================================
// Fault
// ===========================================================================

checkEqual("fault label: no simulated fault (inactive)", deriveFaultSummaryLabel(fixtureFault({ active: false })), "No simulated fault is active.");
checkEqual("fault label: no simulated fault (null)", deriveFaultSummaryLabel(null), "No simulated fault is active.");

{
  const ppgDropout = deriveFaultSummaryLabel(fixtureFault({ active: true, target: "ppg", fault_type: "modality_dropout", severity: 1 }));
  checkIncludes("fault label: PPG modality dropout mentions PPG", ppgDropout, "PPG");
  checkIncludes("fault label: PPG modality dropout mentions fault type", ppgDropout, "modality dropout");
  checkIncludes("fault label: PPG modality dropout includes severity", ppgDropout, "severity 1");

  const imuPacketLoss = deriveFaultSummaryLabel(fixtureFault({ active: true, target: "imu", fault_type: "packet_loss", severity: 0.25 }));
  checkIncludes("fault label: IMU packet loss mentions IMU", imuPacketLoss, "IMU");
  checkIncludes("fault label: IMU packet loss mentions fault type", imuPacketLoss, "packet loss");
  checkIncludes("fault label: IMU packet loss includes severity", imuPacketLoss, "severity 0.25");

  const bothAdditiveNoise = deriveFaultSummaryLabel(fixtureFault({ active: true, target: "both", fault_type: "additive_noise", severity: 0.5 }));
  checkIncludes("fault label: both-modality additive noise mentions BOTH", bothAdditiveNoise, "BOTH");
  checkIncludes("fault label: both-modality additive noise mentions fault type", bothAdditiveNoise, "additive noise");

  const frozenSensor = deriveFaultSummaryLabel(fixtureFault({ active: true, target: "ppg", fault_type: "frozen_sensor", severity: 1 }));
  checkIncludes("fault label: frozen sensor mentions fault type", frozenSensor, "frozen sensor");

  const saturation = deriveFaultSummaryLabel(fixtureFault({ active: true, target: "imu", fault_type: "saturation", severity: 0.75 }));
  checkIncludes("fault label: saturation mentions fault type", saturation, "saturation");

  const missingSeverity = deriveFaultSummaryLabel(fixtureFault({ active: true, target: "ppg", fault_type: "modality_dropout", severity: null }));
  checkNotIncludes("fault label: severity omitted when null (not fabricated)", missingSeverity, "severity");

  for (const [name, label] of [
    ["PPG modality dropout", ppgDropout],
    ["IMU packet loss", imuPacketLoss],
    ["both-modality additive noise", bothAdditiveNoise],
    ["frozen sensor", frozenSensor],
    ["saturation", saturation],
    ["missing severity", missingSeverity],
  ] as const) {
    checkIncludes(`fault label contains "Simulated": ${name}`, label, "Simulated");
  }

  checkEqual("formatFaultTypeLabel: underscore replaced with space", formatFaultTypeLabel("modality_dropout"), "modality dropout");
}

// ===========================================================================
// Fault-aware inference presentation state (Prompt-2C §4/§7)
// ===========================================================================

{
  // Case 1 — replay selected + connected + confirmed replay prediction +
  // available inference + no simulated fault.
  const nominal = deriveFaultAwareInferenceView({
    connected: true,
    isReplay: true,
    isWaitingForConfirmation: false,
    prediction: fixturePrediction({ value: 72.5 }),
    inference: fixtureInference({ status: "available" }),
    fault: fixtureFault({ active: false }),
  });
  checkEqual("fault-aware view: case 1 — nominal status", nominal.status, "Nominal");
  checkEqual("fault-aware view: case 1 — valid prediction text", nominal.currentValidPrediction, "72.5 bpm (window 0.0s)");
  checkEqual("fault-aware view: case 1 — actual inference status shown", nominal.inferenceModelStatus, "available");
  checkEqual("fault-aware view: case 1 — no active fault", nominal.activeFaultCondition, "None");

  // Case 2 — replay selected + connected + confirmed replay frame + no
  // valid prediction.
  const noPrediction = deriveFaultAwareInferenceView({
    connected: true,
    isReplay: true,
    isWaitingForConfirmation: false,
    prediction: null,
    inference: fixtureInference({ status: "input_unavailable" }),
    fault: fixtureFault({ active: false }),
  });
  checkEqual("fault-aware view: case 2 — no fabricated prediction", noPrediction.currentValidPrediction, "None this window");
  checkEqual("fault-aware view: case 2 — bounded prediction-unavailable text", noPrediction.predictionAvailability, "No valid prediction — see status below");
  checkEqual("fault-aware view: case 2 — bounded inference-status text", noPrediction.inferenceModelStatus, "input unavailable");
  checkEqual("fault-aware view: case 2 — status is Unavailable, not fabricated Nominal/Degraded", noPrediction.status, "Unavailable");

  // Case 3 — replay selected + connected + mismatched (rejected) snapshot.
  // The "stale" prediction/inference/fault below simulate what a rejected
  // cross-source snapshot could have carried; every field must render the
  // waiting message regardless, proving none of this stale content leaks.
  const waiting = deriveFaultAwareInferenceView({
    connected: true,
    isReplay: true,
    isWaitingForConfirmation: true,
    prediction: fixturePrediction({ value: 999 }),
    inference: fixtureInference({ status: "available" }),
    fault: fixtureFault({ active: true, target: "ppg", fault_type: "modality_dropout", severity: 1 }),
  });
  checkEqual("fault-aware view: case 3 — status is Waiting", waiting.status, "Waiting");
  checkEqual("fault-aware view: case 3 — inference source uses waiting message", waiting.currentInferenceSource, WAITING_FOR_CONFIRMED_FRAME_MESSAGE);
  checkEqual("fault-aware view: case 3 — active fault condition uses waiting message", waiting.activeFaultCondition, WAITING_FOR_CONFIRMED_FRAME_MESSAGE);
  checkEqual("fault-aware view: case 3 — prediction availability uses waiting message", waiting.predictionAvailability, WAITING_FOR_CONFIRMED_FRAME_MESSAGE);
  checkEqual("fault-aware view: case 3 — current valid prediction uses waiting message", waiting.currentValidPrediction, WAITING_FOR_CONFIRMED_FRAME_MESSAGE);
  checkEqual("fault-aware view: case 3 — inference model status uses waiting message", waiting.inferenceModelStatus, WAITING_FOR_CONFIRMED_FRAME_MESSAGE);
  checkNotIncludes("fault-aware view: case 3 — no stale prediction value (999) survives", waiting.currentValidPrediction, "999");
  checkNotIncludes("fault-aware view: case 3 — no stale fault target survives", waiting.activeFaultCondition, "PPG");
  checkNotIncludes("fault-aware view: case 3 — no stale inference status survives", waiting.inferenceModelStatus, "available");

  // Case 4 — synthetic selected + confirmed synthetic frame. No replay
  // inference window is ever evaluated in synthetic mode, so every
  // current-frame field must say so explicitly rather than claiming a
  // replay-specific "None this window" result (Prompt-2D §4/§6.4).
  const synthetic = deriveFaultAwareInferenceView({
    connected: true,
    isReplay: false,
    isWaitingForConfirmation: false,
    prediction: null,
    inference: null,
    fault: null,
  });
  checkEqual("fault-aware view: case 4 — synthetic scope explicit in inference source", synthetic.currentInferenceSource, "Synthetic demo (not AI-estimated)");
  checkEqual("fault-aware view: case 4 — synthetic scope explicit in prediction availability", synthetic.predictionAvailability, "Not applicable in synthetic demo mode");
  checkEqual("fault-aware view: case 4 — current valid prediction is synthetic-scoped, not a replay-window claim", synthetic.currentValidPrediction, "Not applicable in synthetic demo mode");
  checkEqual("fault-aware view: case 4 — inference model status is synthetic-scoped", synthetic.inferenceModelStatus, "Not applicable in synthetic demo mode");
  checkEqual("fault-aware view: case 4 — no active fault", synthetic.activeFaultCondition, "None");
  checkEqual("fault-aware view: case 4 — status is Unavailable (no replay active), not fabricated", synthetic.status, "Unavailable");
  checkNotIncludes("fault-aware view: case 4 — no replay-window claim in current valid prediction", synthetic.currentValidPrediction, "None this window");

  // Case 5 — disconnected source, with DELIBERATELY STALE prediction/
  // inference/fault objects (Prompt-2D §6.1). `useLiveFeed`/`missionStore`
  // flip `connectionStatus` on transport drop but never erase the last
  // `latest` snapshot, so a real disconnected component can still receive
  // these stale objects — a null-only fixture would not have caught the
  // Prompt-2D bug where activeFaultCondition/currentValidPrediction/
  // inferenceModelStatus skipped the `connected` check entirely.
  const disconnectedWithStaleData = deriveFaultAwareInferenceView({
    connected: false,
    isReplay: true,
    isWaitingForConfirmation: false,
    prediction: fixturePrediction({ value: 999 }),
    inference: fixtureInference({ status: "available" }),
    fault: fixtureFault({ active: true, target: "ppg", fault_type: "modality_dropout", severity: 1 }),
  });
  checkEqual("fault-aware view: case 5 — status is Unavailable", disconnectedWithStaleData.status, "Unavailable");
  checkEqual("fault-aware view: case 5 — inference source uses disconnected message", disconnectedWithStaleData.currentInferenceSource, SOURCE_DISCONNECTED_MESSAGE);
  checkEqual("fault-aware view: case 5 — active fault condition uses disconnected message", disconnectedWithStaleData.activeFaultCondition, SOURCE_DISCONNECTED_MESSAGE);
  checkEqual("fault-aware view: case 5 — prediction availability uses disconnected message", disconnectedWithStaleData.predictionAvailability, SOURCE_DISCONNECTED_MESSAGE);
  checkEqual("fault-aware view: case 5 — current valid prediction uses disconnected message", disconnectedWithStaleData.currentValidPrediction, SOURCE_DISCONNECTED_MESSAGE);
  checkEqual("fault-aware view: case 5 — inference model status uses disconnected message", disconnectedWithStaleData.inferenceModelStatus, SOURCE_DISCONNECTED_MESSAGE);
  checkNotIncludes("fault-aware view: case 5 — stale prediction value (999) does not survive", disconnectedWithStaleData.currentValidPrediction, "999");
  checkNotIncludes("fault-aware view: case 5 — stale fault target (PPG) does not survive", disconnectedWithStaleData.activeFaultCondition, "PPG");
  checkNotIncludes("fault-aware view: case 5 — stale fault type (modality dropout) does not survive", disconnectedWithStaleData.activeFaultCondition, "modality dropout");
  check(
    "fault-aware view: case 5 — stale inference status (available) does not survive as its own value",
    disconnectedWithStaleData.inferenceModelStatus !== "available",
    `expected inferenceModelStatus not to be the literal stale value "available", got ${JSON.stringify(disconnectedWithStaleData.inferenceModelStatus)}`,
  );
  checkNotIncludes("fault-aware view: case 5 — result does not say Nominal", disconnectedWithStaleData.status, "Nominal");
  checkNotIncludes("fault-aware view: case 5 — result does not say Degraded", disconnectedWithStaleData.status, "Degraded");

  // Case 6 — connected replay, confirmed snapshot, but no inference object
  // has been reported yet AND no prediction exists (Prompt-2D §6.2).
  const connectedReplayNoInferenceNoPrediction = deriveFaultAwareInferenceView({
    connected: true,
    isReplay: true,
    isWaitingForConfirmation: false,
    prediction: null,
    inference: null,
    fault: fixtureFault({ active: false }),
  });
  checkEqual("fault-aware view: case 6 — status is Unavailable", connectedReplayNoInferenceNoPrediction.status, "Unavailable");
  checkEqual("fault-aware view: case 6 — current valid prediction is None this window", connectedReplayNoInferenceNoPrediction.currentValidPrediction, "None this window");
  checkEqual("fault-aware view: case 6 — inference model status is the replay-specific not-yet-reported message", connectedReplayNoInferenceNoPrediction.inferenceModelStatus, NO_INFERENCE_STATUS_YET_MESSAGE);
  checkNotIncludes("fault-aware view: case 6 — inference model status does not say synthetic demo", connectedReplayNoInferenceNoPrediction.inferenceModelStatus, "synthetic demo");
  checkNotIncludes("fault-aware view: case 6 — prediction availability does not say synthetic demo", connectedReplayNoInferenceNoPrediction.predictionAvailability, "synthetic demo");
  checkNotIncludes("fault-aware view: case 6 — current valid prediction does not say synthetic demo", connectedReplayNoInferenceNoPrediction.currentValidPrediction, "synthetic demo");

  // Case 7 — connected replay, confirmed snapshot, a VALID prediction, but
  // still no inference object (Prompt-2D §6.3) — prediction presence must
  // never be used to fabricate an inference status.
  const connectedReplayPredictionNoInference = deriveFaultAwareInferenceView({
    connected: true,
    isReplay: true,
    isWaitingForConfirmation: false,
    prediction: fixturePrediction({ value: 64.3 }),
    inference: null,
    fault: fixtureFault({ active: false }),
  });
  checkEqual("fault-aware view: case 7 — actual prediction value is displayed", connectedReplayPredictionNoInference.currentValidPrediction, "64.3 bpm (window 0.0s)");
  checkEqual("fault-aware view: case 7 — inference model status is still the replay-specific not-yet-reported message", connectedReplayPredictionNoInference.inferenceModelStatus, NO_INFERENCE_STATUS_YET_MESSAGE);
  checkNotIncludes("fault-aware view: case 7 — status is not Nominal (inference.status !== \"available\" was never asserted)", connectedReplayPredictionNoInference.status, "Nominal");
  checkNotIncludes("fault-aware view: case 7 — inference model status does not say synthetic demo", connectedReplayPredictionNoInference.inferenceModelStatus, "synthetic demo");
  checkNotIncludes("fault-aware view: case 7 — current valid prediction does not say synthetic demo", connectedReplayPredictionNoInference.currentValidPrediction, "synthetic demo");
}

// ===========================================================================
// Modalities
// ===========================================================================

{
  const wristBvpBatch = fixtureChannelBatch({ channel_name: "wrist_bvp", units: "device units", samples: [1, 2, 3] });
  const wristAccBatch = fixtureChannelBatch({ channel_name: "wrist_acc", units: "device units", samples: [[1, 2, 3], [4, 5, 6]] });
  const chestEcgBatch = fixtureChannelBatch({ channel_name: "chest_ecg", units: "device units", samples: [10, 20, 30] });

  const ppgPresent = deriveModalityObservation("PPG", { isReplay: true, channels: [wristBvpBatch], availableChannels: ["wrist_bvp"], sensors: undefined });
  checkEqual("modality: replay PPG present — state", ppgPresent.state, "recorded_replay_observed");
  checkEqual("modality: replay PPG present — label", ppgPresent.statusLabel, "Recorded replay — current samples available");
  checkEqual("modality: replay PPG present — unit from payload", ppgPresent.unit, "device units");

  const imuPresent = deriveModalityObservation("IMU", { isReplay: true, channels: [wristAccBatch], availableChannels: ["wrist_acc"], sensors: undefined });
  checkEqual("modality: replay IMU present — state", imuPresent.state, "recorded_replay_observed");

  const ecgPresent = deriveModalityObservation("ECG", { isReplay: true, channels: [chestEcgBatch], availableChannels: ["chest_ecg"], sensors: undefined });
  checkEqual("modality: replay ECG present — state", ecgPresent.state, "recorded_replay_observed");

  const eegAbsent = deriveModalityObservation("EEG", { isReplay: true, channels: [], availableChannels: [], sensors: undefined });
  checkEqual("modality: replay EEG absent — state", eegAbsent.state, "unavailable");
  checkIncludes("modality: replay EEG absent — reason names EEG", eegAbsent.unavailableReason ?? "", "EEG");

  const eogAbsent = deriveModalityObservation("EOG", { isReplay: true, channels: [], availableChannels: [], sensors: undefined });
  checkEqual("modality: replay EOG absent — state", eogAbsent.state, "unavailable");
  checkIncludes("modality: replay EOG absent — reason names EOG", eogAbsent.unavailableReason ?? "", "EOG");

  const syntheticEegHealth = deriveModalityObservation("EEG", { isReplay: false, channels: undefined, availableChannels: undefined, sensors: [fixtureSensorReading({ sensor: "eeg", status: "nominal" })] });
  checkEqual("modality: synthetic EEG health available — state", syntheticEegHealth.state, "synthetic_observed");
  const syntheticEegPlot = resolvePlotSeries("EEG", false, syntheticEegHealth, undefined);
  checkEqual("modality: synthetic EEG has health but NO plottable waveform", syntheticEegPlot, null);

  const syntheticPpgObservation = deriveModalityObservation("PPG", { isReplay: false, channels: undefined, availableChannels: undefined, sensors: [fixtureSensorReading({ sensor: "ppg", status: "nominal" })] });
  const syntheticPpgPlot = resolvePlotSeries("PPG", false, syntheticPpgObservation, [0.1, 0.2, 0.3]);
  check("modality: synthetic PPG waveform available — plot resolved", syntheticPpgPlot !== null);
  checkEqual("modality: synthetic PPG waveform values pass through unchanged", syntheticPpgPlot?.values.length, 3);

  const waitingForSamples = deriveModalityObservation("PPG", { isReplay: true, channels: [], availableChannels: ["wrist_bvp"], sensors: undefined });
  checkEqual("modality: channel declared available but batch absent — state", waitingForSamples.state, "recorded_replay_waiting_for_samples");
  checkEqual("modality: waiting-for-samples label", waitingForSamples.statusLabel, "Recorded replay — channel available; waiting for current-window samples");
  check("modality: waiting-for-samples never called unavailable", waitingForSamples.state !== "unavailable");
  checkEqual("modality: waiting-for-samples resolves no plot", resolvePlotSeries("PPG", true, waitingForSamples, undefined), null);

  const notDeclaredAvailable = deriveModalityObservation("PPG", { isReplay: true, channels: [wristBvpBatch], availableChannels: [], sensors: undefined });
  checkEqual("modality: channel not declared available — state (batch presence does not override)", notDeclaredAvailable.state, "unavailable");
}

// ===========================================================================
// Numerical helpers
// ===========================================================================

checkEqual("acceleration magnitude: 3-4-0 triangle", computeAccelerationMagnitude([[3, 4, 0]])[0], 5);
checkEqual("acceleration magnitude: incomplete row defaults missing axes to 0", computeAccelerationMagnitude([[3]])[0], 3);

{
  const small = downsampleForDisplay([1, 2, 3], 400);
  checkEqual("downsampling: below threshold — values unchanged", small.values.length, 3);
  checkEqual("downsampling: below threshold — not flagged as downsampled", small.downsampled, false);

  const large = downsampleForDisplay(Array.from({ length: 1000 }, (_, i) => i), 100);
  check("downsampling: above threshold — flagged as downsampled", large.downsampled === true);
  check("downsampling: above threshold — reduced to <= maxPoints", large.values.length <= 100);
}

// ===========================================================================
// Summary
// ===========================================================================

const total = passed + failed;
console.log(`verify-monitoring-state: ${passed}/${total} passed, ${failed} failed`);
if (failed > 0) {
  console.error("\nFAILURES:");
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exit(1);
}
process.exit(0);
