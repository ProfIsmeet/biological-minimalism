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

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { deriveTransportState, deriveReplaySessionState, replaySessionStateLabel } from "../src/lib/monitoring/runtimeState";
import { applyFaultOverride, applyTelemetryGate, deriveTelemetryAvailability, resolveReplayStateLabel, telemetryAvailabilityLabel } from "../src/lib/monitoring/telemetryAvailability";
import { useMissionStore } from "../src/store/missionStore";
import { computeOrthographicFit, orthoCameraPosition } from "../src/components/visualization/human/humanLayout";
import { deriveSourceLabel, deriveConnectionLabel } from "../src/lib/monitoring/sourceState";
import {
  sourceIdentityFromStatus,
  sourceIdentityFromSnapshot,
  sourceIdentityKey,
  snapshotMatchesConfirmedSource,
} from "../src/lib/monitoring/sourceIdentity";
import { deriveIdentityContextDisplay } from "../src/lib/monitoring/liveMonitoringPresentation";
import {
  deriveConfidenceDisplay,
  isFiniteMetricValue,
  metricGroupLevelForAvailability,
  metricLevelForAvailability,
} from "../src/lib/monitoring/insightDisplay";
import { deriveFaultControlPresentation, deriveReplayControlPresentation } from "../src/lib/monitoring/controlPresentation";
import {
  classifySourceConvergenceStatus,
  planSourceConvergenceRequest,
  SourceStateRequestCoordinator,
  statusConfirmsSourceConvergence,
} from "../src/lib/monitoring/sourceConvergence";
import { confirmedHistoryForState, confirmedSnapshotForState } from "../src/lib/monitoring/useConfirmedSnapshot";
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
import { computeDynamicDomain, downsampleExtremaPreserving } from "../src/lib/monitoring/waveformDisplay";
import { deriveModalityNodeState, nodeStateLabel } from "../src/lib/monitoring/modalityNodeState";
import { deriveIntegrityRings } from "../src/lib/monitoring/integrityRings";
import { deriveHexFlow } from "../src/lib/monitoring/inferenceHexFlow";
import { deriveEventsFromTransition, type OperationalEventSignature } from "../src/lib/monitoring/operationalEvents";
import { projectPoint, rotateY } from "../src/lib/visualization/twinProjection";
import { dedupeAgainstLast } from "../src/store/operationalEventStore";
import { BODY_SEGMENTS, HEAD_RADIUS, JOINTS, computeSegmentTransform, isFiniteVec3 } from "../src/components/visualization/human/humanGeometry";
import { ALL_FINAL_MODALITIES, MODALITY_ANCHOR_POSITION, REGION_ORBITS, buildSensorAnchors } from "../src/components/visualization/human/humanLayout";
import { computeHrSegments } from "../src/lib/monitoring/hrSegments";
import { deriveHrTrend } from "../src/lib/monitoring/hrTrend";
import { buildAnatomicalHuman } from "../src/components/visualization/human/anatomicalHumanGeometry";
// Prompt-4 additions — route/runtime isolation, presenter preflight, demo
// reset, architecture separation and claim-safety.
import {
  classifyRuntimeTier,
  tierOpensWebSocket,
  tierMountsMonitoringSession,
} from "../src/lib/runtime/operationalRuntimeTier";
import {
  derivePresenterPreflight,
  planDemoReset,
  summariseDemoReset,
  CANONICAL_JURY_SUBJECT_ID,
  checkCanonicalBootstrapPrerequisites,
  runCanonicalJuryBootstrap,
  summariseCanonicalBootstrap,
  type DemoResetResult,
  type CanonicalBootstrapResult,
} from "../src/lib/monitoring/presenterOps";
import {
  FINAL_ARCHITECTURE_ID,
  FINAL_SENSOR_INVENTORY,
  EOG_DELTA_NOTE,
  MINIMAL_CORE_SUMMARY,
  CORE_PLUS_CONTEXT_SUMMARY,
  S14_SCOPE_STATEMENT,
  DIGITAL_TWIN_SCOPE_LABEL,
  BOUNDED_ESTIMATE_QUALIFIER,
  DASHBOARD_VS_RESULTS_STATEMENT,
  BIOZ_EXCLUSION_STATEMENT,
} from "../src/lib/architecture";
// Prompt-4A corrective additions.
import { reduceMotionEnabledFromStorage } from "../src/lib/runtime/reduceMotion";

/** Repo `frontend/src` root, for the Prompt 3A.1 Digital Twin source-inspection tests (readFileSync-based, since that route's .tsx cannot be imported into this plain-Node harness). */
const REPO_SRC_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "src");

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

  const replayDatasetA = fixtureDataSourceStatus({ source_type: "dataset_replay", dataset_name: "FIXTURE_A", subject_id: "FIXTURE_S1" });
  const replayDatasetB = fixtureSnapshot({ source: { source_type: "dataset_replay", dataset_name: "FIXTURE_B", subject_id: "FIXTURE_S1" } });
  check(
    "identity F-23: same source + subject from a different dataset is rejected",
    !snapshotMatchesConfirmedSource(replayDatasetB, replayDatasetA),
  );
  const replayDatasetAMatch = fixtureSnapshot({ source: { source_type: "dataset_replay", dataset_name: "FIXTURE_A", subject_id: "FIXTURE_S1" } });
  check("identity F-23: same dataset + source + subject remains confirmed", snapshotMatchesConfirmedSource(replayDatasetAMatch, replayDatasetA));

  const unknownDatasetIdentity = sourceIdentityFromStatus(
    fixtureDataSourceStatus({ source_type: "dataset_replay", dataset_name: null, subject_id: "FIXTURE_S1" }),
  );
  const literalDatasetIdentity = sourceIdentityFromStatus(
    fixtureDataSourceStatus({ source_type: "dataset_replay", dataset_name: "unconfirmed", subject_id: "FIXTURE_S1" }),
  );
  check(
    "identity F-23: tagged missing dataset cannot collide with a real dataset name",
    unknownDatasetIdentity !== null
      && literalDatasetIdentity !== null
      && sourceIdentityKey(unknownDatasetIdentity) !== sourceIdentityKey(literalDatasetIdentity),
  );

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
// WaveformChart helpers (master prompt 3 §8.6) — dynamic domain and
// extrema-preserving downsampling.
// ===========================================================================

{
  const positive = computeDynamicDomain([1, 2, 3, 10]);
  check("domain: positive-only — lower bound stays positive", positive !== null && positive[0] > 0);
  check("domain: positive-only — upper bound exceeds max value", positive !== null && positive[1] > 10);

  const negative = computeDynamicDomain([-10, -5, -1]);
  check("domain: negative-only — upper bound stays negative", negative !== null && negative[1] < 0);
  check("domain: negative-only — lower bound below min value", negative !== null && negative[0] < -10);

  const zeroCrossing = computeDynamicDomain([-3, 0, 4]);
  check("domain: zero-crossing — spans zero", zeroCrossing !== null && zeroCrossing[0] < 0 && zeroCrossing[1] > 0);

  const flatline = computeDynamicDomain([2, 2, 2, 2]);
  check("domain: flatline — non-degenerate padded range", flatline !== null && flatline[0] < 2 && flatline[1] > 2);

  const zeroFlatline = computeDynamicDomain([0, 0, 0]);
  check("domain: zero flatline — uses absolute epsilon padding, not NaN", zeroFlatline !== null && Number.isFinite(zeroFlatline[0]) && Number.isFinite(zeroFlatline[1]));

  const withNonFinite = computeDynamicDomain([1, Number.NaN, 5, Number.POSITIVE_INFINITY, 3]);
  check("domain: non-finite values filtered before min/max", withNonFinite !== null && withNonFinite[1] < 100);

  const allNonFinite = computeDynamicDomain([Number.NaN, Number.POSITIVE_INFINITY]);
  checkEqual("domain: all non-finite — returns null (explicit unavailable, not a fake range)", allNonFinite, null);

  const empty = computeDynamicDomain([]);
  checkEqual("domain: empty input — returns null", empty, null);
}

{
  const shortSeries = [1, 5, 2];
  const passThrough = downsampleExtremaPreserving(shortSeries, 400);
  checkEqual("downsample: short series — pass-through length", passThrough.points.length, 3);
  checkEqual("downsample: short series — not flagged as downsampled", passThrough.downsampled, false);
  checkEqual("downsample: short series — values unchanged in order", passThrough.points.map((p) => p.value).join(","), "1,5,2");

  const flat = downsampleExtremaPreserving(Array.from({ length: 500 }, () => 4), 50);
  check("downsample: flatline — does not crash and respects budget", flat.points.length <= 50);
  check("downsample: flatline — every retained value equals the flat value", flat.points.every((p) => p.value === 4));

  const n = 1000;
  const large = Array.from({ length: n }, (_, i) => Math.sin(i / 20));
  const result = downsampleExtremaPreserving(large, 100);
  checkEqual("downsample: first sample retained", result.points[0]?.index, 0);
  checkEqual("downsample: last sample retained", result.points[result.points.length - 1]?.index, n - 1);
  check("downsample: output respects point budget", result.points.length <= 100);
  check("downsample: flagged as downsampled when input exceeds budget", result.downsampled === true);
  let chronological = true;
  for (let i = 1; i < result.points.length; i++) {
    if (result.points[i]!.index <= result.points[i - 1]!.index) chronological = false;
  }
  check("downsample: chronological ordering preserved", chronological);

  // A single-sample spike hidden inside an otherwise flat region — naive
  // stride decimation would very likely step over it; the extrema-preserving
  // bucket algorithm must retain it as a bucket max.
  const spikeIndex = 437;
  const withPeak = Array.from({ length: n }, (_, i) => (i === spikeIndex ? 500 : 0));
  const peakResult = downsampleExtremaPreserving(withPeak, 100);
  check("downsample: narrow peak retained", peakResult.points.some((p) => p.value === 500));

  const withTrough = Array.from({ length: n }, (_, i) => (i === spikeIndex ? -500 : 0));
  const troughResult = downsampleExtremaPreserving(withTrough, 100);
  check("downsample: narrow trough retained", troughResult.points.some((p) => p.value === -500));
}

// ===========================================================================
// Operational modality-node state (master prompt 3 §12/§44)
// ===========================================================================

{
  const wristBvpBatch = fixtureChannelBatch({ channel_name: "wrist_bvp", units: "device units", samples: [1, 2, 3] });
  const confirmedObservation = deriveModalityObservation("PPG", { isReplay: true, channels: [wristBvpBatch], availableChannels: ["wrist_bvp"], sensors: undefined });
  const unavailableObservation = deriveModalityObservation("EOG", { isReplay: true, channels: [], availableChannels: [], sensors: undefined });
  const waitingObservation = deriveModalityObservation("PPG", { isReplay: true, channels: [], availableChannels: ["wrist_bvp"], sensors: undefined });

  checkEqual(
    "modality node state: active telemetry + confirmed observation -> confirmed",
    deriveModalityNodeState({ telemetry: "active", isFaulted: false, observation: confirmedObservation }),
    "confirmed",
  );
  checkEqual(
    "modality node state: active telemetry + faulted overrides confirmed observation -> fault",
    deriveModalityNodeState({ telemetry: "active", isFaulted: true, observation: confirmedObservation }),
    "fault",
  );
  checkEqual(
    "modality node state: disconnected overrides everything -> disconnected",
    deriveModalityNodeState({ telemetry: "disconnected", isFaulted: true, observation: confirmedObservation }),
    "disconnected",
  );
  checkEqual(
    "modality node state: no channel in source -> unavailable",
    deriveModalityNodeState({ telemetry: "active", isFaulted: false, observation: unavailableObservation }),
    "unavailable",
  );
  checkEqual(
    "modality node state: channel declared but no batch yet -> warmup",
    deriveModalityNodeState({ telemetry: "active", isFaulted: false, observation: waitingObservation }),
    "warmup",
  );
  checkEqual(
    "modality node state: synthetic sensor reported offline -> unavailable (not a fabricated fault)",
    deriveModalityNodeState({
      telemetry: "active",
      isFaulted: false,
      observation: deriveModalityObservation("EEG", { isReplay: false, channels: undefined, availableChannels: undefined, sensors: [fixtureSensorReading({ sensor: "eeg", status: "offline" })] }),
    }),
    "unavailable",
  );
  // Prompt 3A.1 §4.6/§9 item 5 — a simulated fault must never be presented
  // as currently confirmed while telemetry cannot be trusted; the gate
  // reason takes precedence over `isFaulted` regardless of how it was set.
  checkEqual(
    "modality node state: awaiting_confirmation gate overrides a faulted observation -> awaiting_confirmation, not fault",
    deriveModalityNodeState({ telemetry: "awaiting_confirmation", isFaulted: true, observation: confirmedObservation }),
    "awaiting_confirmation",
  );
  checkEqual(
    "modality node state: source_error gate overrides a faulted observation -> source_error, not fault",
    deriveModalityNodeState({ telemetry: "source_error", isFaulted: true, observation: confirmedObservation }),
    "source_error",
  );

  checkEqual("modality node state label: confirmed", nodeStateLabel("confirmed"), "Confirmed");
  checkEqual("modality node state label: warmup", nodeStateLabel("warmup"), "Replay warm-up");
  checkEqual("modality node state label: unavailable", nodeStateLabel("unavailable"), "No channel in current source");
  checkEqual("modality node state label: fault", nodeStateLabel("fault"), "Simulated fault");
  checkEqual("modality node state label: disconnected", nodeStateLabel("disconnected"), "Disconnected");
  checkEqual("modality node state label: awaiting_confirmation", nodeStateLabel("awaiting_confirmation"), "Connected — awaiting confirmed frame");
  checkEqual("modality node state label: source_error", nodeStateLabel("source_error"), "Source error");

  // Confirmed-channel count over a fixed 5-entry inventory, mirroring how
  // useOperationalViewModel() reduces OperationalModalityState[] — 2
  // confirmed, 1 warmup, 1 unavailable, 1 fault out of 5 total. Also
  // Prompt 3A.1 §9 item 13 — a fault localized to one modality must not
  // suppress an unaffected, otherwise-confirmed modality's own state.
  const nodeStates = [
    deriveModalityNodeState({ telemetry: "active", isFaulted: false, observation: confirmedObservation }),
    deriveModalityNodeState({ telemetry: "active", isFaulted: false, observation: confirmedObservation }),
    deriveModalityNodeState({ telemetry: "active", isFaulted: false, observation: waitingObservation }),
    deriveModalityNodeState({ telemetry: "active", isFaulted: false, observation: unavailableObservation }),
    deriveModalityNodeState({ telemetry: "active", isFaulted: true, observation: confirmedObservation }),
  ];
  checkEqual(
    "confirmed-channel count: 2 of 5 confirmed in a mixed inventory",
    nodeStates.filter((state) => state === "confirmed").length,
    2,
  );
  check(
    "fault localization: the faulted entry is 'fault' while an otherwise-identical unaffected entry stays 'confirmed'",
    nodeStates[0] === "confirmed" && nodeStates[4] === "fault",
  );
}

// ===========================================================================
// Telemetry-availability gate (Prompt 3A.1 §4/§9) — the single authoritative
// "may current telemetry be trusted" state, and the root-cause fix for the
// Prompt 3A defect where a disconnected `/mission-overview` modality still
// showed its last-confirmed waveform and the status strip could
// simultaneously read DISCONNECTED and "Replay state: Playing".
// ===========================================================================

{
  checkEqual(
    "telemetry availability: REST source_error takes precedence over everything else",
    deriveTelemetryAvailability({ connected: false, sourceStateStatus: "error", hasConfirmedSnapshot: true }),
    "source_error",
  );
  checkEqual(
    "telemetry availability F-01: WebSocket connected + retained snapshot + REST failure still fails closed",
    deriveTelemetryAvailability({ connected: true, sourceStateStatus: "error", hasConfirmedSnapshot: true }),
    "source_error",
  );
  checkEqual(
    "telemetry availability: transport disconnected (no REST error) -> disconnected",
    deriveTelemetryAvailability({ connected: false, sourceStateStatus: "available", hasConfirmedSnapshot: true }),
    "disconnected",
  );
  checkEqual(
    "telemetry availability: connected, no confirmed snapshot yet -> awaiting_confirmation",
    deriveTelemetryAvailability({ connected: true, sourceStateStatus: "available", hasConfirmedSnapshot: false }),
    "awaiting_confirmation",
  );
  checkEqual(
    "telemetry availability F-01: WebSocket frame cannot become current while authoritative REST state is still loading",
    deriveTelemetryAvailability({ connected: true, sourceStateStatus: "loading", hasConfirmedSnapshot: true }),
    "awaiting_confirmation",
  );
  checkEqual(
    "telemetry availability: connected + confirmed snapshot + no REST error -> active",
    deriveTelemetryAvailability({ connected: true, sourceStateStatus: "available", hasConfirmedSnapshot: true }),
    "active",
  );

  // §9 item 1 — active telemetry leaves an observation untouched (a real
  // confirmed PPG/IMU/ECG observation must still say so, unmodified).
  const activeObservation = deriveModalityObservation("PPG", {
    isReplay: true,
    channels: [fixtureChannelBatch({ channel_name: "wrist_bvp", units: "device units", samples: [1, 2, 3] })],
    availableChannels: ["wrist_bvp"],
    sensors: undefined,
  });
  checkEqual("telemetry gate: active telemetry does not modify the observation", applyTelemetryGate(activeObservation, "active"), activeObservation);
  check("telemetry gate: active observation legitimately says samples are available", activeObservation.statusLabel.includes("current samples available"));

  // §9 item 3 — disconnected must never say "current samples available".
  const disconnectedGated = applyTelemetryGate(activeObservation, "disconnected");
  checkNotIncludes("telemetry gate: disconnected observation never says 'current samples available'", disconnectedGated.statusLabel, "current samples available");
  checkEqual("telemetry gate: disconnected — exact required detail sentence", disconnectedGated.unavailableReason, "Source disconnected — no current samples");
  check("telemetry gate: disconnected observation carries no channel batch", disconnectedGated.channelBatch === null);

  const awaitingGated = applyTelemetryGate(activeObservation, "awaiting_confirmation");
  checkEqual("telemetry gate: awaiting_confirmation — exact required detail sentence", awaitingGated.unavailableReason, "Awaiting a confirmed frame from the selected source");

  // §9 item 6 — source_error must clear current observations exactly like disconnected.
  const sourceErrorGated = applyTelemetryGate(activeObservation, "source_error");
  checkEqual("telemetry gate: source_error — exact required detail sentence", sourceErrorGated.unavailableReason, "Source error — current samples unavailable");
  check("telemetry gate: source_error observation carries no channel batch (plot cannot be resolved from it)", sourceErrorGated.channelBatch === null);
  checkEqual(
    "telemetry gate: source_error clears the plot exactly like disconnected (resolvePlotSeries sees no channelBatch)",
    resolvePlotSeries("PPG", true, sourceErrorGated, undefined),
    null,
  );

  // §9 item 12 — a faulted modality must never render a normal waveform,
  // regardless of what the backend's channel payload still contained for
  // that fault type.
  const faultOverridden = applyFaultOverride(activeObservation, "PPG");
  checkEqual("fault override: state forced to unavailable even though the source observation was a confirmed replay channel", faultOverridden.state, "unavailable");
  checkNotIncludes("fault override: no stale clean statusLabel survives", faultOverridden.statusLabel, "current samples available");
  checkIncludes("fault override: exact required sentence names the modality", faultOverridden.unavailableReason ?? "", "Simulated PPG fault active — current input unavailable");
  check("fault override: channel batch cleared (no plot can be resolved)", faultOverridden.channelBatch === null);
  const imuFaultOverridden = applyFaultOverride(activeObservation, "IMU");
  checkIncludes("fault override F-01: IMU fault explicitly identifies unavailable IMU input", imuFaultOverridden.unavailableReason ?? "", "Simulated IMU fault");
  checkEqual("fault override F-01: IMU fault exposes no current channel batch", imuFaultOverridden.channelBatch, null);

  const rebuildingAvailability = derivePredictionAvailability({ connected: true, isReplay: true, prediction: null });
  const recoveredAvailability = derivePredictionAvailability({ connected: true, isReplay: true, prediction: fixturePrediction({ value: 71 }) });
  checkEqual("live F-01: rebuilding after fault clear has no current HR", rebuildingAvailability, "unavailable_no_prediction");
  checkEqual("live F-01: recovered valid PPG+IMU window restores HR availability", recoveredAvailability, "available");

  const retainedDataset = deriveIdentityContextDisplay({
    kind: "Dataset",
    telemetry: "source_error",
    currentValue: null,
    retainedValue: "FIXTURE_A",
  });
  checkEqual("live F-01: retained dataset is labeled as context", retainedDataset.label, "Dataset context");
  checkIncludes("live F-01: retained dataset says retained configuration", retainedDataset.value, "retained configuration");
  checkIncludes("live F-01: retained dataset explicitly says it is not current telemetry", retainedDataset.value, "not current telemetry");
  checkEqual("live F-01: retained dataset is marked retained", retainedDataset.retained, true);
  const awaitingDataset = deriveIdentityContextDisplay({ kind: "Dataset", telemetry: "awaiting_confirmation", currentValue: null, retainedValue: "FIXTURE_A" });
  checkEqual("live F-01: identity mismatch/awaiting state labels retained dataset as context", awaitingDataset.label, "Dataset context");
  checkIncludes("live F-01: identity mismatch/awaiting state cannot present retained dataset as current", awaitingDataset.value, "not current telemetry");
  const activeDataset = deriveIdentityContextDisplay({ kind: "Dataset", telemetry: "active", currentValue: "FIXTURE_A", retainedValue: "OLD" });
  checkEqual("live F-01: active identity uses current dataset, not retained value", activeDataset.value, "FIXTURE_A");
  checkEqual("live F-01: active identity is not marked retained", activeDataset.retained, false);
  checkEqual("live F-01: source_error availability copy never claims current HR", telemetryAvailabilityLabel("source_error"), "Source error — current samples unavailable");

  // §9 item 4 — the mission-status-strip replay-state field must never say
  // "Playing" while telemetry cannot be trusted, even though the raw
  // deriveReplaySessionState (fed a stale playbackState) would.
  checkEqual(
    "replay-state gate: disconnected overrides a stale 'playing' raw state",
    resolveReplayStateLabel({ telemetry: "disconnected", replaySessionState: "playing" }),
    "Unavailable — disconnected",
  );
  checkEqual(
    "replay-state gate: source_error overrides a stale 'playing' raw state",
    resolveReplayStateLabel({ telemetry: "source_error", replaySessionState: "playing" }),
    "Unavailable — source error",
  );
  checkEqual(
    "replay-state gate: awaiting_confirmation overrides a stale 'paused' raw state",
    resolveReplayStateLabel({ telemetry: "awaiting_confirmation", replaySessionState: "paused" }),
    "Awaiting source confirmation",
  );
  checkEqual(
    "replay-state gate: active telemetry passes the raw label through unmodified",
    resolveReplayStateLabel({ telemetry: "active", replaySessionState: "playing" }),
    "Playing",
  );
}

// ===========================================================================
// missionStore transport-disconnect clearing (Prompt 3A.1 §4.1 root-cause
// fix) — exercised directly against the real zustand store (its vanilla
// getState/setState/subscribe API works outside React), not a mock.
// ===========================================================================

{
  const fixtureSnapshotReplayS1 = fixtureSnapshot({
    timestamp: 1000,
    source: { source_type: "dataset_replay", subject_id: "FIXTURE_S1", dataset_name: "FIXTURE", available_channels: ["wrist_bvp"], playback_state: "playing" },
  });

  useMissionStore.setState({ latest: null, history: [], lastConfirmedTimestampSeconds: null, dataSourceStatus: null, connectionStatus: "connecting" });

  useMissionStore.getState().ingest(fixtureSnapshotReplayS1);
  check("missionStore: ingest sets latest", useMissionStore.getState().latest === fixtureSnapshotReplayS1);
  checkEqual("missionStore: ingest sets lastConfirmedTimestampSeconds", useMissionStore.getState().lastConfirmedTimestampSeconds, 1000);

  // §9 item 2 — a retained snapshot followed by a transport disconnect must
  // produce zero plots: this is the exact root-cause fix, at its source.
  useMissionStore.getState().setConnectionStatus("closed");
  check("missionStore: transport 'closed' clears latest immediately (root-cause fix)", useMissionStore.getState().latest === null);
  check("missionStore: transport 'closed' clears history", useMissionStore.getState().history.length === 0);
  // §9 item 14 — the historical frame-age timestamp explicitly survives.
  checkEqual("missionStore: lastConfirmedTimestampSeconds survives a transport disconnect (explicit historical-metadata exception)", useMissionStore.getState().lastConfirmedTimestampSeconds, 1000);

  // §9 item 10 — reconnection before a new confirmed frame remains empty.
  useMissionStore.getState().setConnectionStatus("connecting");
  check("missionStore: 'connecting' also keeps latest cleared", useMissionStore.getState().latest === null);
  useMissionStore.getState().setConnectionStatus("open");
  check("missionStore: reconnecting to 'open' does NOT resurrect the pre-disconnect snapshot", useMissionStore.getState().latest === null);

  // §9 item 11 — a new matching confirmed frame restores plots.
  const freshSnapshot = fixtureSnapshot({ timestamp: 2000, source: { source_type: "dataset_replay", subject_id: "FIXTURE_S1", dataset_name: "FIXTURE" } });
  useMissionStore.getState().ingest(freshSnapshot);
  check("missionStore: a fresh frame after reconnect restores latest", useMissionStore.getState().latest === freshSnapshot);

  // §9 items 7/8/9 — a source/subject identity change clears latest AND the
  // historical timestamp (a new session has no "last confirmed frame" of
  // its own yet), preventing S14's data from flashing under a new subject.
  useMissionStore.getState().setDataSourceStatus(fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "FIXTURE_S2", dataset_name: "FIXTURE" }));
  check("missionStore: an identity change (S1 -> S2) clears latest — no stale-subject flash", useMissionStore.getState().latest === null);
  check(
    "missionStore: an identity change also clears lastConfirmedTimestampSeconds — a new session has no prior 'last confirmed frame'",
    useMissionStore.getState().lastConfirmedTimestampSeconds === null,
  );

  // Reset to a clean slate so later test blocks are not affected by this store mutation.
  useMissionStore.setState({ latest: null, history: [], lastConfirmedTimestampSeconds: null, dataSourceStatus: null, connectionStatus: "connecting" });
}

// ===========================================================================
// Session-lifecycle integrity after disconnect (Prompt 3A.2 §4) — a source/
// subject/fault change performed AFTER a transport disconnect (when `latest`
// is already null) must still be recognized as a session transition and clear
// the historical last-confirmed timestamp. The store now falls back to the
// last `dataSourceStatus` to detect the change when `latest` is unavailable.
// ===========================================================================

{
  const statusA = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "PPG-DaLiA" });
  const snapshotA = fixtureSnapshot({ timestamp: 1000, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "PPG-DaLiA" } });

  function primeSessionA() {
    useMissionStore.setState({ latest: null, history: [], lastConfirmedTimestampSeconds: null, dataSourceStatus: null, connectionStatus: "connecting" });
    useMissionStore.getState().setDataSourceStatus(statusA); // authoritative identity A recorded
    useMissionStore.getState().ingest(snapshotA); // ts = 1000
    useMissionStore.getState().setConnectionStatus("closed"); // latest -> null; ts survives; dataSourceStatus still A
  }

  // Case 1 — ingest source A → disconnect → incoming status source B → ts clears.
  primeSessionA();
  useMissionStore.getState().setDataSourceStatus(fixtureDataSourceStatus({ source_type: "synthetic", subject_id: null, dataset_name: null }));
  checkEqual("lifecycle: source A → disconnect → source B status clears last-confirmed ts (falls back to dataSourceStatus)", useMissionStore.getState().lastConfirmedTimestampSeconds, null);

  // Case 2 — replay subject S14 → disconnect → different subject → ts clears.
  primeSessionA();
  useMissionStore.getState().setDataSourceStatus(fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S9", dataset_name: "PPG-DaLiA" }));
  checkEqual("lifecycle: replay S14 → disconnect → subject S9 status clears last-confirmed ts", useMissionStore.getState().lastConfirmedTimestampSeconds, null);

  // Case 3 — clean replay → disconnect → fault configuration change → ts clears.
  primeSessionA();
  useMissionStore
    .getState()
    .setDataSourceStatus(
      fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "PPG-DaLiA", fault_injection: fixtureFault({ active: true, target: "ppg", fault_type: "modality_dropout", severity: 1 }) }),
    );
  checkEqual("lifecycle: clean replay → disconnect → fault-config change clears last-confirmed ts", useMissionStore.getState().lastConfirmedTimestampSeconds, null);

  // Case 4 — same unchanged source A status after disconnect → ts remains.
  primeSessionA();
  useMissionStore.getState().setDataSourceStatus(fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "PPG-DaLiA" }));
  checkEqual("lifecycle: unchanged source A after disconnect preserves last-confirmed ts", useMissionStore.getState().lastConfirmedTimestampSeconds, 1000);

  // Case 5 — reconnect to the unchanged source without a new frame → no current telemetry.
  useMissionStore.getState().setConnectionStatus("open");
  check("lifecycle: reconnect to unchanged source without a new frame keeps latest empty (no current telemetry)", useMissionStore.getState().latest === null);

  // Case 6 — first matching post-reconnect frame → current telemetry resumes.
  const freshA = fixtureSnapshot({ timestamp: 2000, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "PPG-DaLiA" } });
  useMissionStore.getState().ingest(freshA);
  check("lifecycle: first matching frame after reconnect restores current telemetry", useMissionStore.getState().latest === freshA);

  // Prompt 3B §19 — a different DATASET with the same source_type + subject_id
  // must still be recognized as a session change and clear historical state.
  useMissionStore.setState({ latest: null, history: [], lastConfirmedTimestampSeconds: null, dataSourceStatus: null, connectionStatus: "connecting" });
  useMissionStore.getState().setDataSourceStatus(fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "PPG-DaLiA" }));
  useMissionStore.getState().ingest(fixtureSnapshot({ timestamp: 3000, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "PPG-DaLiA" } }));
  useMissionStore.getState().setConnectionStatus("closed");
  useMissionStore.getState().setDataSourceStatus(fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "OtherDataset" }));
  checkEqual("lifecycle 3B §19: same source_type+subject but a different dataset clears last-confirmed ts", useMissionStore.getState().lastConfirmedTimestampSeconds, null);

  // F-23 — history itself is segmented by the same canonical identity and a
  // late prior-dataset frame cannot repopulate the active session.
  const statusDatasetA = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "Dataset-A" });
  const statusDatasetB = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "Dataset-B" });
  const frameA1 = fixtureSnapshot({ timestamp: 10, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "Dataset-A" } });
  const frameA2 = fixtureSnapshot({ timestamp: 11, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "Dataset-A" } });
  const frameB = fixtureSnapshot({ timestamp: 20, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "Dataset-B" } });
  useMissionStore.setState({ latest: null, history: [], lastConfirmedTimestampSeconds: null, dataSourceStatus: null, connectionStatus: "open" });
  useMissionStore.getState().setDataSourceStatus(statusDatasetA);
  useMissionStore.getState().ingest(frameA1);
  useMissionStore.getState().ingest(frameA2);
  checkEqual("history F-23: same dataset/source/subject retains both frames", useMissionStore.getState().history.length, 2);
  useMissionStore.getState().setDataSourceStatus(statusDatasetA);
  checkEqual("history F-23: repeated authoritative identity preserves history", useMissionStore.getState().history.length, 2);
  useMissionStore.getState().setDataSourceStatus(statusDatasetB);
  checkEqual("history F-23: dataset change clears active history", useMissionStore.getState().history.length, 0);
  useMissionStore.getState().ingest(frameA2);
  checkEqual("history F-23: late frame from previous dataset is rejected", useMissionStore.getState().history.length, 0);
  checkEqual("history F-23: late frame from previous dataset cannot replace latest", useMissionStore.getState().latest, null);
  useMissionStore.getState().ingest(frameB);
  checkEqual("history F-23: first valid frame in new dataset starts distinct history", useMissionStore.getState().history.length, 1);
  checkEqual("history F-23: valid new-dataset frame becomes latest", useMissionStore.getState().latest, frameB);

  const unknownDatasetStatus = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: null });
  const literalUnknownFrame = fixtureSnapshot({ timestamp: 30, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "unconfirmed" } });
  useMissionStore.getState().setDataSourceStatus(unknownDatasetStatus);
  useMissionStore.getState().ingest(literalUnknownFrame);
  checkEqual("history F-23: missing dataset does not accept a real dataset named 'unconfirmed'", useMissionStore.getState().history.length, 0);

  useMissionStore.setState({
    latest: null,
    history: [],
    observedSourceIdentityKey: null,
    sourceConvergenceKey: null,
    sourceConvergenceBaseKey: null,
    sourceConvergenceSupersededKeys: [],
    retiredSourceIdentityKeys: [],
    lastConfirmedTimestampSeconds: null,
    dataSourceStatus: null,
    connectionStatus: "connecting",
  });
}

// ===========================================================================
// Corrective review residual 1 — complete A → observed B mismatch → REST B
// convergence. This exercises the real store plus the pure request planner.
// ===========================================================================

{
  const statusA = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "A" });
  const statusB = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "B" });
  const frameA1 = fixtureSnapshot({ timestamp: 100, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "A" } });
  const frameA2 = fixtureSnapshot({ timestamp: 150, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "A" } });
  const frameB1 = fixtureSnapshot({ timestamp: 200, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "B" } });
  const frameB2 = fixtureSnapshot({ timestamp: 201, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "B" } });
  const frameB3 = fixtureSnapshot({ timestamp: 202, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "B" } });

  useMissionStore.setState({
    latest: null,
    history: [],
    observedSourceIdentityKey: null,
    sourceConvergenceKey: null,
    sourceConvergenceBaseKey: null,
    sourceConvergenceSupersededKeys: [],
    retiredSourceIdentityKeys: [],
    lastConfirmedTimestampSeconds: null,
    dataSourceStatus: null,
    connectionStatus: "open",
  });
  useMissionStore.getState().setDataSourceStatus(statusA);
  useMissionStore.getState().ingest(frameA1);
  checkEqual("convergence residual 1: authoritative A frame becomes current", useMissionStore.getState().latest, frameA1);
  checkEqual("convergence residual 1: A history starts active", useMissionStore.getState().history.length, 1);

  useMissionStore.getState().ingest(frameB1);
  const mismatchKey = useMissionStore.getState().sourceConvergenceKey;
  checkEqual("convergence residual 1: observed B immediately clears stale A latest", useMissionStore.getState().latest, null);
  checkEqual("convergence residual 1: observed B immediately clears stale A current history", useMissionStore.getState().history.length, 0);
  checkEqual(
    "convergence residual 1: cleared current frame makes operational telemetry unavailable immediately",
    deriveTelemetryAvailability({
      connected: useMissionStore.getState().connectionStatus === "open",
      sourceStateStatus: "available",
      hasConfirmedSnapshot: useMissionStore.getState().latest !== null,
    }),
    "awaiting_confirmation",
  );
  check("convergence residual 1: observed B creates a convergence key", mismatchKey !== null);
  checkEqual("convergence residual 1: REST remains authoritative A until convergence", useMissionStore.getState().dataSourceStatus?.dataset_name, "A");

  let lastRequestedKey: string | null = null;
  let requestCount = 0;
  function consumePlan(key: string | null) {
    const plan = planSourceConvergenceRequest(key, lastRequestedKey);
    lastRequestedKey = plan.nextLastRequestedKey;
    if (plan.shouldRequest) requestCount += 1;
    return plan;
  }
  const firstPlan = consumePlan(mismatchKey);
  check("convergence residual 1: first observed B transition requests REST convergence", firstPlan.shouldRequest);
  checkEqual("convergence residual 1: exactly one request planned for first B identity", requestCount, 1);

  useMissionStore.getState().ingest(frameB2);
  const repeatedPlan = consumePlan(useMissionStore.getState().sourceConvergenceKey);
  checkEqual("convergence residual 1: repeated identical B frame is deduplicated", repeatedPlan.shouldRequest, false);
  checkEqual("convergence residual 1: repeated B frame does not increment request count", requestCount, 1);
  checkEqual("convergence residual 1: repeated B frame keeps current telemetry unavailable", useMissionStore.getState().latest, null);

  checkEqual("convergence residual 1: authoritative A does not confirm pending B", statusConfirmsSourceConvergence(statusA, mismatchKey), false);
  useMissionStore.getState().setDataSourceStatus(statusA);
  checkEqual("convergence residual 1: unsuccessful convergence does not restore stale A", useMissionStore.getState().latest, null);
  checkEqual("convergence residual 1: unsuccessful convergence keeps history empty", useMissionStore.getState().history.length, 0);
  checkEqual("convergence residual 1: unsuccessful convergence retains pending B key without retry loop", useMissionStore.getState().sourceConvergenceKey, mismatchKey);
  check("event ordering A: unchanged REST A retains the pre-convergence authority record", useMissionStore.getState().sourceConvergenceBaseKey !== null);
  consumePlan(useMissionStore.getState().sourceConvergenceKey);
  checkEqual("convergence residual 1: unchanged failed convergence does not create a request loop", requestCount, 1);

  // Second independent review: an old-authoritative A frame after failed B
  // convergence must not cross the shared pending boundary on legacy routes.
  useMissionStore.getState().ingest(frameA2);
  const pendingAfterOldFrame = useMissionStore.getState();
  checkEqual("cross-route convergence: old-authoritative A2 is rejected while B remains pending", pendingAfterOldFrame.latest, null);
  checkEqual("cross-route convergence: rejected A2 cannot repopulate current history", pendingAfterOldFrame.history.length, 0);
  checkEqual("cross-route convergence: rejected A2 cannot advance last-confirmed timestamp", pendingAfterOldFrame.lastConfirmedTimestampSeconds, 100);
  checkEqual("cross-route convergence: rejected A2 cannot replace pending B identity", pendingAfterOldFrame.sourceConvergenceKey, mismatchKey);
  checkEqual("cross-route convergence: rejected A2 keeps observed convergence target on B", pendingAfterOldFrame.observedSourceIdentityKey, mismatchKey);
  const confirmedWhilePending = confirmedSnapshotForState(
    pendingAfterOldFrame.latest,
    pendingAfterOldFrame.dataSourceStatus,
    pendingAfterOldFrame.sourceConvergenceKey,
  );
  checkEqual("cross-route convergence: confirmed-snapshot boundary exposes no A2 while B is pending", confirmedWhilePending.snapshot, null);
  checkEqual("cross-route convergence: confirmed-snapshot boundary reports pending confirmation", confirmedWhilePending.isWaitingForConfirmation, true);
  checkEqual(
    "cross-route convergence: confirmed-history boundary exposes no A history while B is pending",
    confirmedHistoryForState(
      pendingAfterOldFrame.history,
      pendingAfterOldFrame.dataSourceStatus,
      pendingAfterOldFrame.sourceConvergenceKey,
    ).length,
    0,
  );
  const defensiveSnapshotGate = confirmedSnapshotForState(frameA2, statusA, mismatchKey);
  checkEqual("cross-route convergence: selector defense-in-depth withholds matching stale A residue while B is pending", defensiveSnapshotGate.snapshot, null);
  checkEqual("cross-route convergence: selector defense-in-depth identifies pending confirmation despite stale residue", defensiveSnapshotGate.isWaitingForConfirmation, true);
  checkEqual(
    "cross-route convergence: history selector defense-in-depth withholds matching stale A residue while B is pending",
    confirmedHistoryForState([frameA1, frameA2], statusA, mismatchKey).length,
    0,
  );
  consumePlan(pendingAfterOldFrame.sourceConvergenceKey);
  checkEqual("cross-route convergence: repeated old A frame does not plan another convergence request", requestCount, 1);

  useMissionStore.getState().ingest(frameB2);
  checkEqual("cross-route convergence: repeated pending B frame stays unavailable", useMissionStore.getState().latest, null);
  checkEqual("cross-route convergence: repeated pending B frame does not advance confirmed timestamp", useMissionStore.getState().lastConfirmedTimestampSeconds, 100);
  consumePlan(useMissionStore.getState().sourceConvergenceKey);
  checkEqual("cross-route convergence: repeated pending B frame remains request-deduplicated", requestCount, 1);

  checkEqual("convergence residual 1: authoritative B confirms pending B", statusConfirmsSourceConvergence(statusB, mismatchKey), true);
  useMissionStore.getState().setDataSourceStatus(statusB);
  checkEqual("convergence residual 1: confirmed REST B clears pending convergence key", useMissionStore.getState().sourceConvergenceKey, null);
  checkEqual("event ordering A: confirmed REST B clears the pre-convergence authority record", useMissionStore.getState().sourceConvergenceBaseKey, null);
  const clearedPlan = consumePlan(useMissionStore.getState().sourceConvergenceKey);
  checkEqual("convergence residual 1: clearing convergence does not issue another request", clearedPlan.shouldRequest, false);
  checkEqual("convergence residual 1: clearing convergence resets dedupe boundary", lastRequestedKey, null);

  useMissionStore.getState().ingest(frameB3);
  checkEqual("convergence residual 1: valid B frame recovers current telemetry", useMissionStore.getState().latest, frameB3);
  checkEqual("convergence residual 1: recovered history contains one B frame", useMissionStore.getState().history.length, 1);
  check("convergence residual 1: recovered history contains only dataset B", useMissionStore.getState().history.every((frame) => frame.source.dataset_name === "B"));
  const recoveredState = useMissionStore.getState();
  checkEqual(
    "cross-route convergence: confirmed-snapshot boundary recovers with authoritative B3",
    confirmedSnapshotForState(recoveredState.latest, recoveredState.dataSourceStatus, recoveredState.sourceConvergenceKey).snapshot,
    frameB3,
  );
  checkEqual(
    "cross-route convergence: confirmed-history boundary recovers with B-only history",
    confirmedHistoryForState(recoveredState.history, recoveredState.dataSourceStatus, recoveredState.sourceConvergenceKey).length,
    1,
  );
  checkEqual("convergence residual 1: normal accepted B traffic has no convergence trigger", useMissionStore.getState().sourceConvergenceKey, null);
  consumePlan(useMissionStore.getState().sourceConvergenceKey);
  checkEqual("convergence residual 1: normal stream traffic does not poll", requestCount, 1);

  useMissionStore.setState({
    latest: null,
    history: [],
    observedSourceIdentityKey: null,
    sourceConvergenceKey: null,
    sourceConvergenceBaseKey: null,
    sourceConvergenceSupersededKeys: [],
    retiredSourceIdentityKeys: [],
    lastConfirmedTimestampSeconds: null,
    dataSourceStatus: null,
    connectionStatus: "connecting",
  });
}

// A genuinely new mismatch identity replaces the pending target exactly once;
// pre-REST provisional startup remains unchanged.
{
  const statusA = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "A" });
  const frameA1 = fixtureSnapshot({ timestamp: 300, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "A" } });
  const frameB1 = fixtureSnapshot({ timestamp: 400, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "B" } });
  const frameC1 = fixtureSnapshot({ timestamp: 500, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "C" } });
  const frameC2 = fixtureSnapshot({ timestamp: 501, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "C" } });

  useMissionStore.setState({
    latest: null,
    history: [],
    observedSourceIdentityKey: null,
    sourceConvergenceKey: null,
    sourceConvergenceBaseKey: null,
    sourceConvergenceSupersededKeys: [],
    retiredSourceIdentityKeys: [],
    lastConfirmedTimestampSeconds: null,
    dataSourceStatus: null,
    connectionStatus: "open",
  });
  useMissionStore.getState().setDataSourceStatus(statusA);
  useMissionStore.getState().ingest(frameA1);
  useMissionStore.getState().ingest(frameB1);

  let lastRequestedKey: string | null = null;
  let requestCount = 0;
  function consumePlan(key: string | null) {
    const plan = planSourceConvergenceRequest(key, lastRequestedKey);
    lastRequestedKey = plan.nextLastRequestedKey;
    if (plan.shouldRequest) requestCount += 1;
    return plan;
  }
  const pendingB = useMissionStore.getState().sourceConvergenceKey;
  consumePlan(pendingB);
  checkEqual("cross-route convergence: initial B mismatch plans exactly one request", requestCount, 1);

  useMissionStore.getState().ingest(frameC1);
  const pendingC = useMissionStore.getState().sourceConvergenceKey;
  check("cross-route convergence: new mismatched C replaces pending B", pendingC !== null && pendingC !== pendingB);
  checkEqual("cross-route convergence: C replacement remains fail-closed", useMissionStore.getState().latest, null);
  checkEqual("cross-route convergence: C replacement does not advance confirmed timestamp", useMissionStore.getState().lastConfirmedTimestampSeconds, 300);
  consumePlan(pendingC);
  checkEqual("cross-route convergence: new C identity plans one additional request", requestCount, 2);

  useMissionStore.getState().ingest(frameC2);
  consumePlan(useMissionStore.getState().sourceConvergenceKey);
  checkEqual("cross-route convergence: repeated C remains request-deduplicated", requestCount, 2);
  checkEqual("cross-route convergence: repeated C remains unavailable", useMissionStore.getState().latest, null);
  checkEqual("cross-route convergence: repeated C cannot advance confirmed timestamp", useMissionStore.getState().lastConfirmedTimestampSeconds, 300);

  useMissionStore.getState().ingest(frameB1);
  consumePlan(useMissionStore.getState().sourceConvergenceKey);
  checkEqual("cross-route convergence: superseded B cannot replace newer pending C", useMissionStore.getState().sourceConvergenceKey, pendingC);
  checkEqual("cross-route convergence: late superseded B creates no request loop", requestCount, 2);
  checkEqual("cross-route convergence: late superseded B remains fail-closed", useMissionStore.getState().latest, null);

  useMissionStore.setState({
    latest: null,
    history: [],
    observedSourceIdentityKey: null,
    sourceConvergenceKey: null,
    sourceConvergenceBaseKey: null,
    sourceConvergenceSupersededKeys: [],
    retiredSourceIdentityKeys: [],
    lastConfirmedTimestampSeconds: null,
    dataSourceStatus: null,
    connectionStatus: "open",
  });
  const provisionalFrame = fixtureSnapshot({ timestamp: 600, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "STARTUP" } });
  useMissionStore.getState().ingest(provisionalFrame);
  const provisionalState = useMissionStore.getState();
  checkEqual("cross-route convergence: pre-REST startup still accepts provisional telemetry", provisionalState.latest, provisionalFrame);
  checkEqual("cross-route convergence: pre-REST startup begins provisional history", provisionalState.history.length, 1);
  checkEqual("cross-route convergence: pre-REST provisional frame advances confirmed timestamp", provisionalState.lastConfirmedTimestampSeconds, 600);
  checkEqual(
    "cross-route convergence: confirmed-snapshot helper preserves pre-REST provisional contract",
    confirmedSnapshotForState(provisionalState.latest, provisionalState.dataSourceStatus, provisionalState.sourceConvergenceKey).snapshot,
    provisionalFrame,
  );
  checkEqual(
    "cross-route convergence: confirmed-history helper preserves pre-REST provisional contract",
    confirmedHistoryForState(provisionalState.history, provisionalState.dataSourceStatus, provisionalState.sourceConvergenceKey).length,
    1,
  );

  useMissionStore.setState({
    latest: null,
    history: [],
    observedSourceIdentityKey: null,
    sourceConvergenceKey: null,
    sourceConvergenceBaseKey: null,
    sourceConvergenceSupersededKeys: [],
    retiredSourceIdentityKeys: [],
    lastConfirmedTimestampSeconds: null,
    dataSourceStatus: null,
    connectionStatus: "connecting",
  });
}

// ===========================================================================
// Third independent review — authoritative A/B/C transition semantics.
// ===========================================================================

{
  const statusA = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "A" });
  const statusB = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "B" });
  const statusC = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "C" });
  const pendingB = "pending-B";
  const fullOwner = "full-owner";
  const legacyOwner = "legacy-owner";

  function deferred<T>() {
    let resolve!: (value: T) => void;
    let reject!: (reason?: unknown) => void;
    const promise = new Promise<T>((resolvePromise, rejectPromise) => {
      resolve = resolvePromise;
      reject = rejectPromise;
    });
    return { promise, resolve, reject };
  }

  const seedCoordinator = new SourceStateRequestCoordinator();
  const seedOwner = "seed-owner";
  const seedResponse = deferred<DataSourceStatus>();
  let seedRequests = 0;
  let seedAccepted = 0;
  seedCoordinator.activateOwner(seedOwner);
  const seedRegistration = seedCoordinator.startOrAdoptRequest(
    seedOwner,
    null,
    () => {
      seedRequests += 1;
      return seedResponse.promise;
    },
    () => {
      seedAccepted += 1;
    },
    () => undefined,
  );
  const repeatedSeedRegistration = seedCoordinator.startOrAdoptRequest(
    seedOwner,
    null,
    () => {
      seedRequests += 1;
      return seedResponse.promise;
    },
    () => {
      seedAccepted += 1;
    },
    () => undefined,
  );
  checkEqual("request ordering B: owner without pending starts an initial seed", seedRegistration?.reason, "initial_seed");
  checkEqual("request ordering B: owner without pending starts exactly one request", seedRequests, 1);
  checkEqual("request ordering B: repeated seed registration adopts physical request", repeatedSeedRegistration?.adopted, true);
  seedResponse.resolve(statusA);
  checkEqual("request ordering B: adopted seed result is accepted", await repeatedSeedRegistration?.outcome, "accepted");
  checkEqual("request ordering B: adopted seed invokes one active callback", seedAccepted, 1);

  const pendingCoordinator = new SourceStateRequestCoordinator();
  const pendingOwner = "pending-owner";
  const pendingResponse = deferred<DataSourceStatus>();
  let pendingRequests = 0;
  pendingCoordinator.activateOwner(pendingOwner);
  const pendingRegistration = pendingCoordinator.startOrAdoptRequest(
    pendingOwner,
    pendingB,
    () => {
      pendingRequests += 1;
      return pendingResponse.promise;
    },
    () => undefined,
    () => undefined,
  );
  const repeatedPendingRegistration = pendingCoordinator.startOrAdoptRequest(
    pendingOwner,
    pendingB,
    () => {
      pendingRequests += 1;
      return pendingResponse.promise;
    },
    () => undefined,
    () => undefined,
  );
  checkEqual("request ordering B: owner starting with pending B requests convergence, not seed", pendingRegistration?.reason, "convergence");
  checkEqual("request ordering B: pending B mount starts exactly one total request", pendingRequests, 1);
  checkEqual("request ordering B: repeated B frame while request is in flight stays single-flight", repeatedPendingRegistration?.adopted, true);
  pendingResponse.resolve(statusB);
  await repeatedPendingRegistration?.outcome;

  const strictCoordinator = new SourceStateRequestCoordinator();
  const strictOwner = "strict-owner";
  const strictResponse = deferred<DataSourceStatus>();
  let strictRequests = 0;
  let strictOldCallbacks = 0;
  let strictActiveCallbacks = 0;
  strictCoordinator.activateOwner(strictOwner);
  const strictOriginal = strictCoordinator.startOrAdoptRequest(
    strictOwner,
    null,
    () => {
      strictRequests += 1;
      return strictResponse.promise;
    },
    () => {
      strictOldCallbacks += 1;
    },
    () => undefined,
  );
  strictCoordinator.releaseOwner(strictOwner);
  strictCoordinator.activateOwner(strictOwner);
  const strictReplay = strictCoordinator.startOrAdoptRequest(
    strictOwner,
    null,
    () => {
      strictRequests += 1;
      return strictResponse.promise;
    },
    () => {
      strictActiveCallbacks += 1;
    },
    () => undefined,
  );
  checkEqual("request ordering B: Strict Mode same-owner replay does not duplicate initial seed", strictRequests, 1);
  checkEqual("request ordering B: same-owner reactivation adopts original physical request", strictReplay?.adopted, true);
  strictResponse.resolve(statusA);
  checkEqual("request ordering B: Strict Mode destination receives adopted result", await strictReplay?.outcome, "accepted");
  checkEqual("request ordering B: Strict Mode original registration becomes stale", await strictOriginal?.outcome, "stale");
  checkEqual("request ordering B: Strict Mode result is accepted exactly once", strictActiveCallbacks, 1);
  checkEqual("request ordering B: Strict Mode superseded callback is blocked", strictOldCallbacks, 0);

  async function verifySameKeyTransfer(
    fromOwner: string,
    toOwner: string,
    direction: "full-to-legacy" | "legacy-to-full",
  ) {
    const coordinator = new SourceStateRequestCoordinator();
    const response = deferred<DataSourceStatus>();
    let physicalRequests = 0;
    let oldCallbacks = 0;
    let destinationCallbacks = 0;
    coordinator.activateOwner(fromOwner);
    const original = coordinator.startOrAdoptRequest(
      fromOwner,
      pendingB,
      () => {
        physicalRequests += 1;
        return response.promise;
      },
      () => {
        oldCallbacks += 1;
      },
      () => undefined,
    );
    coordinator.releaseOwner(fromOwner);
    coordinator.activateOwner(toOwner);
    const adopted = coordinator.startOrAdoptRequest(
      toOwner,
      pendingB,
      () => {
        physicalRequests += 1;
        return response.promise;
      },
      (result) => {
        if (result.dataset_name === "B") destinationCallbacks += 1;
      },
      () => undefined,
    );
    checkEqual(`request ordering B: ${direction} transfer reuses one physical request`, physicalRequests, 1);
    checkEqual(`request ordering B: ${direction} destination adopts unresolved B`, adopted?.adopted, true);
    response.resolve(statusB);
    checkEqual(`request ordering B: ${direction} destination accepts B`, await adopted?.outcome, "accepted");
    checkEqual(`request ordering B: ${direction} old registration is stale`, await original?.outcome, "stale");
    checkEqual(`request ordering B: ${direction} destination callback runs once`, destinationCallbacks, 1);
    checkEqual(`request ordering B: ${direction} superseded callbacks do not run`, oldCallbacks, 0);
  }

  await verifySameKeyTransfer(fullOwner, legacyOwner, "full-to-legacy");
  await verifySameKeyTransfer(legacyOwner, fullOwner, "legacy-to-full");

  const transferredSeedCoordinator = new SourceStateRequestCoordinator();
  const transferredSeedResponse = deferred<DataSourceStatus>();
  let transferredSeedRequests = 0;
  let transferredSeedOldCallbacks = 0;
  let transferredSeedDestinationCallbacks = 0;
  transferredSeedCoordinator.activateOwner(fullOwner);
  const transferredSeedOriginal = transferredSeedCoordinator.startOrAdoptRequest(
    fullOwner,
    null,
    () => {
      transferredSeedRequests += 1;
      return transferredSeedResponse.promise;
    },
    () => {
      transferredSeedOldCallbacks += 1;
    },
    () => undefined,
  );
  transferredSeedCoordinator.releaseOwner(fullOwner);
  transferredSeedCoordinator.activateOwner(legacyOwner);
  const transferredSeedAdoption = transferredSeedCoordinator.startOrAdoptRequest(
    legacyOwner,
    null,
    () => {
      transferredSeedRequests += 1;
      return transferredSeedResponse.promise;
    },
    () => {
      transferredSeedDestinationCallbacks += 1;
    },
    () => undefined,
  );
  checkEqual("request ordering B: initial-seed transfer keeps one physical request", transferredSeedRequests, 1);
  checkEqual("request ordering B: initial-seed destination adopts unresolved request", transferredSeedAdoption?.adopted, true);
  transferredSeedResponse.resolve(statusA);
  checkEqual("request ordering B: initial-seed destination accepts result", await transferredSeedAdoption?.outcome, "accepted");
  checkEqual("request ordering B: initial-seed old registration is stale", await transferredSeedOriginal?.outcome, "stale");
  checkEqual("request ordering B: initial-seed destination callback runs once", transferredSeedDestinationCallbacks, 1);
  checkEqual("request ordering B: initial-seed old callback does not run", transferredSeedOldCallbacks, 0);

  const settlementGapCoordinator = new SourceStateRequestCoordinator();
  const settlementGapResponse = deferred<DataSourceStatus>();
  let settlementGapRequests = 0;
  let settlementGapOldCallbacks = 0;
  let settlementGapDestinationCallbacks = 0;
  settlementGapCoordinator.activateOwner(fullOwner);
  const settlementGapOriginal = settlementGapCoordinator.startOrAdoptRequest(
    fullOwner,
    pendingB,
    () => {
      settlementGapRequests += 1;
      return settlementGapResponse.promise;
    },
    () => {
      settlementGapOldCallbacks += 1;
    },
    () => undefined,
  );
  settlementGapCoordinator.releaseOwner(fullOwner);
  settlementGapResponse.resolve(statusB);
  await Promise.resolve();
  settlementGapCoordinator.activateOwner(legacyOwner);
  const settlementGapAdoption = settlementGapCoordinator.startOrAdoptRequest(
    legacyOwner,
    pendingB,
    () => {
      settlementGapRequests += 1;
      return settlementGapResponse.promise;
    },
    () => {
      settlementGapDestinationCallbacks += 1;
    },
    () => undefined,
  );
  checkEqual("request ordering B: settlement during owner gap remains one physical request", settlementGapRequests, 1);
  checkEqual("request ordering B: destination adopts result settled during owner gap", settlementGapAdoption?.adopted, true);
  checkEqual("request ordering B: owner-gap adopted result is accepted", await settlementGapAdoption?.outcome, "accepted");
  checkEqual("request ordering B: owner-gap original registration is stale", await settlementGapOriginal?.outcome, "stale");
  checkEqual("request ordering B: owner-gap destination callback runs once", settlementGapDestinationCallbacks, 1);
  checkEqual("request ordering B: owner-gap superseded callback stays blocked", settlementGapOldCallbacks, 0);

  const unmountedCoordinator = new SourceStateRequestCoordinator();
  const unmountedOwner = "unmounted-owner";
  const unmountedResponse = deferred<DataSourceStatus>();
  let unmountedRequests = 0;
  let unmountedWrites = 0;
  unmountedCoordinator.activateOwner(unmountedOwner);
  const unmountedRegistration = unmountedCoordinator.startOrAdoptRequest(
    unmountedOwner,
    pendingB,
    () => {
      unmountedRequests += 1;
      return unmountedResponse.promise;
    },
    () => {
      unmountedWrites += 1;
    },
    () => {
      unmountedWrites += 1;
    },
  );
  unmountedCoordinator.releaseOwner(unmountedOwner);
  unmountedResponse.resolve(statusB);
  checkEqual("request ordering B: no-replacement request factory runs once", unmountedRequests, 1);
  checkEqual("request ordering B: unmounted owner response is stale", await unmountedRegistration?.outcome, "stale");
  checkEqual("request ordering B: unmounted owner cannot write", unmountedWrites, 0);
  const frameA1 = fixtureSnapshot({ timestamp: 700, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "A" } });
  const frameB1 = fixtureSnapshot({ timestamp: 800, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "B" } });
  const frameC1 = fixtureSnapshot({ timestamp: 900, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "C" } });
  const lateA2 = fixtureSnapshot({ timestamp: 701, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "A" } });

  const identityA = sourceIdentityFromStatus(statusA);
  const identityB = sourceIdentityFromStatus(statusB);
  check("event ordering A: fixture identities are available", identityA !== null && identityB !== null);
  const keyA = identityA ? sourceIdentityKey(identityA) : null;
  const keyB = identityB ? sourceIdentityKey(identityB) : null;

  useMissionStore.setState({
    latest: null,
    history: [],
    observedSourceIdentityKey: null,
    sourceConvergenceKey: null,
    sourceConvergenceBaseKey: null,
    sourceConvergenceSupersededKeys: [],
    retiredSourceIdentityKeys: [],
    lastConfirmedTimestampSeconds: null,
    dataSourceStatus: null,
    connectionStatus: "open",
  });
  useMissionStore.getState().setDataSourceStatus(statusA);
  useMissionStore.getState().ingest(frameA1);
  useMissionStore.getState().ingest(frameB1);
  checkEqual("event ordering A: B frame opens pending B", useMissionStore.getState().sourceConvergenceKey, keyB);
  checkEqual("event ordering A: convergence records pre-transition authority A", useMissionStore.getState().sourceConvergenceBaseKey, keyA);
  checkEqual(
    "event ordering A: unchanged REST A is classified separately from third authority",
    classifySourceConvergenceStatus(statusA, keyB, keyA),
    "unchanged_pre_convergence_authority",
  );
  checkEqual(
    "event ordering A: REST B confirms pending B",
    classifySourceConvergenceStatus(statusB, keyB, keyA),
    "confirmed_pending_identity",
  );
  checkEqual(
    "event ordering A: REST C is a third authoritative transition",
    classifySourceConvergenceStatus(statusC, keyB, keyA),
    "advanced_to_third_authority",
  );

  useMissionStore.getState().setDataSourceStatus(statusC);
  checkEqual("event ordering A: REST C clears obsolete pending B", useMissionStore.getState().sourceConvergenceKey, null);
  checkEqual("event ordering A: REST C clears the completed transition base", useMissionStore.getState().sourceConvergenceBaseKey, null);
  checkEqual("event ordering A: REST C becomes authoritative", useMissionStore.getState().dataSourceStatus?.dataset_name, "C");
  checkEqual("event ordering A: REST C restores no stale A latest", useMissionStore.getState().latest, null);
  checkEqual("event ordering A: REST C restores no speculative B history", useMissionStore.getState().history.length, 0);
  check("event ordering A: pre-convergence A is recorded as retired", keyA !== null && useMissionStore.getState().retiredSourceIdentityKeys.includes(keyA));
  check("event ordering A: abandoned speculative B is recorded as retired", keyB !== null && useMissionStore.getState().retiredSourceIdentityKeys.includes(keyB));

  let lastRequestedKey: string | null = null;
  let requestCount = 0;
  const firstBPlan = planSourceConvergenceRequest(keyB, lastRequestedKey);
  lastRequestedKey = firstBPlan.nextLastRequestedKey;
  if (firstBPlan.shouldRequest) requestCount += 1;
  const clearedPlan = planSourceConvergenceRequest(useMissionStore.getState().sourceConvergenceKey, lastRequestedKey);
  if (clearedPlan.shouldRequest) requestCount += 1;
  checkEqual("event ordering A: REST C resolution opens no redundant convergence request", requestCount, 1);

  useMissionStore.getState().ingest(frameC1);
  checkEqual("event ordering A: first valid C frame recovers current telemetry", useMissionStore.getState().latest, frameC1);
  checkEqual("event ordering A: recovered history contains one C frame", useMissionStore.getState().history.length, 1);
  check("event ordering A: recovered history contains only C", useMissionStore.getState().history.every((frame) => frame.source.dataset_name === "C"));
  checkEqual("event ordering A: C recovery does not reopen pending convergence", useMissionStore.getState().sourceConvergenceKey, null);

  useMissionStore.getState().ingest(lateA2);
  checkEqual("event ordering A: retired late A cannot overwrite current C", useMissionStore.getState().latest, frameC1);
  check("event ordering A: retired late A cannot enter C history", useMissionStore.getState().history.every((frame) => frame.source.dataset_name === "C"));
  checkEqual("event ordering A: retired late A cannot reopen stale convergence", useMissionStore.getState().sourceConvergenceKey, null);
  checkEqual("event ordering A: retired late A cannot advance confirmed timestamp", useMissionStore.getState().lastConfirmedTimestampSeconds, 900);

  useMissionStore.setState({
    latest: null,
    history: [],
    observedSourceIdentityKey: null,
    sourceConvergenceKey: null,
    sourceConvergenceBaseKey: null,
    sourceConvergenceSupersededKeys: [],
    retiredSourceIdentityKeys: [],
    lastConfirmedTimestampSeconds: null,
    dataSourceStatus: null,
    connectionStatus: "connecting",
  });
}

// ===========================================================================
// Third independent review — shared request ownership/generation controller.
// ===========================================================================

{
  const pendingB = "pending-B";
  const pendingC = "pending-C";
  const fullOwner = "full-owner";
  const legacyOwner = "legacy-owner";

  function deferred<T>() {
    let resolve!: (value: T) => void;
    let reject!: (reason?: unknown) => void;
    const promise = new Promise<T>((resolvePromise, rejectPromise) => {
      resolve = resolvePromise;
      reject = rejectPromise;
    });
    return { promise, resolve, reject };
  }

  const statusA = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "A" });
  const statusB = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "B" });
  const statusC = fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14", dataset_name: "C" });

  useMissionStore.setState({
    latest: null,
    history: [],
    observedSourceIdentityKey: null,
    sourceConvergenceKey: null,
    sourceConvergenceBaseKey: null,
    sourceConvergenceSupersededKeys: [],
    retiredSourceIdentityKeys: [],
    lastConfirmedTimestampSeconds: null,
    dataSourceStatus: null,
    connectionStatus: "open",
  });
  useMissionStore.getState().setDataSourceStatus(statusA);
  useMissionStore.getState().ingest(fixtureSnapshot({ timestamp: 1000, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "A" } }));
  useMissionStore.getState().ingest(fixtureSnapshot({ timestamp: 1100, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "B" } }));
  const realPendingB = useMissionStore.getState().sourceConvergenceKey;
  check("request ordering B: real store provides pending B for response-order test", realPendingB !== null);

  const outOfOrder = new SourceStateRequestCoordinator();
  const orderOwner = "order-owner";
  outOfOrder.activateOwner(orderOwner);
  const olderResponse = deferred<DataSourceStatus>();
  let acceptedAuthority: string | null = null;
  let acceptedWrites = 0;
  let outOfOrderRequests = 0;
  const olderRegistration = outOfOrder.startOrAdoptRequest(
    orderOwner,
    null,
    () => {
      outOfOrderRequests += 1;
      return olderResponse.promise;
    },
    (result) => {
      acceptedAuthority = result.dataset_name;
      acceptedWrites += 1;
      useMissionStore.getState().setDataSourceStatus(result);
    },
    () => undefined,
  );
  const newerResponse = deferred<DataSourceStatus>();
  const newerRegistration = outOfOrder.startOrAdoptRequest(
    orderOwner,
    realPendingB,
    () => {
      outOfOrderRequests += 1;
      return newerResponse.promise;
    },
    (result) => {
      acceptedAuthority = result.dataset_name;
      acceptedWrites += 1;
      useMissionStore.getState().setDataSourceStatus(result);
    },
    () => undefined,
  );
  checkEqual("request ordering B: A to B creates exactly two distinct physical requests", outOfOrderRequests, 2);
  newerResponse.resolve(statusB);
  checkEqual("request ordering B: newer B response is accepted", await newerRegistration?.outcome, "accepted");
  checkEqual("request ordering B: newer B becomes accepted authority", acceptedAuthority, "B");
  checkEqual("request ordering B: newer B updates the real authoritative store", useMissionStore.getState().dataSourceStatus?.dataset_name, "B");
  checkEqual("request ordering B: newer B clears real pending convergence", useMissionStore.getState().sourceConvergenceKey, null);
  olderResponse.resolve(statusA);
  checkEqual("request ordering B: older A resolving after B is rejected as stale", await olderRegistration?.outcome, "stale");
  checkEqual("request ordering B: stale older A cannot roll authority backward", acceptedAuthority, "B");
  checkEqual("request ordering B: stale older A cannot roll real store backward", useMissionStore.getState().dataSourceStatus?.dataset_name, "B");
  checkEqual("request ordering B: out-of-order pair produces one authoritative write", acceptedWrites, 1);

  const inverseOrder = new SourceStateRequestCoordinator();
  inverseOrder.activateOwner(orderOwner);
  const inverseOlderResponse = deferred<DataSourceStatus>();
  let inverseAuthority: string | null = null;
  let inverseRequests = 0;
  const inverseOlderRegistration = inverseOrder.startOrAdoptRequest(
    orderOwner,
    null,
    () => {
      inverseRequests += 1;
      return inverseOlderResponse.promise;
    },
    (result) => {
      inverseAuthority = result.dataset_name;
    },
    () => undefined,
  );
  const inverseNewerResponse = deferred<DataSourceStatus>();
  const inverseNewerRegistration = inverseOrder.startOrAdoptRequest(
    orderOwner,
    pendingC,
    () => {
      inverseRequests += 1;
      return inverseNewerResponse.promise;
    },
    (result) => {
      inverseAuthority = result.dataset_name;
    },
    () => undefined,
  );
  checkEqual("request ordering B: inverse A to C creates one physical request per identity", inverseRequests, 2);
  inverseOlderResponse.resolve(statusA);
  checkEqual("request ordering B: superseded A is stale even when it resolves first", await inverseOlderRegistration?.outcome, "stale");
  checkEqual("request ordering B: early stale A performs no write", inverseAuthority, null);
  inverseNewerResponse.resolve(statusC);
  checkEqual("request ordering B: newer C is accepted after early stale A", await inverseNewerRegistration?.outcome, "accepted");
  checkEqual("request ordering B: inverse completion order ends at C", inverseAuthority, "C");

  const supersededCoordinator = new SourceStateRequestCoordinator();
  supersededCoordinator.activateOwner(fullOwner);
  const oldOwnerResponse = deferred<DataSourceStatus>();
  let supersededAuthority: string | null = null;
  let supersededRequests = 0;
  let supersededOldCallbacks = 0;
  const oldOwnerRegistration = supersededCoordinator.startOrAdoptRequest(
    fullOwner,
    pendingB,
    () => {
      supersededRequests += 1;
      return oldOwnerResponse.promise;
    },
    () => {
      supersededOldCallbacks += 1;
    },
    () => undefined,
  );
  supersededCoordinator.releaseOwner(fullOwner);
  supersededCoordinator.activateOwner(legacyOwner);
  const newOwnerResponse = deferred<DataSourceStatus>();
  const newOwnerRegistration = supersededCoordinator.startOrAdoptRequest(
    legacyOwner,
    pendingC,
    () => {
      supersededRequests += 1;
      return newOwnerResponse.promise;
    },
    (result) => {
      supersededAuthority = result.dataset_name;
    },
    () => undefined,
  );
  checkEqual("request ordering B: B-to-C transfer starts exactly one request for each identity", supersededRequests, 2);
  checkEqual("request ordering B: B-to-C destination starts rather than adopts C", newOwnerRegistration?.adopted, false);
  newOwnerResponse.resolve(statusC);
  checkEqual("request ordering B: replacement owner accepts C", await newOwnerRegistration?.outcome, "accepted");
  oldOwnerResponse.resolve(statusA);
  checkEqual("request ordering B: superseded owner's later A response is stale", await oldOwnerRegistration?.outcome, "stale");
  checkEqual("request ordering B: superseded owner cannot roll C back", supersededAuthority, "C");
  checkEqual("request ordering B: superseded B callbacks stay blocked when C resolves first", supersededOldCallbacks, 0);

  const earlyBTransfer = new SourceStateRequestCoordinator();
  const earlyBResponse = deferred<DataSourceStatus>();
  const laterCResponse = deferred<DataSourceStatus>();
  let earlyBTransferRequests = 0;
  let earlyBTransferWrites = 0;
  let earlyBTransferAuthority: string | null = null;
  earlyBTransfer.activateOwner(fullOwner);
  const earlyBRegistration = earlyBTransfer.startOrAdoptRequest(
    fullOwner,
    pendingB,
    () => {
      earlyBTransferRequests += 1;
      return earlyBResponse.promise;
    },
    () => {
      earlyBTransferWrites += 1;
    },
    () => undefined,
  );
  earlyBTransfer.releaseOwner(fullOwner);
  earlyBTransfer.activateOwner(legacyOwner);
  const laterCRegistration = earlyBTransfer.startOrAdoptRequest(
    legacyOwner,
    pendingC,
    () => {
      earlyBTransferRequests += 1;
      return laterCResponse.promise;
    },
    (result) => {
      earlyBTransferWrites += 1;
      earlyBTransferAuthority = result.dataset_name;
    },
    () => undefined,
  );
  earlyBResponse.resolve(statusB);
  checkEqual("request ordering B: transferred B is stale when it resolves before C", await earlyBRegistration?.outcome, "stale");
  checkEqual("request ordering B: early superseded B performs no write", earlyBTransferWrites, 0);
  laterCResponse.resolve(statusC);
  checkEqual("request ordering B: C is accepted after early stale B", await laterCRegistration?.outcome, "accepted");
  checkEqual("request ordering B: C is sole accepted authority in inverse completion order", earlyBTransferAuthority, "C");
  checkEqual("request ordering B: inverse B-to-C transfer creates exactly two physical requests", earlyBTransferRequests, 2);
  checkEqual("request ordering B: inverse B-to-C transfer produces one accepted write", earlyBTransferWrites, 1);

  const errorCoordinator = new SourceStateRequestCoordinator();
  const errorOwner = "error-owner";
  const errorResponse = deferred<DataSourceStatus>();
  let errorRequests = 0;
  let oldOwnerErrors = 0;
  let destinationErrors = 0;
  errorCoordinator.activateOwner(errorOwner);
  const errorOriginal = errorCoordinator.startOrAdoptRequest(
    errorOwner,
    pendingB,
    () => {
      errorRequests += 1;
      return errorResponse.promise;
    },
    () => undefined,
    () => {
      oldOwnerErrors += 1;
    },
  );
  errorCoordinator.releaseOwner(errorOwner);
  errorCoordinator.activateOwner(legacyOwner);
  const errorAdoption = errorCoordinator.startOrAdoptRequest(
    legacyOwner,
    pendingB,
    () => {
      errorRequests += 1;
      return errorResponse.promise;
    },
    () => undefined,
    () => {
      destinationErrors += 1;
    },
  );
  checkEqual("request ordering B: error transfer adopts one physical request", errorRequests, 1);
  checkEqual("request ordering B: error transfer registration is adopted", errorAdoption?.adopted, true);
  errorResponse.reject(new Error("fixture failure"));
  checkEqual("request ordering B: current-owner request failure reports error", await errorAdoption?.outcome, "error");
  checkEqual("request ordering B: superseded error registration is stale", await errorOriginal?.outcome, "stale");
  checkEqual("request ordering B: active destination error callback runs once", destinationErrors, 1);
  checkEqual("request ordering B: superseded owner error callback is blocked", oldOwnerErrors, 0);
  const noAutomaticRetry = errorCoordinator.startOrAdoptRequest(
    legacyOwner,
    pendingB,
    () => {
      errorRequests += 1;
      return Promise.resolve(statusB);
    },
    () => undefined,
    () => undefined,
  );
  checkEqual("request ordering B: failure does not create an automatic retry loop", noAutomaticRetry, null);
  const retryResponse = deferred<DataSourceStatus>();
  let retryAccepted = 0;
  const explicitRetry = errorCoordinator.startOrAdoptRequest(
    legacyOwner,
    pendingB,
    () => {
      errorRequests += 1;
      return retryResponse.promise;
    },
    () => {
      retryAccepted += 1;
    },
    () => undefined,
    { force: true },
  );
  const repeatedExplicitRetry = errorCoordinator.startOrAdoptRequest(
    legacyOwner,
    pendingB,
    () => {
      errorRequests += 1;
      return retryResponse.promise;
    },
    () => {
      retryAccepted += 1;
    },
    () => undefined,
    { force: true },
  );
  checkEqual("request ordering B: explicit source-state retry remains available after failure", explicitRetry?.reason, "retry");
  checkEqual("request ordering B: explicit retry creates exactly one new physical request", errorRequests, 2);
  checkEqual("request ordering B: explicit retry remains single-flight", repeatedExplicitRetry?.adopted, true);
  retryResponse.resolve(statusB);
  checkEqual("request ordering B: adopted explicit retry accepts recovery", await repeatedExplicitRetry?.outcome, "accepted");
  checkEqual("request ordering B: explicit retry recovery callback runs once", retryAccepted, 1);

  // Fifth independent review — authoritative mutation ordering shares the
  // production owner/epoch/generation lifecycle with physical GET requests.
  const lateGetCoordinator = new SourceStateRequestCoordinator();
  const lateGetResponse = deferred<DataSourceStatus>();
  const mutationBResponse = deferred<DataSourceStatus>();
  let lateGetFactories = 0;
  let mutationBFactories = 0;
  let lateGetWrites = 0;
  let lateGetAuthority: string | null = null;
  lateGetCoordinator.activateOwner(legacyOwner);
  const lateGetRegistration = lateGetCoordinator.startOrAdoptRequest(
    legacyOwner,
    null,
    () => {
      lateGetFactories += 1;
      return lateGetResponse.promise;
    },
    (result) => {
      lateGetWrites += 1;
      lateGetAuthority = result.dataset_name;
    },
    () => undefined,
  );
  const mutationBRegistration = lateGetCoordinator.startAuthoritativeMutation(
    legacyOwner,
    () => {
      mutationBFactories += 1;
      return mutationBResponse.promise;
    },
    (result) => {
      lateGetWrites += 1;
      lateGetAuthority = result.dataset_name;
    },
    () => undefined,
  );
  checkEqual("mutation ordering: legacy seed GET factory runs exactly once", lateGetFactories, 1);
  checkEqual("mutation ordering: legacy mutation B factory runs exactly once", mutationBFactories, 1);
  mutationBResponse.resolve(statusB);
  checkEqual("mutation ordering: newer legacy mutation B is accepted", await mutationBRegistration?.outcome, "accepted");
  checkEqual("mutation ordering: mutation B establishes authority", lateGetAuthority, "B");
  checkEqual("mutation ordering: exactly one authority write occurs when B is accepted", lateGetWrites, 1);
  lateGetResponse.resolve(statusA);
  checkEqual("mutation ordering: earlier seed GET A is stale after mutation B", await lateGetRegistration?.outcome, "stale");
  checkEqual("mutation ordering: late seed GET cannot roll B back to A", lateGetAuthority, "B");
  checkEqual("mutation ordering: late seed GET performs no additional write", lateGetWrites, 1);

  const inverseMutationCoordinator = new SourceStateRequestCoordinator();
  const inverseGetResponse = deferred<DataSourceStatus>();
  const inverseMutationResponse = deferred<DataSourceStatus>();
  let inverseMutationWrites = 0;
  let inverseMutationAuthority: string | null = null;
  inverseMutationCoordinator.activateOwner(legacyOwner);
  const inverseGetRegistration = inverseMutationCoordinator.startOrAdoptRequest(
    legacyOwner,
    null,
    () => inverseGetResponse.promise,
    (result) => {
      inverseMutationWrites += 1;
      inverseMutationAuthority = result.dataset_name;
    },
    () => undefined,
  );
  const inverseMutationRegistration = inverseMutationCoordinator.startAuthoritativeMutation(
    legacyOwner,
    () => inverseMutationResponse.promise,
    (result) => {
      inverseMutationWrites += 1;
      inverseMutationAuthority = result.dataset_name;
    },
    () => undefined,
  );
  inverseGetResponse.resolve(statusA);
  checkEqual("mutation ordering: GET A is stale even when it physically resolves before mutation B", await inverseGetRegistration?.outcome, "stale");
  checkEqual("mutation ordering: earlier GET completion performs no write", inverseMutationWrites, 0);
  inverseMutationResponse.resolve(statusB);
  checkEqual("mutation ordering: chronologically newer mutation wins inverse completion order", await inverseMutationRegistration?.outcome, "accepted");
  checkEqual("mutation ordering: inverse completion order ends at B", inverseMutationAuthority, "B");
  checkEqual("mutation ordering: inverse completion order produces one authority write", inverseMutationWrites, 1);

  useMissionStore.setState({
    latest: null,
    history: [],
    observedSourceIdentityKey: null,
    sourceConvergenceKey: null,
    sourceConvergenceBaseKey: null,
    sourceConvergenceSupersededKeys: [],
    retiredSourceIdentityKeys: [],
    lastConfirmedTimestampSeconds: null,
    dataSourceStatus: null,
    connectionStatus: "open",
  });
  useMissionStore.getState().setDataSourceStatus(statusA);
  useMissionStore.getState().ingest(fixtureSnapshot({ timestamp: 2100, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "A" } }));
  useMissionStore.getState().ingest(fixtureSnapshot({ timestamp: 2200, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "B" } }));
  const mutationPendingB = useMissionStore.getState().sourceConvergenceKey;
  check("mutation ordering: real store opens pending B before convergence GET", mutationPendingB !== null);
  const convergenceMutationCoordinator = new SourceStateRequestCoordinator();
  const convergenceBResponse = deferred<DataSourceStatus>();
  const mutationCResponse = deferred<DataSourceStatus>();
  let convergenceMutationWrites = 0;
  convergenceMutationCoordinator.activateOwner(legacyOwner);
  const convergenceBRegistration = convergenceMutationCoordinator.startOrAdoptRequest(
    legacyOwner,
    mutationPendingB,
    () => convergenceBResponse.promise,
    (result) => {
      convergenceMutationWrites += 1;
      useMissionStore.getState().setDataSourceStatus(result);
    },
    () => undefined,
  );
  const mutationCRegistration = convergenceMutationCoordinator.startAuthoritativeMutation(
    legacyOwner,
    () => mutationCResponse.promise,
    (result) => {
      convergenceMutationWrites += 1;
      useMissionStore.getState().setDataSourceStatus(result);
    },
    () => undefined,
  );
  mutationCResponse.resolve(statusC);
  checkEqual("mutation ordering: mutation C superseding pending-B GET is accepted", await mutationCRegistration?.outcome, "accepted");
  checkEqual("mutation ordering: mutation C is authoritative in the real store", useMissionStore.getState().dataSourceStatus?.dataset_name, "C");
  checkEqual("mutation ordering: authoritative C resolves obsolete pending B", useMissionStore.getState().sourceConvergenceKey, null);
  convergenceBResponse.resolve(statusB);
  checkEqual("mutation ordering: late convergence GET B is stale after mutation C", await convergenceBRegistration?.outcome, "stale");
  checkEqual("mutation ordering: late convergence B cannot roll C backward", useMissionStore.getState().dataSourceStatus?.dataset_name, "C");
  checkEqual("mutation ordering: pending-B GET plus mutation C produces one store write", convergenceMutationWrites, 1);
  const recoveryFrameC = fixtureSnapshot({ timestamp: 2300, source: { source_type: "dataset_replay", subject_id: "S14", dataset_name: "C" } });
  useMissionStore.getState().ingest(recoveryFrameC);
  checkEqual("mutation ordering: C-compatible telemetry recovers after mutation", useMissionStore.getState().latest, recoveryFrameC);
  check("mutation ordering: recovered telemetry history contains only C", useMissionStore.getState().history.every((frame) => frame.source.dataset_name === "C"));

  const unmountedMutationCoordinator = new SourceStateRequestCoordinator();
  const unmountedMutationResponse = deferred<DataSourceStatus>();
  let unmountedMutationWrites = 0;
  let unmountedMutationLocalCallbacks = 0;
  let unmountedMutationFactories = 0;
  unmountedMutationCoordinator.activateOwner(legacyOwner);
  const unmountedMutationRegistration = unmountedMutationCoordinator.startAuthoritativeMutation(
    legacyOwner,
    () => {
      unmountedMutationFactories += 1;
      return unmountedMutationResponse.promise;
    },
    () => {
      unmountedMutationWrites += 1;
      unmountedMutationLocalCallbacks += 1;
    },
    () => {
      unmountedMutationLocalCallbacks += 1;
    },
  );
  unmountedMutationCoordinator.releaseOwner(legacyOwner);
  unmountedMutationResponse.resolve(statusB);
  checkEqual("mutation ordering: unmounted legacy mutation factory ran once", unmountedMutationFactories, 1);
  checkEqual("mutation ordering: mutation resolving after unmount is stale", await unmountedMutationRegistration?.outcome, "stale");
  checkEqual("mutation ordering: unmounted legacy mutation performs zero store writes", unmountedMutationWrites, 0);
  checkEqual("mutation ordering: unmounted legacy mutation performs zero local callbacks", unmountedMutationLocalCallbacks, 0);

  const transferredMutationCoordinator = new SourceStateRequestCoordinator();
  const obsoleteLegacyResponse = deferred<DataSourceStatus>();
  const currentFullResponse = deferred<DataSourceStatus>();
  let transferredMutationAuthority: string | null = null;
  let obsoleteLegacyCallbacks = 0;
  transferredMutationCoordinator.activateOwner(legacyOwner);
  const obsoleteLegacyMutation = transferredMutationCoordinator.startAuthoritativeMutation(
    legacyOwner,
    () => obsoleteLegacyResponse.promise,
    () => {
      obsoleteLegacyCallbacks += 1;
    },
    () => {
      obsoleteLegacyCallbacks += 1;
    },
  );
  transferredMutationCoordinator.releaseOwner(legacyOwner);
  transferredMutationCoordinator.activateOwner(fullOwner);
  const currentFullMutation = transferredMutationCoordinator.startAuthoritativeMutation(
    fullOwner,
    () => currentFullResponse.promise,
    (result) => {
      transferredMutationAuthority = result.dataset_name;
    },
    () => undefined,
  );
  currentFullResponse.resolve(statusC);
  checkEqual("mutation ordering: newer full-owner mutation is accepted", await currentFullMutation?.outcome, "accepted");
  obsoleteLegacyResponse.resolve(statusB);
  checkEqual("mutation ordering: obsolete legacy mutation is stale after owner transfer", await obsoleteLegacyMutation?.outcome, "stale");
  checkEqual("mutation ordering: obsolete legacy owner cannot overwrite full authority", transferredMutationAuthority, "C");
  checkEqual("mutation ordering: obsolete legacy owner receives no callbacks", obsoleteLegacyCallbacks, 0);

  const reversedMutationsCoordinator = new SourceStateRequestCoordinator();
  const olderMutationResponse = deferred<DataSourceStatus>();
  const newerMutationResponse = deferred<DataSourceStatus>();
  let reversedMutationAuthority: string | null = null;
  let reversedMutationWrites = 0;
  reversedMutationsCoordinator.activateOwner(legacyOwner);
  const olderMutationRegistration = reversedMutationsCoordinator.startAuthoritativeMutation(
    legacyOwner,
    () => olderMutationResponse.promise,
    (result) => {
      reversedMutationWrites += 1;
      reversedMutationAuthority = result.dataset_name;
    },
    () => undefined,
  );
  const newerMutationRegistration = reversedMutationsCoordinator.startAuthoritativeMutation(
    legacyOwner,
    () => newerMutationResponse.promise,
    (result) => {
      reversedMutationWrites += 1;
      reversedMutationAuthority = result.dataset_name;
    },
    () => undefined,
  );
  newerMutationResponse.resolve(statusC);
  checkEqual("mutation ordering: newer of two mutations is accepted first", await newerMutationRegistration?.outcome, "accepted");
  olderMutationResponse.resolve(statusB);
  checkEqual("mutation ordering: older mutation is stale in reversed completion order", await olderMutationRegistration?.outcome, "stale");
  checkEqual("mutation ordering: reversed mutation completion ends at newer C", reversedMutationAuthority, "C");
  checkEqual("mutation ordering: reversed mutations produce one authoritative write", reversedMutationWrites, 1);

  const activeFailureCoordinator = new SourceStateRequestCoordinator();
  const activeFailureResponse = deferred<DataSourceStatus>();
  let activeFailureWrites = 0;
  let activeFailureErrors = 0;
  activeFailureCoordinator.activateOwner(legacyOwner);
  const activeFailureRegistration = activeFailureCoordinator.startAuthoritativeMutation(
    legacyOwner,
    () => activeFailureResponse.promise,
    () => {
      activeFailureWrites += 1;
    },
    () => {
      activeFailureErrors += 1;
    },
  );
  activeFailureResponse.reject(new Error("mutation failed"));
  checkEqual("mutation ordering: active mutation failure reports error", await activeFailureRegistration?.outcome, "error");
  checkEqual("mutation ordering: failed mutation performs no authority write", activeFailureWrites, 0);
  checkEqual("mutation ordering: active owner receives mutation error once", activeFailureErrors, 1);

  const obsoleteFailureCoordinator = new SourceStateRequestCoordinator();
  const obsoleteFailureResponse = deferred<DataSourceStatus>();
  let obsoleteFailureCallbacks = 0;
  obsoleteFailureCoordinator.activateOwner(legacyOwner);
  const obsoleteFailureRegistration = obsoleteFailureCoordinator.startAuthoritativeMutation(
    legacyOwner,
    () => obsoleteFailureResponse.promise,
    () => {
      obsoleteFailureCallbacks += 1;
    },
    () => {
      obsoleteFailureCallbacks += 1;
    },
  );
  obsoleteFailureCoordinator.releaseOwner(legacyOwner);
  obsoleteFailureResponse.reject(new Error("obsolete mutation failed"));
  checkEqual("mutation ordering: obsolete mutation failure is stale", await obsoleteFailureRegistration?.outcome, "stale");
  checkEqual("mutation ordering: obsolete owner receives no success or error callback", obsoleteFailureCallbacks, 0);

  useMissionStore.setState({
    latest: null,
    history: [],
    observedSourceIdentityKey: null,
    sourceConvergenceKey: null,
    sourceConvergenceBaseKey: null,
    sourceConvergenceSupersededKeys: [],
    retiredSourceIdentityKeys: [],
    lastConfirmedTimestampSeconds: null,
    dataSourceStatus: null,
    connectionStatus: "connecting",
  });
}

// ===========================================================================
// Operational session event log (master prompt 3 §16/§44)
// ===========================================================================

{
  function fixtureSignature(overrides: Partial<OperationalEventSignature>): OperationalEventSignature {
    return {
      connected: true,
      sourceType: "synthetic_demo",
      subjectId: null,
      replaySessionState: "not_applicable",
      inferenceStatus: null,
      predictionAvailability: "not_applicable",
      faultActive: false,
      faultedModalities: [],
      sourceStateStatus: "available",
      ...overrides,
    };
  }
  const ctx = { sourceLabel: "FIXTURE", sourceTimestampSeconds: null, clientMs: 0 };

  const firstObservation = deriveEventsFromTransition(null, fixtureSignature({ connected: true }), ctx);
  checkEqual("event log: first observation while connected emits exactly source_connected", firstObservation.length, 1);
  checkEqual("event log: first observation kind", firstObservation[0]?.kind, "source_connected");

  const noopTransition = deriveEventsFromTransition(fixtureSignature({}), fixtureSignature({}), ctx);
  checkEqual("event log: identical signature transition emits no events (no duplicate spam)", noopTransition.length, 0);

  const disconnectEvents = deriveEventsFromTransition(fixtureSignature({ connected: true }), fixtureSignature({ connected: false }), ctx);
  checkEqual("event log: connected -> disconnected emits exactly disconnected", disconnectEvents.length, 1);
  checkEqual("event log: disconnected event kind", disconnectEvents[0]?.kind, "disconnected");

  const reconnectEvents = deriveEventsFromTransition(fixtureSignature({ connected: false }), fixtureSignature({ connected: true }), ctx);
  checkEqual("event log: disconnected -> connected emits source_connected", reconnectEvents[0]?.kind, "source_connected");

  const sourceChangeEvents = deriveEventsFromTransition(
    fixtureSignature({ sourceType: "synthetic_demo", subjectId: null }),
    fixtureSignature({ sourceType: "recorded_replay", subjectId: "FIXTURE_S1" }),
    ctx,
  );
  check("event log: source type change emits source_changed", sourceChangeEvents.some((event) => event.kind === "source_changed"));

  const subjectChangeEvents = deriveEventsFromTransition(
    fixtureSignature({ sourceType: "recorded_replay", subjectId: "FIXTURE_S1" }),
    fixtureSignature({ sourceType: "recorded_replay", subjectId: "FIXTURE_S2" }),
    ctx,
  );
  check("event log: same source type, different subject still emits source_changed", subjectChangeEvents.some((event) => event.kind === "source_changed"));

  const playEvents = deriveEventsFromTransition(
    fixtureSignature({ replaySessionState: "ready" }),
    fixtureSignature({ replaySessionState: "playing" }),
    ctx,
  );
  checkEqual("event log: ready -> playing emits replay_started", playEvents[0]?.kind, "replay_started");

  const pauseEvents = deriveEventsFromTransition(
    fixtureSignature({ replaySessionState: "playing" }),
    fixtureSignature({ replaySessionState: "paused" }),
    ctx,
  );
  checkEqual("event log: playing -> paused emits replay_paused", pauseEvents[0]?.kind, "replay_paused");

  const loadedEvents = deriveEventsFromTransition(
    fixtureSignature({ replaySessionState: "loading" }),
    fixtureSignature({ replaySessionState: "ready" }),
    ctx,
  );
  checkEqual("event log: loading -> ready emits replay_loaded", loadedEvents[0]?.kind, "replay_loaded");

  const warmupEvents = deriveEventsFromTransition(
    fixtureSignature({ inferenceStatus: null }),
    fixtureSignature({ inferenceStatus: "warming_up" }),
    ctx,
  );
  check("event log: inference warming_up emits warmup_started", warmupEvents.some((event) => event.kind === "warmup_started"));

  const faultAppliedEvents = deriveEventsFromTransition(
    fixtureSignature({ faultActive: false, faultedModalities: [] }),
    fixtureSignature({ faultActive: true, faultedModalities: ["PPG"] }),
    ctx,
  );
  checkEqual("event log: fault applied to PPG emits exactly one fault_applied event", faultAppliedEvents.length, 1);
  checkEqual("event log: fault_applied event names the affected modality", faultAppliedEvents[0]?.modality, "PPG");
  check("event log: fault_applied is marked simulated", faultAppliedEvents[0]?.simulated === true);

  const bothFaultEvents = deriveEventsFromTransition(
    fixtureSignature({ faultActive: false, faultedModalities: [] }),
    fixtureSignature({ faultActive: true, faultedModalities: ["PPG", "IMU"] }),
    ctx,
  );
  checkEqual("event log: both-target fault emits one fault_applied event per modality", bothFaultEvents.length, 2);

  const faultClearedEvents = deriveEventsFromTransition(
    fixtureSignature({ faultActive: true, faultedModalities: ["IMU"] }),
    fixtureSignature({ faultActive: false, faultedModalities: [] }),
    ctx,
  );
  checkEqual("event log: fault cleared emits fault_cleared naming the previously-affected modality", faultClearedEvents[0]?.kind, "fault_cleared");
  checkEqual("event log: fault_cleared names IMU (from the PREVIOUS signature)", faultClearedEvents[0]?.modality, "IMU");

  const predictionAvailableEvents = deriveEventsFromTransition(
    fixtureSignature({ faultActive: false, predictionAvailability: "unavailable_no_prediction" }),
    fixtureSignature({ faultActive: false, predictionAvailability: "available" }),
    ctx,
  );
  checkEqual("event log: prediction becomes available (no prior fault) -> prediction_available", predictionAvailableEvents[0]?.kind, "prediction_available");

  const predictionRecoveredEvents = deriveEventsFromTransition(
    fixtureSignature({ faultActive: true, predictionAvailability: "unavailable_no_prediction" }),
    fixtureSignature({ faultActive: true, predictionAvailability: "available" }),
    ctx,
  );
  checkEqual(
    "event log: prediction becomes available WHILE the previous signature had an active fault -> prediction_recovered, not prediction_available",
    predictionRecoveredEvents[0]?.kind,
    "prediction_recovered",
  );

  const predictionUnavailableEvents = deriveEventsFromTransition(
    fixtureSignature({ predictionAvailability: "available" }),
    fixtureSignature({ predictionAvailability: "unavailable_no_prediction" }),
    ctx,
  );
  checkEqual("event log: prediction becomes unavailable -> prediction_unavailable", predictionUnavailableEvents[0]?.kind, "prediction_unavailable");

  const sourceErrorEvents = deriveEventsFromTransition(
    fixtureSignature({ sourceStateStatus: "available" }),
    fixtureSignature({ sourceStateStatus: "error" }),
    ctx,
  );
  check("event log: source state status -> error emits source_error", sourceErrorEvents.some((event) => event.kind === "source_error"));

  // Repeated identical transitions must never accumulate duplicate events —
  // this is the exact "duplicate-event prevention" requirement (§44):
  // calling the derivation twice on the SAME (previous, next) pair must
  // return the same single event each time, not an ever-growing list.
  const repeatedA = deriveEventsFromTransition(fixtureSignature({ faultActive: false }), fixtureSignature({ faultActive: true, faultedModalities: ["PPG"] }), ctx);
  const repeatedB = deriveEventsFromTransition(fixtureSignature({ faultActive: false }), fixtureSignature({ faultActive: true, faultedModalities: ["PPG"] }), ctx);
  checkEqual("event log: duplicate-event prevention — identical transition called twice yields same count each time", repeatedA.length, repeatedB.length);
  check("event log: duplicate-event prevention — every event carries a unique id", repeatedA[0]!.id !== repeatedB[0]!.id);
}

// ===========================================================================
// RotatingTwinFigure projection geometry (master prompt 3 §31/§44)
// ===========================================================================

{
  const head = { x: 0, y: 1.72, z: 0 };
  const rotatedHead = rotateY(head, Math.PI / 3);
  check("twin projection: rotateY output stays finite for a normal angle", Number.isFinite(rotatedHead.x) && Number.isFinite(rotatedHead.y) && Number.isFinite(rotatedHead.z));

  const rotatedFullTurn = rotateY(head, Math.PI * 8);
  check("twin projection: rotateY stays finite across many full turns (no drift into NaN/Infinity)", Number.isFinite(rotatedFullTurn.x) && Number.isFinite(rotatedFullTurn.z));

  const normalProjection = projectPoint(head, 300, 400, 200);
  check("twin projection: normal container size yields finite x/y/depth", Number.isFinite(normalProjection.x) && Number.isFinite(normalProjection.y) && Number.isFinite(normalProjection.depthFactor));

  // Zero-size visualization container (§44) — width/height/scale all 0.
  // Must never divide-by-zero into NaN or throw; every point collapses
  // toward the origin instead.
  const zeroSizeProjection = projectPoint(head, 0, 0, 0);
  check(
    "twin projection: zero-size container still returns finite coordinates",
    Number.isFinite(zeroSizeProjection.x) && Number.isFinite(zeroSizeProjection.y) && Number.isFinite(zeroSizeProjection.depthFactor),
  );
  checkEqual("twin projection: zero-size container collapses x to the origin (0/2 + 0)", zeroSizeProjection.x, 0);
}

// ===========================================================================
// Event-store duplicate-event prevention (master prompt 3 §44)
// ===========================================================================

{
  const sourceChangedA = deriveEventsFromTransition(
    null,
    { connected: true, sourceType: "recorded_replay", subjectId: null, replaySessionState: "not_applicable", inferenceStatus: null, predictionAvailability: "not_applicable", faultActive: false, faultedModalities: [], sourceStateStatus: "available" },
    { sourceLabel: "FIXTURE", sourceTimestampSeconds: null, clientMs: 0 },
  );
  const sourceChangedB = deriveEventsFromTransition(
    { connected: true, sourceType: "synthetic_demo", subjectId: null, replaySessionState: "not_applicable", inferenceStatus: null, predictionAvailability: "not_applicable", faultActive: false, faultedModalities: [], sourceStateStatus: "available" },
    { connected: true, sourceType: "recorded_replay", subjectId: "S14", replaySessionState: "not_applicable", inferenceStatus: null, predictionAvailability: "not_applicable", faultActive: false, faultedModalities: [], sourceStateStatus: "available" },
    { sourceLabel: "FIXTURE", sourceTimestampSeconds: null, clientMs: 0 },
  );
  checkEqual("event dedupe: fixture A is source_connected only", sourceChangedA[0]?.kind, "source_connected");
  checkEqual("event dedupe: fixture B is source_changed", sourceChangedB[0]?.kind, "source_changed");

  const afterFirstAppend = dedupeAgainstLast([], sourceChangedA);
  checkEqual("event dedupe: first append passes through unchanged", afterFirstAppend.length, 1);

  const afterSecondAppend = dedupeAgainstLast(afterFirstAppend, sourceChangedB);
  checkEqual("event dedupe: distinct kind (source_connected -> source_changed) is not suppressed", afterSecondAppend.length, 1);

  const storeAfterTwoAppends = [...afterFirstAppend, ...afterSecondAppend];
  const repeatedSourceChanged = dedupeAgainstLast(storeAfterTwoAppends, sourceChangedB);
  checkEqual(
    "event dedupe: a second source_changed immediately after the first (two independent REST resolutions) is suppressed",
    repeatedSourceChanged.length,
    0,
  );

  const differentModalityFault = dedupeAgainstLast(
    [{ id: "x", kind: "fault_applied", label: "Simulated fault applied", modality: "PPG", simulated: true, sourceLabel: "F", sourceTimestampSeconds: null, clientMs: 0 }],
    [{ id: "y", kind: "fault_applied", label: "Simulated fault applied", modality: "IMU", simulated: true, sourceLabel: "F", sourceTimestampSeconds: null, clientMs: 0 }],
  );
  check("event dedupe: same kind but different modality is NOT suppressed (both-target fault)", differentModalityFault.length === 1);
}

// ===========================================================================
// Volumetric human system — geometry, anchors, HR segments (master prompt
// 3A §19: "no duplicate modality", "confirmed-channel count", "fault
// localization", "finite geometry values", "no NaN transformation",
// "HR segment mapping", "no stale prediction").
// ===========================================================================

{
  // Every body segment's capsule transform must be finite — no NaN can ever
  // reach a Three.js mesh transform.
  for (const segment of BODY_SEGMENTS) {
    const transform = computeSegmentTransform(segment.from, segment.to);
    check(
      `human geometry: segment "${segment.id}" transform is fully finite`,
      transform.position.every(Number.isFinite) && transform.quaternion.every(Number.isFinite) && Number.isFinite(transform.length),
    );
    check(`human geometry: segment "${segment.id}" endpoints are finite`, isFiniteVec3(segment.from) && isFiniteVec3(segment.to));
  }
  check("human geometry: head joint is finite", isFiniteVec3(JOINTS.head) && Number.isFinite(HEAD_RADIUS));

  for (const orbit of REGION_ORBITS) {
    check(`region orbit: "${orbit.id}" center/radii are finite`, orbit.center.every(Number.isFinite) && Number.isFinite(orbit.radiusX) && Number.isFinite(orbit.radiusY));
  }
  checkEqual("region orbit: exactly 3 physical regions (frontal/chest/wrist)", REGION_ORBITS.length, 3);
  check(
    "region orbit: ids are exactly frontal/chest/wrist, no duplicates",
    new Set(REGION_ORBITS.map((o) => o.id)).size === 3 && ["frontal", "chest", "wrist"].every((id) => REGION_ORBITS.some((o) => o.id === id)),
  );

  // Sensor-anchor mapping — modality-to-3D-anchor mapping and no-duplicate-modality (§19).
  checkEqual("sensor anchors: exactly 5 final modalities defined", ALL_FINAL_MODALITIES.length, 5);
  for (const modality of ALL_FINAL_MODALITIES) {
    const position = MODALITY_ANCHOR_POSITION[modality];
    check(`sensor anchors: ${modality} has a finite 3D position`, position.every(Number.isFinite));
  }
  check(
    "sensor anchors: PPG and IMU share the wrist region but are NOT at the identical point (visually distinct)",
    MODALITY_ANCHOR_POSITION.PPG.join(",") !== MODALITY_ANCHOR_POSITION.IMU.join(","),
  );

  const fixtureModalityStates = ALL_FINAL_MODALITIES.map((modality) => ({
    modality,
    region: "Wrist" as const,
    nodeState: "confirmed" as const,
    stateLabel: "Confirmed" as const,
    statusLabel: "FIXTURE",
  }));
  const anchors = buildSensorAnchors(fixtureModalityStates, "PPG");
  checkEqual("sensor anchors: buildSensorAnchors returns exactly 5 anchors", anchors.length, 5);
  checkEqual("sensor anchors: no duplicate modality in the anchor list", new Set(anchors.map((a) => a.modality)).size, 5);
  check("sensor anchors: exactly one anchor is selected (PPG)", anchors.filter((a) => a.selected).length === 1 && anchors.find((a) => a.selected)?.modality === "PPG");
  check("sensor anchors: every anchor position is finite", anchors.every((a) => a.position.every(Number.isFinite)));

  // Fault localization — only the faulted modality's anchor carries "fault" state.
  const faultedStates = ALL_FINAL_MODALITIES.map((modality) => ({
    modality,
    region: "Wrist" as const,
    nodeState: modality === "PPG" ? ("fault" as const) : ("confirmed" as const),
    stateLabel: modality === "PPG" ? ("Simulated fault" as const) : ("Confirmed" as const),
    statusLabel: "FIXTURE",
  }));
  const faultedAnchors = buildSensorAnchors(faultedStates, "PPG");
  checkEqual("sensor anchors: fault localization — exactly 1 anchor in fault state", faultedAnchors.filter((a) => a.state === "fault").length, 1);
  check("sensor anchors: fault localization — the faulted anchor is PPG, not IMU/ECG/EEG/EOG", faultedAnchors.find((a) => a.state === "fault")?.modality === "PPG");

  // Disconnected clearing — every anchor reflects disconnected state uniformly.
  const disconnectedStates = ALL_FINAL_MODALITIES.map((modality) => ({
    modality,
    region: "Wrist" as const,
    nodeState: "disconnected" as const,
    stateLabel: "Disconnected" as const,
    statusLabel: "FIXTURE",
  }));
  check("sensor anchors: disconnected clearing — every anchor is disconnected", buildSensorAnchors(disconnectedStates, "PPG").every((a) => a.state === "disconnected"));

  // HR segment mapping (§10/§19), including the PPG-fault interruption case and no-stale-output guarantee.
  const nominalSegments = computeHrSegments({ sourceConfirmed: true, ppgAvailable: true, imuAvailable: true, modelOutputAvailable: true, ppgFaulted: false, imuFaulted: false });
  checkEqual("HR segments: nominal — all 4 segments on", nominalSegments.filter((s) => s.on).length, 4);
  check("HR segments: nominal — none faulted", nominalSegments.every((s) => !s.faulted));

  const ppgFaultSegments = computeHrSegments({ sourceConfirmed: true, ppgAvailable: false, imuAvailable: true, modelOutputAvailable: false, ppgFaulted: true, imuFaulted: false });
  checkEqual("HR segments: PPG fault — PPG segment is off", ppgFaultSegments.find((s) => s.key === "ppg")?.on, false);
  checkEqual("HR segments: PPG fault — PPG segment is marked faulted", ppgFaultSegments.find((s) => s.key === "ppg")?.faulted, true);
  checkEqual("HR segments: PPG fault — IMU segment stays unaffected (on, not faulted)", ppgFaultSegments.find((s) => s.key === "imu")?.on, true);
  checkEqual("HR segments: PPG fault — IMU segment not faulted", ppgFaultSegments.find((s) => s.key === "imu")?.faulted, false);
  checkEqual("HR segments: PPG fault — no stale model output (OUT segment off)", ppgFaultSegments.find((s) => s.key === "model")?.on, false);

  const disconnectedSegments = computeHrSegments({ sourceConfirmed: false, ppgAvailable: false, imuAvailable: false, modelOutputAvailable: false, ppgFaulted: false, imuFaulted: false });
  check("HR segments: disconnected — all 4 segments off, no stale on-state survives", disconnectedSegments.every((s) => !s.on));
}

// ===========================================================================
// Orthographic camera fit (Prompt 3A.2 §6/§9 item 19) — the deterministic
// figure framing that replaced the 3A.1 perspective "zoom out until it fits"
// approach. Every frustum edge must stay finite across the desktop/tablet/
// mobile aspect ratios the required screenshot set exercises, and the figure
// must be framed to the requested fraction of the canvas.
// ===========================================================================

{
  const cases = [
    { aspect: 1440 / 900, fraction: 0.76 },
    { aspect: 1024 / 768, fraction: 0.72 },
    { aspect: 390 / 844, fraction: 0.64 },
    { aspect: 0.6, fraction: 0.78 },
    // Degenerate inputs must fail closed to finite bounds, never NaN.
    { aspect: 0, fraction: 0.76 },
    { aspect: -1, fraction: 0.76 },
    { aspect: Number.NaN, fraction: Number.NaN },
  ];
  let allFinite = true;
  let allOrdered = true;
  for (const { aspect, fraction } of cases) {
    const fit = computeOrthographicFit(aspect, fraction);
    if (![fit.left, fit.right, fit.top, fit.bottom].every((value) => Number.isFinite(value))) allFinite = false;
    if (!(fit.right > fit.left && fit.top > fit.bottom)) allOrdered = false;
  }
  check("ortho fit: frustum edges stay finite across desktop/tablet/mobile aspect ratios, and degenerate (0/negative/NaN) inputs fail closed to finite bounds", allFinite);
  check("ortho fit: right > left and top > bottom for every case (a non-degenerate frustum)", allOrdered);

  // A wider canvas at the same height fraction gives a wider frustum (more
  // horizontal world units mapped), confirming the fit is aspect-aware.
  const wide = computeOrthographicFit(1.6, 0.76);
  const narrow = computeOrthographicFit(0.8, 0.76);
  check("ortho fit: a wider canvas aspect yields a wider frustum (aspect-aware)", wide.right - wide.left > narrow.right - narrow.left);

  // The three-quarter orthographic camera position is finite and off-axis.
  const [cx, cy, cz] = orthoCameraPosition();
  check("ortho camera: position is finite and genuinely three-quarter (non-zero X and Z)", [cx, cy, cz].every(Number.isFinite) && Math.abs(cx) > 0 && Math.abs(cz) > 0);
}

// ===========================================================================
// Digital Twin static-copy safety (Prompt 3A.1 §8.2/§9 items 15-16) — source
// inspection of app/digital-twin/page.tsx. This route's `.tsx` cannot be
// imported directly under plain Node (it renders JSX and pulls in
// next/dynamic + a WebGL component tree), so the specific data bindings this
// pass exists to remove are asserted absent from the source text directly —
// a precise regression test for the exact defect found during Prompt 3A
// live QA (the backend's `narrative`/`milestone_label` fields still implied
// an inferred adaptation state after the first percentage-ring removal).
// ===========================================================================

{
  const digitalTwinPageSource = readFileSync(join(REPO_SRC_ROOT, "app/digital-twin/page.tsx"), "utf8");
  check("digital twin: milestone_label is never read from state (optional-chain form)", !digitalTwinPageSource.includes("state?.milestone_label"));
  check("digital twin: milestone_label is never read from state (direct form)", !digitalTwinPageSource.includes("state.milestone_label"));
  check("digital twin: the backend narrative field is never rendered", !digitalTwinPageSource.includes("state?.narrative") && !digitalTwinPageSource.includes("state.narrative"));
  check("digital twin: overall_adaptation is never rendered", !digitalTwinPageSource.includes("overall_adaptation"));
  check("digital twin: per-system baseline_score/current_score/delta are never rendered", !digitalTwinPageSource.includes("baseline_score") && !digitalTwinPageSource.includes("current_score") && !digitalTwinPageSource.includes(".delta"));
  check("digital twin: the old procedural RotatingTwinFigure import is gone", !digitalTwinPageSource.includes('from "@/components/visualization/RotatingTwinFigure"'));
  check("digital twin: the volumetric ConceptualTwinStage is used instead", digitalTwinPageSource.includes("ConceptualTwinStage"));

  // §9 item 20 — reduced-motion must disable automatic conceptual-twin
  // rotation. ConceptualTwinStage.tsx is a "use client" R3F component (uses
  // useFrame/useThree) and cannot be imported into this plain-Node harness
  // the same way the pure lib/monitoring/** modules are — this is therefore
  // a source-inspection check that the reduced-motion gate exists and
  // forces `playing` false on match, not a full behavioral render test.
  // Live confirmation is via QA screenshot/interaction, not this script.
  //
  // Stage 2 A2 update: this component no longer runs its own OS-only
  // `matchMedia("(prefers-reduced-motion: reduce)")` check — it now reads the
  // shared `useReducedMotionPreference()` hook (lib/runtime/reduceMotion.ts),
  // which combines that same OS query with the persisted `/settings` toggle,
  // so this component also respects a user who only enabled the persisted
  // setting. The OS-query string itself, plus the hook's OR-combination and
  // live-update listeners, are asserted separately by
  // scripts/verify-reduced-motion-unification.mjs (part of `verify:monitoring`).
  // The guarantee this block existed for — reduced motion disables auto-
  // rotation — is unchanged and still verified below.
  const conceptualTwinStageSource = readFileSync(join(REPO_SRC_ROOT, "components/visualization/human/ConceptualTwinStage.tsx"), "utf8");
  check("conceptual twin stage: uses the shared reduced-motion source of truth", conceptualTwinStageSource.includes("useReducedMotionPreference()"));
  check("conceptual twin stage: reduced-motion forces playing to false", conceptualTwinStageSource.includes("setPlaying(false)"));
  check("conceptual twin stage: auto-rotation is gated on both playing and reducedMotion", conceptualTwinStageSource.includes("if (playing && !reducedMotion)"));

  // Prompt 3A.2 §8 / §11 — the day slider, mission-day text, backend call, and
  // in-canvas duplicated safety badge must all be gone.
  check("digital twin 3A.2: DigitalTwinDaySlider is no longer rendered", !digitalTwinPageSource.includes("DigitalTwinDaySlider"));
  check("digital twin 3A.2: no 'Illustrative scenario day' control", !digitalTwinPageSource.includes("Illustrative scenario day"));
  check("digital twin 3A.2: no 'Illustrative mission day' label", !digitalTwinPageSource.includes("Illustrative mission day"));
  check("digital twin 3A.2: no day-dependent backend call (getDigitalTwin)", !digitalTwinPageSource.includes("getDigitalTwin"));
  check("digital twin 3A.2: 'Proposed computation boundary' architecture-flow card present", digitalTwinPageSource.includes("Proposed computation boundary"));
  check("digital twin 3A.2: no adaptation/confidence percentage copy", !/adaptation\s*percentage|% adaptation|confidence value:/i.test(digitalTwinPageSource) || digitalTwinPageSource.includes("reports no adaptation percentage"));
  // The mannequin canvas must not carry an overlaid safety badge (§8.1); the
  // single badge lives on the page only.
  check("conceptual twin stage: no in-canvas safety badge overlaid on the figure", !conceptualTwinStageSource.includes("ARCHITECTURE ONLY"));
}

// ===========================================================================
// Operational avatar overlay structure (Prompt 3A.2 §5/§11) — the sensor
// buttons and module labels must be owned by the DOM overlay, NOT by
// independent world-space drei <Html> elements inside the 3D scene. Asserted
// by source inspection since these are "use client" R3F components that cannot
// be imported into this plain-Node harness.
// ===========================================================================

{
  const avatarSource = readFileSync(join(REPO_SRC_ROOT, "components/visualization/human/PhysiologyAvatar3D.tsx"), "utf8");
  const sensorAnchorSource = readFileSync(join(REPO_SRC_ROOT, "components/visualization/human/SensorAnchor.tsx"), "utf8");
  const overlaySource = readFileSync(join(REPO_SRC_ROOT, "components/visualization/human/OperationalAvatarOverlay.tsx"), "utf8");

  check("avatar overlay: PhysiologyAvatar3D no longer imports the deleted world-space AvatarLabels", !avatarSource.includes("AvatarLabels"));
  check("avatar overlay: PhysiologyAvatar3D renders the DOM OperationalAvatarOverlay", avatarSource.includes("OperationalAvatarOverlay"));
  check("avatar overlay: SensorAnchor renders no interactive <button> (moved to the DOM overlay)", !sensorAnchorSource.includes("<button"));
  check("avatar overlay: SensorAnchor imports no drei (no world-space <Html>/<Billboard> label)", !sensorAnchorSource.includes('from "@react-three/drei"'));
  check("avatar overlay: the interactive sensor buttons are owned by the DOM overlay", overlaySource.includes("<button") && overlaySource.includes("aria-pressed"));
  check("avatar overlay: module labels live in the DOM overlay, not world-space", overlaySource.includes("FRONTAL MODULE") && overlaySource.includes("WRIST MODULE"));
}

// ===========================================================================
// Prompt 3B §8/§24 — Inference Integrity Orbit categorical ring derivation.
// Every ring is categorical (no percentage/confidence). Assert the gate,
// fault localisation, replay-only output, and recovered transient mappings.
// ===========================================================================

{
  // Active replay, everything confirmed, prediction available → all confirmed.
  const healthy = deriveIntegrityRings({
    telemetry: "active",
    ppgState: "confirmed",
    imuState: "confirmed",
    isReplay: true,
    predictionAvailable: true,
    inferenceWarmingUp: false,
    recovered: false,
  });
  checkEqual("integrity rings: exactly four rings", healthy.length, 4);
  checkEqual("integrity rings: ring order is source/ppg/imu/output", healthy.map((r) => r.key).join(","), "source,ppg,imu,output");
  checkEqual("integrity rings: healthy replay source confirmed", healthy[0]!.state, "confirmed");
  checkEqual("integrity rings: healthy replay output confirmed", healthy[3]!.state, "confirmed");

  // PPG fault localises to the PPG ring; IMU stays confirmed; output not confirmed.
  const ppgFault = deriveIntegrityRings({
    telemetry: "active",
    ppgState: "fault",
    imuState: "confirmed",
    isReplay: true,
    predictionAvailable: false,
    inferenceWarmingUp: false,
    recovered: false,
  });
  checkEqual("integrity rings: PPG fault localises to PPG ring", ppgFault[1]!.state, "fault");
  checkEqual("integrity rings: PPG fault leaves IMU confirmed", ppgFault[2]!.state, "confirmed");
  check("integrity rings: PPG fault means output is not confirmed", ppgFault[3]!.state !== "confirmed");

  // Synthetic source never claims an HR output (replay-only inference).
  const synthetic = deriveIntegrityRings({
    telemetry: "active",
    ppgState: "confirmed",
    imuState: "confirmed",
    isReplay: false,
    predictionAvailable: false,
    inferenceWarmingUp: false,
    recovered: false,
  });
  checkEqual("integrity rings: synthetic output is unavailable (HR inference is replay-only)", synthetic[3]!.state, "unavailable");

  // Disconnected telemetry gates every ring.
  const disconnected = deriveIntegrityRings({
    telemetry: "disconnected",
    ppgState: "confirmed",
    imuState: "confirmed",
    isReplay: true,
    predictionAvailable: true,
    inferenceWarmingUp: false,
    recovered: false,
  });
  check("integrity rings: disconnect gates all rings", disconnected.every((r) => r.state === "disconnected"));

  // Recovered transient marks source + output recovered.
  const recovered = deriveIntegrityRings({
    telemetry: "active",
    ppgState: "confirmed",
    imuState: "confirmed",
    isReplay: true,
    predictionAvailable: true,
    inferenceWarmingUp: false,
    recovered: true,
  });
  checkEqual("integrity rings: recovered transient marks source recovered", recovered[0]!.state, "recovered");
  checkEqual("integrity rings: recovered transient marks output recovered", recovered[3]!.state, "recovered");
}

// ===========================================================================
// Prompt 3B §10/§24 — Hexagonal inference/fault flow derivation. Six nodes,
// six edges; a single confirmed input is insufficient (PPG fault blocks the
// window even while IMU is confirmed).
// ===========================================================================

{
  const healthy = deriveHexFlow({
    telemetry: "active",
    ppgState: "confirmed",
    imuState: "confirmed",
    isReplay: true,
    predictionAvailable: true,
    inferenceWarmingUp: false,
  });
  checkEqual("hex flow: exactly six nodes", healthy.nodes.length, 6);
  checkEqual("hex flow: exactly six edges", healthy.edges.length, 6);
  checkEqual("hex flow: node ids complete + ordered", healthy.nodes.map((n) => n.id).join(","), "source,ppgInput,imuInput,window,model,output");
  checkEqual("hex flow: healthy window confirmed", healthy.nodes.find((n) => n.id === "window")!.state, "confirmed");
  checkEqual("hex flow: healthy output confirmed", healthy.nodes.find((n) => n.id === "output")!.state, "confirmed");

  // PPG fault: PPG node faults, IMU confirmed, window BLOCKED, model+output unavailable.
  const ppgFault = deriveHexFlow({
    telemetry: "active",
    ppgState: "fault",
    imuState: "confirmed",
    isReplay: true,
    predictionAvailable: true,
    inferenceWarmingUp: false,
  });
  checkEqual("hex flow: PPG fault → ppgInput fault", ppgFault.nodes.find((n) => n.id === "ppgInput")!.state, "fault");
  checkEqual("hex flow: PPG fault leaves imuInput confirmed", ppgFault.nodes.find((n) => n.id === "imuInput")!.state, "confirmed");
  checkEqual("hex flow: one confirmed input is insufficient → window blocked", ppgFault.nodes.find((n) => n.id === "window")!.state, "blocked");
  checkEqual("hex flow: PPG fault → model unavailable", ppgFault.nodes.find((n) => n.id === "model")!.state, "unavailable");
  checkEqual("hex flow: PPG fault → output unavailable", ppgFault.nodes.find((n) => n.id === "output")!.state, "unavailable");
  check("hex flow: PPG fault breaks the ppgInput→window edge", ppgFault.edges.find((e) => e.id === "ppg-win")!.state === "broken");

  // Both inputs faulted still blocks the window.
  const bothFault = deriveHexFlow({
    telemetry: "active",
    ppgState: "fault",
    imuState: "fault",
    isReplay: true,
    predictionAvailable: true,
    inferenceWarmingUp: false,
  });
  checkEqual("hex flow: both-input fault blocks window", bothFault.nodes.find((n) => n.id === "window")!.state, "blocked");

  // Synthetic source: inputs confirmed, but model/output unavailable (replay-only).
  const synthetic = deriveHexFlow({
    telemetry: "active",
    ppgState: "confirmed",
    imuState: "confirmed",
    isReplay: false,
    predictionAvailable: false,
    inferenceWarmingUp: false,
  });
  checkEqual("hex flow: synthetic model unavailable (HR inference replay-only)", synthetic.nodes.find((n) => n.id === "model")!.state, "unavailable");

  // Source-error telemetry propagates to the source node.
  const sourceError = deriveHexFlow({
    telemetry: "source_error",
    ppgState: "confirmed",
    imuState: "confirmed",
    isReplay: true,
    predictionAvailable: true,
    inferenceWarmingUp: false,
  });
  checkEqual("hex flow: source_error telemetry marks source node source_error", sourceError.nodes.find((n) => n.id === "source")!.state, "source_error");
}

// ===========================================================================
// Prompt 3B §9/§23/§24 — Source inspection of the new geometric telemetry
// components. Asserts the anti-fabrication guarantees that cannot be exercised
// by importing these "use client" R3F/SVG components into this plain-Node
// harness: no invented confidence/percentage, the pentagon is topology (no
// filled radar), five unique modalities, the honest legends.
// ===========================================================================

{
  const pentagon = readFileSync(join(REPO_SRC_ROOT, "components/operations/ModalityPentagon.tsx"), "utf8");
  const orbit = readFileSync(join(REPO_SRC_ROOT, "components/operations/InferenceIntegrityOrbit.tsx"), "utf8");
  const hexFlow = readFileSync(join(REPO_SRC_ROOT, "components/operations/InferenceHexFlow.tsx"), "utf8");
  const ribbon = readFileSync(join(REPO_SRC_ROOT, "components/operations/SignalRibbonMatrix.tsx"), "utf8");
  const spine = readFileSync(join(REPO_SRC_ROOT, "components/operations/FaultRecoverySpine.tsx"), "utf8");

  // Pentagon carries all five final modalities exactly once, in anatomical order.
  for (const modality of ["EEG", "EOG", "ECG", "IMU", "PPG"]) {
    check(`pentagon: contains ${modality} vertex`, pentagon.includes(`modality: "${modality}"`));
  }
  const vertexMatches = pentagon.match(/modality: "(?:EEG|EOG|ECG|IMU|PPG)"/g) ?? [];
  checkEqual("pentagon: exactly five vertices (no duplicate/absent modality)", vertexMatches.length, 5);
  check("pentagon: frame polygon is not filled (topology, not a radar score)", pentagon.includes('fill="none"'));
  // §12/§17 — "N of 5 currently confirmed" read as if only N of 5 belonged to
  // the final architecture; the pentagon now separates architecture
  // membership from current-source observability explicitly.
  check(
    "pentagon: honest architecture-vs-observability count copy",
    pentagon.includes("final modalities") && pentagon.includes("confirmed in this synthetic session"),
  );

  // No invented confidence/readiness/health/percentage anywhere in these views.
  for (const [name, src] of [
    ["pentagon", pentagon],
    ["integrity orbit", orbit],
    ["hex flow", hexFlow],
    ["ribbon matrix", ribbon],
    ["fault spine", spine],
  ] as const) {
    check(`${name}: renders no invented percentage token`, !/\d\s*%|%\}/.test(src));
    check(`${name}: mentions no fabricated confidence/reliability/readiness score`, !/confidence score|reliability score|readiness score|health score/i.test(src.replace(/not a confidence score/gi, "")));
  }
  check("integrity orbit: keeps the 'not a confidence score' disclaimer", orbit.includes("not a confidence score"));
  check("ribbon matrix: states EEG/EOG are never synthesised", ribbon.includes("never synthesised"));
  check("fault spine: built from recorded events only (no fabricated timeline)", spine.includes("recorded events only"));

  // §3C.1 §6/§14 — the mobile hex flow used to force `min-width: 360px`
  // inside an `overflow-x-auto` wrapper, clipping the last node at 390px.
  // The fix replaced one shrinking SVG with two purpose-built layouts; assert
  // both DESKTOP_POS and MOBILE_POS still carry all six logical nodes (a
  // typo or an incomplete edit to either literal would silently drop a node
  // from just one of the two responsive layouts).
  const hexNodeIds = ["source", "ppgInput", "imuInput", "window", "model", "output"];
  const desktopPosBlock = hexFlow.slice(hexFlow.indexOf("DESKTOP_POS: Positions"), hexFlow.indexOf("DESKTOP_VIEWBOX"));
  const mobilePosBlock = hexFlow.slice(hexFlow.indexOf("MOBILE_POS: Positions"), hexFlow.indexOf("MOBILE_VIEWBOX"));
  for (const id of hexNodeIds) {
    check(`hex flow: desktop layout positions the "${id}" node`, new RegExp(`\\b${id}:\\s*{`).test(desktopPosBlock));
    check(`hex flow: mobile layout positions the "${id}" node`, new RegExp(`\\b${id}:\\s*{`).test(mobilePosBlock));
  }
  check("hex flow: no leftover fixed min-width forcing horizontal scroll", !hexFlow.includes("min-w-[360px]"));

  // §3C.1 §18 — static/reference routes must not display live connection
  // status; PresentationHeader's STATIC_SCOPE_BADGE table is the single
  // switch point, so assert it maps exactly the three static variants to
  // their required labels and leaves "final"/"monitoring" out (so those two
  // fall through to the live sourceLabel/connectionLabel branch).
  const header = readFileSync(join(REPO_SRC_ROOT, "components/layout/PresentationHeader.tsx"), "utf8");
  const badgeBlock = header.slice(header.indexOf("STATIC_SCOPE_BADGE"), header.indexOf("// Master-prompt 3 §6.3"));
  check("header: digital-twin (reference) shows CONCEPTUAL REFERENCE", badgeBlock.includes("CONCEPTUAL REFERENCE"));
  check("header: digital-twin (reference) shows UNTRAINED · UNVALIDATED", badgeBlock.includes("UNTRAINED · UNVALIDATED"));
  check("header: system-brief (system) shows FINAL ARCHITECTURE", badgeBlock.includes("FINAL ARCHITECTURE"));
  check("header: research/experimental shows RESEARCH EVIDENCE", badgeBlock.includes("RESEARCH EVIDENCE"));
  check("header: operational variants ('final', 'monitoring') are absent from the static badge table (so they keep live status)", !/\bfinal:\s*{/.test(badgeBlock) && !/\bmonitoring:\s*{/.test(badgeBlock));
}

// ===========================================================================
// §3C.1 §3 — anatomical human geometry buffer integrity. anatomicalHumanGeometry.ts
// is explicitly pure geometry (no `three`, no DOM, no React), so it can be
// imported and exercised directly here rather than only source-inspected.
// ===========================================================================

{
  const { body } = buildAnatomicalHuman();
  const positions = Array.from(body.positions);
  const normals = Array.from(body.normals);
  const indices = Array.from(body.indices);
  const vertexCount = positions.length / 3;

  check("anatomical human: position buffer length is a whole number of xyz triples", Number.isInteger(vertexCount));
  check("anatomical human: normal buffer is the same length as the position buffer", normals.length === positions.length);
  check("anatomical human: every position component is finite (no NaN/Infinity)", positions.every(Number.isFinite));
  check("anatomical human: every normal component is finite (no NaN/Infinity)", normals.every(Number.isFinite));
  check("anatomical human: index buffer length is a whole number of triangles", indices.length % 3 === 0);
  check(
    "anatomical human: every index references a real vertex (valid triangle indices)",
    indices.every((i) => Number.isInteger(i) && i >= 0 && i < vertexCount),
  );
  check("anatomical human: has a non-trivial vertex count (torso+head+4 limbs actually lofted)", vertexCount > 500);
}

// ===========================================================================
// §3C.1 §5 — Recent HR Estimate Trend gap-preservation. deriveHrTrend must
// never draw a line across an interval with no real sample, and must never
// interpolate/fabricate a value.
// ===========================================================================

{
  const now = 1000;
  const continuous = deriveHrTrend(
    [
      { timestampSeconds: now - 10, heartRateBpm: 70 },
      { timestampSeconds: now - 8, heartRateBpm: 72 },
      { timestampSeconds: now - 6, heartRateBpm: 71 },
      { timestampSeconds: now - 4, heartRateBpm: 73 },
    ],
    now,
  );
  check("hr trend: continuous evenly-spaced samples produce no gap-break points", continuous.points.every((p) => p.value !== null));
  checkEqual("hr trend: current value is the most recent real sample", continuous.currentValue, 73);

  const withGap = deriveHrTrend(
    [
      { timestampSeconds: now - 60, heartRateBpm: 65 },
      { timestampSeconds: now - 58, heartRateBpm: 66 },
      // 40s hole — e.g. a fault withheld the output — must break the line, never connect across it.
      { timestampSeconds: now - 18, heartRateBpm: 80 },
      { timestampSeconds: now - 16, heartRateBpm: 79 },
    ],
    now,
  );
  const gapBreaks = withGap.points.filter((p) => p.value === null);
  check("hr trend: a wide hole in real samples inserts an explicit null break (never a straight interpolated line)", gapBreaks.length >= 1);
  checkEqual("hr trend: current value is the most recent real sample even after a gap", withGap.currentValue, 79);

  const noPredictions = deriveHrTrend(
    [
      { timestampSeconds: now - 10, heartRateBpm: null },
      { timestampSeconds: now - 5, heartRateBpm: null },
    ],
    now,
  );
  checkEqual("hr trend: no real HR samples in window — hasData is false, not a fabricated flat/zero series", noPredictions.hasData, false);
  checkEqual("hr trend: no real HR samples in window — currentValue stays null", noPredictions.currentValue, null);

  const outsideWindow = deriveHrTrend([{ timestampSeconds: now - 500, heartRateBpm: 90 }], now, 90);
  checkEqual("hr trend: a real sample older than the display window is excluded, not shown as current", outsideWindow.hasData, false);
}

// ===========================================================================
// Prompt-4 §26 — Route / runtime isolation (deterministic proof that static
// routes perform no operational work; the Network-panel capture in the dossier
// is corroborating evidence, not the primary proof).
// ===========================================================================

{
  checkEqual("runtime tier: /mission-overview is full-operational", classifyRuntimeTier("/mission-overview"), "full");
  checkEqual("runtime tier: /live-monitoring is full-operational", classifyRuntimeTier("/live-monitoring"), "full");
  checkEqual("runtime tier: /system-brief is static (no operational work)", classifyRuntimeTier("/system-brief"), "static");
  checkEqual("runtime tier: /research/experimental is static", classifyRuntimeTier("/research/experimental"), "static");
  checkEqual("runtime tier: /digital-twin is static", classifyRuntimeTier("/digital-twin"), "static");
  checkEqual("runtime tier: / (redirect root) is static", classifyRuntimeTier("/"), "static");
  checkEqual("runtime tier: null pathname is static (safe default)", classifyRuntimeTier(null), "static");
  checkEqual("runtime tier: unknown route falls through to static", classifyRuntimeTier("/some/new/page"), "static");
  checkEqual("runtime tier: /ai-insights is live-feed (deliberate legacy allowlist)", classifyRuntimeTier("/ai-insights"), "live-feed");
  checkEqual("runtime tier: /mission-timeline is live-feed", classifyRuntimeTier("/mission-timeline"), "live-feed");
  checkEqual("runtime tier: /settings is live-feed", classifyRuntimeTier("/settings"), "live-feed");

  checkEqual("runtime tier: static routes open NO websocket", tierOpensWebSocket("static"), false);
  checkEqual("runtime tier: static routes mount NO monitoring session", tierMountsMonitoringSession("static"), false);
  checkEqual("runtime tier: live-feed opens a websocket", tierOpensWebSocket("live-feed"), true);
  checkEqual("runtime tier: live-feed does NOT mount monitoring session", tierMountsMonitoringSession("live-feed"), false);
  checkEqual("runtime tier: full opens a websocket", tierOpensWebSocket("full"), true);
  checkEqual("runtime tier: full mounts the monitoring session", tierMountsMonitoringSession("full"), true);

  // Structural proof the root layout no longer mounts operational providers
  // globally, and that the boundary + static pages are wired as intended.
  const layoutSource = readFileSync(join(REPO_SRC_ROOT, "app/layout.tsx"), "utf8");
  check("layout: no longer imports MonitoringSessionProvider directly", !layoutSource.includes("MonitoringSessionProvider"));
  check("layout: no longer imports OperationalEventLogWatcher directly", !layoutSource.includes("OperationalEventLogWatcher"));
  check("layout: no longer imports LiveFeedProvider directly", !layoutSource.includes("LiveFeedProvider"));
  check("layout: mounts the OperationalRuntime boundary", layoutSource.includes("OperationalRuntime"));
  check("layout: provides a skip-to-main link", layoutSource.includes("#main-content"));
  check("layout: marks the main landmark id main-content", /id="main-content"/.test(layoutSource));
  check("layout: applies the reduced-motion preference at boot", layoutSource.includes("biomin:reduce-motion"));

  const runtimeSource = readFileSync(join(REPO_SRC_ROOT, "components/layout/OperationalRuntime.tsx"), "utf8");
  check("boundary: mounts MonitoringSessionProvider on the full tier", runtimeSource.includes("MonitoringSessionProvider"));
  check("boundary: mounts OperationalEventLogWatcher on the full tier", runtimeSource.includes("OperationalEventLogWatcher"));
  check("boundary: passes seedDataSourceState={false} on full tier (dedupe)", runtimeSource.includes("seedDataSourceState={false}"));

  for (const staticRoute of ["app/system-brief/page.tsx", "app/research/experimental/page.tsx", "app/digital-twin/page.tsx"]) {
    const src = readFileSync(join(REPO_SRC_ROOT, staticRoute), "utf8");
    check(`${staticRoute}: does not call useLiveFeed`, !src.includes("useLiveFeed"));
    check(`${staticRoute}: does not call useMonitoringSession`, !src.includes("useMonitoringSession"));
    check(`${staticRoute}: does not mount LiveFeedProvider`, !src.includes("LiveFeedProvider"));
  }
}

// ===========================================================================
// Prompt-4 §21 — Presenter preflight semantics. "Ready" is never inferred from
// the absence of an error; the HR-model item is honestly Unknown. Reuses the
// existing fixtureDataSourceStatus / fixtureFault helpers above.
// ===========================================================================

{
  const good = derivePresenterPreflight({
    sourceStateStatus: "available",
    connectionStatus: "open",
    datasetConfigured: true,
    subjectListState: "available",
    subjects: ["S5", "S14"],
    status: fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S14" }),
    inferenceReady: true,
  });
  const goodMap = new Map(good.map((fact) => [fact.id, fact]));
  checkEqual("preflight: exactly ten facts", good.length, 10);
  checkEqual("preflight: backend REST ready when /data-source/state available", goodMap.get("backend-rest")?.state, "ready");
  checkEqual("preflight: websocket ready when open", goodMap.get("websocket")?.state, "ready");
  checkEqual("preflight: architecture definition always ready (bundled constant)", goodMap.get("architecture")?.state, "ready");
  checkEqual("preflight: dataset ready when configured", goodMap.get("dataset")?.state, "ready");
  checkEqual("preflight: subject list ready when available", goodMap.get("subject-list")?.state, "ready");
  checkEqual("preflight: S14 ready when present in subject list", goodMap.get("s14")?.state, "ready");
  checkIncludes("preflight: S14 labelled single-participant robustness demonstration", goodMap.get("s14")?.label ?? "", "single-participant");
  checkEqual("preflight: HR model readiness is Unknown (never fabricated Ready)", goodMap.get("hr-model")?.state, "unknown");
  checkIncludes("preflight: HR model detail states not exposed by current backend contract", goodMap.get("hr-model")?.detail ?? "", "not exposed by current backend contract");
  checkEqual("preflight: fault item ready when no fault active", goodMap.get("active-fault")?.state, "ready");
  checkEqual("preflight: inference ready when a valid prediction exists", goodMap.get("inference")?.state, "ready");

  const degraded = derivePresenterPreflight({
    sourceStateStatus: "error",
    connectionStatus: "closed",
    datasetConfigured: false,
    subjectListState: "error",
    subjects: [],
    status: null,
    inferenceReady: null,
  });
  const degradedMap = new Map(degraded.map((fact) => [fact.id, fact]));
  checkEqual("preflight: backend REST unavailable on request error", degradedMap.get("backend-rest")?.state, "unavailable");
  checkEqual("preflight: websocket unavailable when closed", degradedMap.get("websocket")?.state, "unavailable");
  checkEqual("preflight: dataset not-ready when backend says unconfigured", degradedMap.get("dataset")?.state, "not-ready");
  checkEqual("preflight: subject list unavailable on request error", degradedMap.get("subject-list")?.state, "unavailable");
  checkEqual("preflight: inference Unknown when readiness cannot be determined (never Ready)", degradedMap.get("inference")?.state, "unknown");
  checkEqual("preflight: architecture still ready with backend offline", degradedMap.get("architecture")?.state, "ready");
  checkEqual("preflight: HR model still Unknown with backend offline (not Unavailable-guessed)", degradedMap.get("hr-model")?.state, "unknown");

  const connecting = derivePresenterPreflight({
    sourceStateStatus: "loading",
    connectionStatus: "connecting",
    datasetConfigured: null,
    subjectListState: "loading",
    subjects: [],
    status: null,
    inferenceReady: null,
  });
  const connectingMap = new Map(connecting.map((fact) => [fact.id, fact]));
  checkEqual("preflight: websocket unknown while connecting", connectingMap.get("websocket")?.state, "unknown");
  checkEqual("preflight: dataset unknown before /data-source/state resolves", connectingMap.get("dataset")?.state, "unknown");
  checkEqual("preflight: S14 unknown before subject list resolves", connectingMap.get("s14")?.state, "unknown");

  const noS14 = derivePresenterPreflight({
    sourceStateStatus: "available",
    connectionStatus: "open",
    datasetConfigured: true,
    subjectListState: "available",
    subjects: ["S5", "S6"],
    status: fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S5" }),
    inferenceReady: false,
  });
  const noS14Map = new Map(noS14.map((fact) => [fact.id, fact]));
  checkEqual("preflight: S14 not-applicable when a real subject list omits it (never hard-coded)", noS14Map.get("s14")?.state, "n/a");
  checkEqual("preflight: inference not-ready when no valid prediction yet", noS14Map.get("inference")?.state, "not-ready");

  const faulted = derivePresenterPreflight({
    sourceStateStatus: "available",
    connectionStatus: "open",
    datasetConfigured: true,
    subjectListState: "available",
    subjects: ["S5"],
    status: fixtureDataSourceStatus({
      source_type: "dataset_replay",
      subject_id: "S5",
      fault_injection: fixtureFault({ active: true, target: "ppg", fault_type: "modality_dropout" }),
    }),
    inferenceReady: false,
  });
  const faultedMap = new Map(faulted.map((fact) => [fact.id, fact]));
  checkEqual("preflight: fault item not-ready when a fault is active", faultedMap.get("active-fault")?.state, "not-ready");
}

// ===========================================================================
// Prompt-4 §22 — Demo reset planning + partial-failure honesty.
// ===========================================================================

{
  const synthetic = planDemoReset(fixtureDataSourceStatus({ source_type: "synthetic", subject_id: null }));
  checkEqual("reset plan: synthetic source runs no backend steps", synthetic.steps.length, 0);
  checkEqual("reset plan: always resets modality to PPG", synthetic.resetModalityToPpg, true);
  checkEqual("reset plan: always clears the event history", synthetic.clearEventHistory, true);
  checkEqual("reset plan: always scrolls to top", synthetic.scrollToTop, true);
  checkEqual("reset plan: always preserves source and subject", synthetic.preserveSourceAndSubject, true);

  const playingFaulted = planDemoReset(
    fixtureDataSourceStatus({
      source_type: "dataset_replay",
      subject_id: "S5",
      playback_state: "playing",
      playback_speed: 5,
      fault_injection: fixtureFault({ active: true, target: "ppg", fault_type: "modality_dropout" }),
    }),
  );
  checkEqual("reset plan: playing+fast+faulted → pause,reset,speed-1x,clear-fault", playingFaulted.steps.join(","), "pause,reset,speed-1x,clear-fault");

  const pausedClean = planDemoReset(
    fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: "S5", playback_state: "paused", playback_speed: 1 }),
  );
  checkEqual("reset plan: paused+1x+no-fault → reset only (no redundant calls)", pausedClean.steps.join(","), "reset");

  const noSubject = planDemoReset(fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: null }));
  checkEqual("reset plan: replay configured but no subject → no replay steps", noSubject.steps.length, 0);

  const okResult: DemoResetResult = { ok: true, ranSteps: ["reset"], failedSteps: [] };
  checkIncludes("reset summary: full success says reset complete", summariseDemoReset(okResult), "reset complete");
  const partial: DemoResetResult = { ok: false, ranSteps: ["reset"], failedSteps: ["clear-fault"] };
  checkIncludes("reset summary: partial failure is reported honestly, not as success", summariseDemoReset(partial), "partially failed");
  checkIncludes("reset summary: partial failure names the failed step", summariseDemoReset(partial), "clear-fault");
}

// ===========================================================================
// Stage 3B — canonical jury demo bootstrap: prerequisite gate, step
// sequencing, race safety, and honest summarisation. The prerequisite gate
// and the summary formatter are pure and checked with direct function calls
// (not string matching). The sequencing/race-safety logic in
// `runCanonicalJuryBootstrap` is genuinely behaviorally testable without a
// DOM (it depends only on injected async runners and an `isCurrent()`
// check), so it is exercised with real promise-ordering control via a local
// `deferred()` helper, matching this file's own established convention for
// testing `SourceStateRequestCoordinator`'s race behavior.
// ===========================================================================

{
  function deferred<T>() {
    let resolve!: (value: T) => void;
    let reject!: (reason?: unknown) => void;
    const promise = new Promise<T>((resolvePromise, rejectPromise) => {
      resolve = resolvePromise;
      reject = rejectPromise;
    });
    return { promise, resolve, reject };
  }

  function fixtureStatus(datasetName: string): DataSourceStatus {
    return fixtureDataSourceStatus({ source_type: "dataset_replay", subject_id: CANONICAL_JURY_SUBJECT_ID, dataset_name: datasetName });
  }

  // --- Scenario: arbitrary initial source / prerequisite gate -------------

  checkEqual(
    "canonical bootstrap prereq: dataset not configured is blocked",
    checkCanonicalBootstrapPrerequisites({ datasetConfigured: false, subjectListState: "available", subjects: ["S14"] }).failure,
    "dataset_not_configured",
  );
  checkEqual(
    "canonical bootstrap prereq: dataset-configured unknown (null) is blocked, never inferred ready",
    checkCanonicalBootstrapPrerequisites({ datasetConfigured: null, subjectListState: "available", subjects: ["S14"] }).failure,
    "dataset_not_configured",
  );
  checkEqual(
    "canonical bootstrap prereq: subject list still loading is blocked (missing checkpoint/dataset scenario: never inferred ready from absence of error)",
    checkCanonicalBootstrapPrerequisites({ datasetConfigured: true, subjectListState: "loading", subjects: [] }).failure,
    "subject_list_unavailable",
  );
  checkEqual(
    "canonical bootstrap prereq: subject list error is blocked",
    checkCanonicalBootstrapPrerequisites({ datasetConfigured: true, subjectListState: "error", subjects: [] }).failure,
    "subject_list_unavailable",
  );
  checkEqual(
    "canonical bootstrap prereq: subject list empty is blocked (missing S14 dataset scenario)",
    checkCanonicalBootstrapPrerequisites({ datasetConfigured: true, subjectListState: "empty", subjects: [] }).failure,
    "subject_list_unavailable",
  );
  checkEqual(
    "canonical bootstrap prereq: S14 absent from an otherwise-available subject list is blocked",
    checkCanonicalBootstrapPrerequisites({ datasetConfigured: true, subjectListState: "available", subjects: ["S3", "S8"] }).failure,
    "s14_not_present",
  );
  const readyPrereq = checkCanonicalBootstrapPrerequisites({ datasetConfigured: true, subjectListState: "available", subjects: ["S3", "S14"] });
  checkEqual("canonical bootstrap prereq: dataset configured + S14 present is ready regardless of prior arbitrary source", readyPrereq.ok, true);
  checkEqual("canonical bootstrap prereq: ready result carries no failure code", readyPrereq.failure, null);

  // --- Scenario: full success (two consecutive successful runs) -----------

  async function runSuccess(datasetName: string) {
    return runCanonicalJuryBootstrap(
      {
        loadSubject: async () => fixtureStatus(datasetName),
        reset: async () => fixtureStatus(datasetName),
        setSpeed1x: async () => fixtureStatus(datasetName),
        clearFault: async () => fixtureStatus(datasetName),
      },
      () => true,
    );
  }
  const firstRun = await runSuccess("PPG-DaLiA");
  checkEqual("canonical bootstrap: first successful run completes all 4 steps in order", firstRun.ranSteps.join(","), "load-subject,reset,speed-1x,clear-fault");
  checkEqual("canonical bootstrap: first successful run reports ok", firstRun.ok, true);
  const secondRun = await runSuccess("PPG-DaLiA");
  checkEqual("canonical bootstrap: two consecutive successful runs are both fully successful (idempotent)", secondRun.ok, true);
  checkEqual("canonical bootstrap: two consecutive successful runs both complete all 4 steps", secondRun.ranSteps.length, 4);

  // --- Scenario: failure at each step --------------------------------------

  async function runWithFailureAt(failStep: "load-subject" | "reset" | "speed-1x" | "clear-fault") {
    const runner = (step: string) => async () => {
      if (step === failStep) throw new Error(`${step} failed`);
      return fixtureStatus("PPG-DaLiA");
    };
    return runCanonicalJuryBootstrap(
      {
        loadSubject: runner("load-subject"),
        reset: runner("reset"),
        setSpeed1x: runner("speed-1x"),
        clearFault: runner("clear-fault"),
      },
      () => true,
    );
  }
  const loadFailure = await runWithFailureAt("load-subject");
  checkEqual("canonical bootstrap: load-subject failure aborts remaining steps (nothing else can be trusted)", loadFailure.ranSteps.length, 0);
  checkEqual("canonical bootstrap: load-subject failure is recorded", loadFailure.failedSteps.join(","), "load-subject");
  checkEqual("canonical bootstrap: load-subject failure is not ok", loadFailure.ok, false);

  const resetFailure = await runWithFailureAt("reset");
  checkEqual("canonical bootstrap: reset-step failure still records the completed load-subject step", resetFailure.ranSteps.includes("load-subject"), true);
  checkEqual("canonical bootstrap: reset-step failure still attempts speed-1x and clear-fault after it", resetFailure.ranSteps.includes("speed-1x") && resetFailure.ranSteps.includes("clear-fault"), true);
  checkEqual("canonical bootstrap: reset-step failure is recorded and not silently dropped", resetFailure.failedSteps.join(","), "reset");

  const speedFailure = await runWithFailureAt("speed-1x");
  checkEqual("canonical bootstrap: speed-1x failure is recorded", speedFailure.failedSteps.join(","), "speed-1x");
  checkEqual("canonical bootstrap: speed-1x failure still runs clear-fault after it", speedFailure.ranSteps.includes("clear-fault"), true);

  const faultFailure = await runWithFailureAt("clear-fault");
  checkEqual("canonical bootstrap: clear-fault failure is recorded as the sole failure", faultFailure.failedSteps.join(","), "clear-fault");
  checkEqual("canonical bootstrap: clear-fault failure still ran all 3 prior steps", faultFailure.ranSteps.length, 3);

  // --- Scenario: retry after failure ---------------------------------------

  let loadAttempts = 0;
  const retrySequence = runCanonicalJuryBootstrap(
    {
      loadSubject: async () => {
        loadAttempts += 1;
        if (loadAttempts === 1) throw new Error("transient failure");
        return fixtureStatus("PPG-DaLiA");
      },
      reset: async () => fixtureStatus("PPG-DaLiA"),
      setSpeed1x: async () => fixtureStatus("PPG-DaLiA"),
      clearFault: async () => fixtureStatus("PPG-DaLiA"),
    },
    () => true,
  );
  const firstAttempt = await retrySequence;
  checkEqual("canonical bootstrap retry: first attempt fails at load-subject", firstAttempt.ok, false);
  const retryAttempt = await runSuccess("PPG-DaLiA");
  checkEqual("canonical bootstrap retry: explicit retry after failure succeeds fully", retryAttempt.ok, true);

  // --- Scenario: race safety — superseded mid-sequence (owner transfer /
  // unmounted control / a second concurrent invocation all reduce to the
  // same "isCurrent() becomes false mid-loop" shape) --------------------

  const stepOrder: string[] = [];
  let stillCurrent = true;
  const supersededRun = runCanonicalJuryBootstrap(
    {
      loadSubject: async () => {
        stepOrder.push("load-subject");
        return fixtureStatus("PPG-DaLiA");
      },
      reset: async () => {
        stepOrder.push("reset");
        // Simulate an owner transfer / unmount / second invocation
        // superseding this sequence right after the first step resolves,
        // before the second step is even attempted.
        stillCurrent = false;
        return fixtureStatus("PPG-DaLiA");
      },
      setSpeed1x: async () => {
        stepOrder.push("speed-1x");
        return fixtureStatus("PPG-DaLiA");
      },
      clearFault: async () => {
        stepOrder.push("clear-fault");
        return fixtureStatus("PPG-DaLiA");
      },
    },
    () => stillCurrent,
  );
  const supersededResult = await supersededRun;
  checkEqual("canonical bootstrap race safety: superseded sequence stops issuing requests immediately", stepOrder.join(","), "load-subject,reset");
  checkEqual("canonical bootstrap race safety: superseded sequence never reaches speed-1x/clear-fault", stepOrder.includes("speed-1x") || stepOrder.includes("clear-fault"), false);
  checkEqual("canonical bootstrap race safety: superseded sequence records only what actually ran", supersededResult.ranSteps.join(","), "load-subject,reset");

  // Two genuinely concurrent invocations sharing one `isCurrent` flag that a
  // second call flips false for the first — proves a stale in-flight
  // sequence's tail can never keep issuing requests after a newer
  // invocation starts (the coordinator itself additionally guarantees the
  // stale sequence's final status can never be *applied*; that guarantee is
  // covered by SourceStateRequestCoordinator's own extensive tests above,
  // since `loadCanonicalJuryDemo` gates its final `acceptAuthoritativeMutation`
  // call through the exact same ticket mechanism `resetDemoState` uses).
  const concurrentDeferred = deferred<DataSourceStatus>();
  let firstStillCurrent = true;
  const concurrentFirstOrder: string[] = [];
  const firstInvocation = runCanonicalJuryBootstrap(
    {
      loadSubject: async () => {
        concurrentFirstOrder.push("load-subject");
        return concurrentDeferred.promise;
      },
      reset: async () => {
        concurrentFirstOrder.push("reset");
        return fixtureStatus("PPG-DaLiA");
      },
      setSpeed1x: async () => {
        concurrentFirstOrder.push("speed-1x");
        return fixtureStatus("PPG-DaLiA");
      },
      clearFault: async () => {
        concurrentFirstOrder.push("clear-fault");
        return fixtureStatus("PPG-DaLiA");
      },
    },
    () => firstStillCurrent,
  );
  // Second invocation "wins" (as a real second beginAuthoritativeMutation
  // call would), superseding the first before its load-subject resolves.
  firstStillCurrent = false;
  concurrentDeferred.resolve(fixtureStatus("PPG-DaLiA"));
  const firstInvocationResult = await firstInvocation;
  checkEqual("canonical bootstrap race safety: a superseded concurrent invocation never proceeds past its in-flight step", concurrentFirstOrder.join(","), "load-subject");
  checkEqual("canonical bootstrap race safety: superseded concurrent invocation's ranSteps reflects only the one step that had already started", firstInvocationResult.ranSteps.join(","), "load-subject");

  // --- Scenario: correct accessible announcements (no unsupported EEG/EOG
  // creation is architectural — runCanonicalJuryBootstrap only ever calls the
  // 4 replay/fault runners it is given, never touches modality data) -------

  const blockedResult: CanonicalBootstrapResult = { ok: false, blockedOnPrerequisite: "s14_not_present", blockedDetail: "Subject S14 is not present in the current replay subject list.", ranSteps: [], failedSteps: [] };
  const blockedSummary = summariseCanonicalBootstrap(blockedResult);
  checkIncludes("canonical bootstrap summary: prerequisite block names the exact missing prerequisite", blockedSummary, "S14 is not present");
  checkIncludes("canonical bootstrap summary: prerequisite block explicitly says not loaded", blockedSummary, "not loaded");
  checkEqual("canonical bootstrap summary: prerequisite block never claims success", /demo loaded —/.test(blockedSummary), false);

  const successResult: CanonicalBootstrapResult = { ok: true, blockedOnPrerequisite: null, blockedDetail: null, ranSteps: ["load-subject", "reset", "speed-1x", "clear-fault"], failedSteps: [] };
  const successSummary = summariseCanonicalBootstrap(successResult);
  checkIncludes("canonical bootstrap summary: full success names the canonical subject", successSummary, CANONICAL_JURY_SUBJECT_ID);
  checkIncludes("canonical bootstrap summary: full success mentions 1x speed", successSummary, "1×");

  const partialResult: CanonicalBootstrapResult = { ok: false, blockedOnPrerequisite: null, blockedDetail: null, ranSteps: ["load-subject", "reset"], failedSteps: ["speed-1x"] };
  const partialSummary = summariseCanonicalBootstrap(partialResult);
  checkIncludes("canonical bootstrap summary: partial failure is reported honestly, not as success", partialSummary, "partially failed");
  checkIncludes("canonical bootstrap summary: partial failure names the failed step", partialSummary, "speed-1x");

  const unexpectedResult: CanonicalBootstrapResult = { ok: false, blockedOnPrerequisite: null, blockedDetail: null, ranSteps: [], failedSteps: [] };
  const unexpectedSummary = summariseCanonicalBootstrap(unexpectedResult);
  checkEqual("canonical bootstrap summary: unexpected failure (no named step) never says loaded/complete", /loaded —|complete/.test(unexpectedSummary), false);
}

// ===========================================================================
// Prompt-4 §26 — Architecture separation + claim safety (canonical constants
// remain the single source of these frozen decisions).
// ===========================================================================

{
  checkEqual("architecture: final id is CORE_PLUS_CONTEXT", FINAL_ARCHITECTURE_ID, "CORE_PLUS_CONTEXT");
  const finalModalities = FINAL_SENSOR_INVENTORY.map((entry) => entry.modality) as string[];
  checkEqual("architecture: final sensor set is exactly PPG,IMU,ECG,EEG,EOG", finalModalities.join(","), "PPG,IMU,ECG,EEG,EOG");
  check("architecture: BioZ is NOT a final-system health modality", !finalModalities.includes("BioZ"));
  check("architecture: temperature is NOT a final-system health modality", !finalModalities.map((m) => m.toLowerCase()).includes("temperature"));
  checkNotIncludes("architecture: MINIMAL_CORE summary excludes EOG", MINIMAL_CORE_SUMMARY, "EOG");
  checkIncludes("architecture: CORE_PLUS_CONTEXT summary includes EOG", CORE_PLUS_CONTEXT_SUMMARY, "EOG");
  checkIncludes("architecture: EOG is the sole addition beyond MINIMAL_CORE", EOG_DELTA_NOTE, "sole modality added beyond MINIMAL_CORE");

  checkIncludes("claim safety: S14 statement is single-participant", S14_SCOPE_STATEMENT, "single-participant");
  checkIncludes("claim safety: S14 statement denies population validation", S14_SCOPE_STATEMENT, "not population validation");
  checkIncludes("claim safety: digital twin label says untrained", DIGITAL_TWIN_SCOPE_LABEL, "untrained");
  checkIncludes("claim safety: digital twin label says unvalidated", DIGITAL_TWIN_SCOPE_LABEL, "unvalidated");
  checkIncludes("claim safety: engineering burden is bounded estimates", BOUNDED_ESTIMATE_QUALIFIER, "Bounded engineering estimates");
  checkIncludes("claim safety: dashboard values are not scientific Results", DASHBOARD_VS_RESULTS_STATEMENT, "not the source of scientific Results");
  checkIncludes("claim safety: BioZ excluded from final architecture", BIOZ_EXCLUSION_STATEMENT, "not carried into the final CORE_PLUS_CONTEXT architecture");

  const expSource = readFileSync(join(REPO_SRC_ROOT, "app/research/experimental/page.tsx"), "utf8");
  check("claim safety: /research/experimental retains BioZ evidence content", expSource.includes("BioZEvidenceSection"));
  const twinSource = readFileSync(join(REPO_SRC_ROOT, "app/digital-twin/page.tsx"), "utf8");
  check("claim safety: /digital-twin retains untrained/unvalidated scope language", /untrained|unvalidated|architecture only/i.test(twinSource));
}

// ===========================================================================
// Prompt-4A HIGH-1 — reduced-motion persisted-value encoding. The accepted set
// is asserted directly (not by string-matching layout.tsx), plus a structural
// check that the boot script mirrors the same acceptance set.
// ===========================================================================

{
  checkEqual('reduce-motion: "1" (value Settings writes) enables', reduceMotionEnabledFromStorage("1"), true);
  checkEqual('reduce-motion: legacy "true" still enables', reduceMotionEnabledFromStorage("true"), true);
  checkEqual('reduce-motion: "0" does not enable', reduceMotionEnabledFromStorage("0"), false);
  checkEqual('reduce-motion: "false" does not enable', reduceMotionEnabledFromStorage("false"), false);
  checkEqual("reduce-motion: null (absent) does not enable", reduceMotionEnabledFromStorage(null), false);
  checkEqual("reduce-motion: undefined does not enable", reduceMotionEnabledFromStorage(undefined), false);
  checkEqual('reduce-motion: empty string does not enable', reduceMotionEnabledFromStorage(""), false);
  checkEqual('reduce-motion: unexpected "yes" does not enable', reduceMotionEnabledFromStorage("yes"), false);

  const layoutSource = readFileSync(join(REPO_SRC_ROOT, "app/layout.tsx"), "utf8");
  check("reduce-motion: boot script accepts '1'", layoutSource.includes("v==='1'"));
  check("reduce-motion: boot script accepts legacy 'true'", layoutSource.includes("v==='true'"));
  check("reduce-motion: boot script removes the class when not enabled", layoutSource.includes("classList.remove('reduce-motion')"));

  const settingsSource = readFileSync(join(REPO_SRC_ROOT, "app/settings/page.tsx"), "utf8");
  check("reduce-motion: Settings reads through the shared predicate", settingsSource.includes("reduceMotionEnabledFromStorage"));
}

// ===========================================================================
// Prompt-4A HIGH-2 — reset summary never announces success on an unexpected
// failure. The exact {ok:false, ranSteps:[], failedSteps:[]} case is asserted.
// ===========================================================================

{
  const fullSuccess = summariseDemoReset({ ok: true, ranSteps: ["reset"], failedSteps: [] });
  checkIncludes("reset summary: ok+no-failures says complete", fullSuccess, "complete");

  const partial = summariseDemoReset({ ok: false, ranSteps: ["reset"], failedSteps: ["clear-fault"] });
  checkIncludes("reset summary: named partial failure is honest", partial, "partially failed");
  checkIncludes("reset summary: named partial failure lists the step", partial, "clear-fault");
  // (The partial message legitimately contains "did not complete"; the
  // no-"complete" invariant applies specifically to the unexpected-failure
  // case below, which must never imply success.)

  const unexpected = summariseDemoReset({ ok: false, ranSteps: [], failedSteps: [] });
  checkIncludes("reset summary: unexpected failure is announced as failed", unexpected, "failed unexpectedly");
  checkNotIncludes("reset summary: unexpected failure never says complete", unexpected, "complete");
  checkEqual("reset summary: ok:false empty failedSteps is not treated as success", unexpected.includes("complete"), false);

  // Structural: the drawer clears `resetting` in a finally and derives the
  // announcement from summariseDemoReset (never a hard-coded success string).
  const drawerSource = readFileSync(join(REPO_SRC_ROOT, "components/operations/DemoControlDrawer.tsx"), "utf8");
  check("reset: drawer clears resetting in a finally block", /finally\s*\{[\s\S]*setResetting\(false\)/.test(drawerSource));
  check("reset: drawer announces via summariseDemoReset", drawerSource.includes("summariseDemoReset(result)"));
}

// ===========================================================================
// Prompt-4A HIGH-3 — public Settings route exposes no endpoint constants,
// no shell/uvicorn instructions, and no localhost URLs.
// ===========================================================================

{
  const settingsSource = readFileSync(join(REPO_SRC_ROOT, "app/settings/page.tsx"), "utf8");
  checkNotIncludes("settings: no API_BASE_URL in public route", settingsSource, "API_BASE_URL");
  checkNotIncludes("settings: no WS_URL in public route", settingsSource, "WS_URL");
  checkNotIncludes("settings: no uvicorn instruction", settingsSource, "uvicorn");
  checkNotIncludes("settings: no app.main reference", settingsSource, "app.main");
  checkNotIncludes("settings: no localhost URL", settingsSource, "localhost");
  checkNotIncludes("settings: does not import @/lib/config endpoint constants", settingsSource, "@/lib/config");
  checkIncludes("settings: composed telemetry-unavailable copy present", settingsSource, "telemetry service is unavailable");
}

// ===========================================================================
// Prompt-4A MEDIUM-1 — modal background isolation is implemented via a portal
// plus managed inert/aria-hidden with exact restoration (structural proof;
// activation/cleanup is also verified live in the browser QA).
//
// Stage 2 A3 update: this logic no longer lives inline in
// DemoControlDrawer.tsx — it was extracted into the shared
// useModalDialog() hook (lib/runtime/useModalDialog.ts) so the mobile
// "More" sheet (MobileNav.tsx) could reuse the same tested primitive
// instead of reimplementing its own (weaker) version. DemoControlDrawer.tsx
// now only needs to portal its overlay and call the shared hook; the
// inert/aria-hidden/scroll-lock/focus-restoration behavior itself is
// asserted against the hook file, and scripts/verify-modal-dialog-
// primitives.mjs (part of `verify:monitoring`) separately proves both
// consumers actually call it and portal to document.body.
// ===========================================================================

{
  const drawerSource = readFileSync(join(REPO_SRC_ROOT, "components/operations/DemoControlDrawer.tsx"), "utf8");
  const modalHookSource = readFileSync(join(REPO_SRC_ROOT, "lib/runtime/useModalDialog.ts"), "utf8");
  check("modal: overlay is portaled to document.body", drawerSource.includes("createPortal(overlay, document.body)"));
  check("modal: drawer uses the shared useModalDialog() hook", drawerSource.includes("useModalDialog({"));
  check("modal: background siblings are set inert while open", modalHookSource.includes('setAttribute("inert"'));
  check("modal: background siblings are set aria-hidden while open", modalHookSource.includes('setAttribute("aria-hidden", "true")'));
  check("modal: prior inert state is restored (no stale inert)", modalHookSource.includes('removeAttribute("inert")'));
  check("modal: prior aria-hidden state is restored", modalHookSource.includes('removeAttribute("aria-hidden")'));
  check("modal: focus restored to trigger after inert cleared", /for \(const restore of restores\) restore\(\);[\s\S]*trigger\?\.focus\(\)/.test(modalHookSource));
  check("modal: document scroll is locked while open", modalHookSource.includes('document.body.style.overflow = "hidden"'));
}

// ===========================================================================
// Corrective review residual 2 — behavioral control-surface derivation.
// Covers active, loading, REST error, disconnected, no confirmed frame, and
// identity-mismatch-awaiting-convergence without mounting client components.
// ===========================================================================

{
  const activeTelemetry = deriveTelemetryAvailability({ connected: true, sourceStateStatus: "available", hasConfirmedSnapshot: true });
  const unavailableCases = [
    {
      name: "source loading",
      telemetry: deriveTelemetryAvailability({ connected: true, sourceStateStatus: "loading", hasConfirmedSnapshot: true }),
    },
    {
      name: "REST source error",
      telemetry: deriveTelemetryAvailability({ connected: true, sourceStateStatus: "error", hasConfirmedSnapshot: true }),
    },
    {
      name: "disconnected",
      telemetry: deriveTelemetryAvailability({ connected: false, sourceStateStatus: "available", hasConfirmedSnapshot: true }),
    },
    {
      name: "no confirmed frame",
      telemetry: deriveTelemetryAvailability({ connected: true, sourceStateStatus: "available", hasConfirmedSnapshot: false }),
    },
    {
      name: "identity mismatch awaiting REST convergence",
      telemetry: deriveTelemetryAvailability({ connected: true, sourceStateStatus: "available", hasConfirmedSnapshot: false }),
    },
  ] as const;

  const activeReplay = deriveReplayControlPresentation({
    telemetry: activeTelemetry,
    isReplay: true,
    replaySessionState: "playing",
    playbackSpeed: 5,
    replayPositionSeconds: 42,
    replayDurationSeconds: 120,
    subjectId: "S14",
    pendingAction: null,
  });
  checkEqual("controls residual 2: active replay preserves current subject", activeReplay.activeSubjectId, "S14");
  checkEqual("controls residual 2: active replay preserves current speed", activeReplay.playbackSpeed, 5);
  checkEqual("controls residual 2: active replay preserves current position", activeReplay.replayPositionSeconds, 42);
  checkEqual("controls residual 2: active replay permits playback mutations", activeReplay.canControlPlayback, true);
  checkEqual("controls residual 2: active playing replay permits play action", activeReplay.canPlay, true);
  checkEqual("controls residual 2: active replay permits source change", activeReplay.canChangeSource, true);

  const activeFault = deriveFaultControlPresentation({
    telemetry: activeTelemetry,
    isReplay: true,
    fault: fixtureFault({ active: true, target: "ppg", fault_type: "modality_dropout", severity: 1 }),
    pendingAction: null,
  });
  checkEqual("controls residual 2: active confirmed fault remains current", activeFault.faultActive, true);
  checkEqual("controls residual 2: active confirmed replay permits fault application", activeFault.canApply, true);
  checkEqual("controls residual 2: active confirmed fault permits clear", activeFault.canClear, true);
  checkIncludes("controls residual 2: active confirmed fault label remains specific", activeFault.currentFaultLabel, "Simulated fault active — PPG");

  for (const unavailableCase of unavailableCases) {
    const replay = deriveReplayControlPresentation({
      telemetry: unavailableCase.telemetry,
      isReplay: true,
      replaySessionState: "playing",
      playbackSpeed: 10,
      replayPositionSeconds: 99,
      replayDurationSeconds: 120,
      subjectId: "RETAINED_SUBJECT",
      pendingAction: null,
    });
    checkEqual(`controls residual 2 (${unavailableCase.name}): replay is not authoritative`, replay.authoritativeCurrent, false);
    check(`controls residual 2 (${unavailableCase.name}): unavailable messaging is explicit`, replay.unavailableMessage !== null && replay.playbackStateLabel.includes("Not currently confirmed"));
    checkEqual(`controls residual 2 (${unavailableCase.name}): retained subject is absent from current presentation`, replay.activeSubjectId, null);
    checkEqual(`controls residual 2 (${unavailableCase.name}): retained speed is absent`, replay.playbackSpeed, null);
    checkEqual(`controls residual 2 (${unavailableCase.name}): retained position is absent`, replay.replayPositionSeconds, null);
    checkEqual(`controls residual 2 (${unavailableCase.name}): retained duration is absent`, replay.replayDurationSeconds, null);
    checkEqual(`controls residual 2 (${unavailableCase.name}): playback mutations are disabled`, replay.canControlPlayback, false);
    checkEqual(`controls residual 2 (${unavailableCase.name}): play is disabled`, replay.canPlay, false);
    checkEqual(`controls residual 2 (${unavailableCase.name}): source-changing actions are disabled`, replay.canChangeSource, false);

    const fault = deriveFaultControlPresentation({
      telemetry: unavailableCase.telemetry,
      isReplay: true,
      fault: fixtureFault({ active: true, target: "ppg", fault_type: "modality_dropout", severity: 1 }),
      pendingAction: null,
    });
    checkEqual(`controls residual 2 (${unavailableCase.name}): stale fault is not current`, fault.faultActive, false);
    checkEqual(`controls residual 2 (${unavailableCase.name}): fault apply is disabled`, fault.canApply, false);
    checkEqual(`controls residual 2 (${unavailableCase.name}): fault clear is disabled`, fault.canClear, false);
    checkIncludes(`controls residual 2 (${unavailableCase.name}): fault state is explicitly unconfirmed`, fault.currentFaultLabel, "not currently confirmed");
    checkNotIncludes(`controls residual 2 (${unavailableCase.name}): no false no-fault assertion`, fault.currentFaultLabel, "No simulated fault is active");
    checkNotIncludes(`controls residual 2 (${unavailableCase.name}): stale PPG fault detail is withheld`, fault.currentFaultLabel, "Simulated PPG");
  }

  const pendingReplay = deriveReplayControlPresentation({
    telemetry: activeTelemetry,
    isReplay: true,
    replaySessionState: "paused",
    playbackSpeed: 1,
    replayPositionSeconds: 1,
    replayDurationSeconds: 2,
    subjectId: "S14",
    pendingAction: "play",
  });
  checkEqual("controls residual 2: pending action disables otherwise-active playback mutations", pendingReplay.canControlPlayback, false);

  const activeNoFault = deriveFaultControlPresentation({ telemetry: activeTelemetry, isReplay: true, fault: fixtureFault({ active: false }), pendingAction: null });
  checkEqual("controls residual 2: no-fault assertion is allowed only while authoritative state is active", activeNoFault.currentFaultLabel, "No simulated fault is active.");
}

// ===========================================================================
// Corrective package 01 — F-01 cross-route authoritative telemetry gate.
// Structural checks complement (but do not replace) behavioral derivations.
// ===========================================================================

{
  const liveComponents = [
    "components/monitoring/MonitoringSourceStrip.tsx",
    "components/monitoring/FinalSignalStack.tsx",
    "components/monitoring/HrInferencePanel.tsx",
    "components/monitoring/ScopeProvenanceFooter.tsx",
  ];
  for (const relativePath of liveComponents) {
    const source = readFileSync(join(REPO_SRC_ROOT, relativePath), "utf8");
    check(`live F-01: ${relativePath} consumes the shared operational view model`, source.includes("useOperationalViewModel"));
    check(`live F-01: ${relativePath} has no direct confirmed-snapshot fallback`, !source.includes('from "@/lib/monitoring/useConfirmedSnapshot"'));
  }
  const sourceStrip = readFileSync(join(REPO_SRC_ROOT, "components/monitoring/MonitoringSourceStrip.tsx"), "utf8");
  checkIncludes("live F-01: source strip renders authoritative replay-state label", sourceStrip, "view.replaySessionStateLabel");
  checkIncludes("live F-01: source strip gates replay position on active telemetry", sourceStrip, 'view.telemetryAvailability === "active"');
  checkIncludes("live F-01: source strip labels retained identity through semantic helper", sourceStrip, "deriveIdentityContextDisplay");
  checkIncludes("live F-01: source strip labels retained source identity as configuration", sourceStrip, "Source context");

  const hrPanel = readFileSync(join(REPO_SRC_ROOT, "components/monitoring/HrInferencePanel.tsx"), "utf8");
  checkIncludes("live F-01: HR panel displays source-error/disconnect reason from authoritative gate", hrPanel, "telemetryAvailabilityLabel");
  checkNotIncludes("live F-01: HR panel no longer derives availability from bare WebSocket connected state", hrPanel, "derivePredictionAvailability");

  const provenanceFooter = readFileSync(join(REPO_SRC_ROOT, "components/monitoring/ScopeProvenanceFooter.tsx"), "utf8");
  checkIncludes("live F-01: provenance source context says it is not current telemetry", provenanceFooter, "retained configuration context, not current telemetry");

  const operationalModel = readFileSync(join(REPO_SRC_ROOT, "lib/monitoring/operationalViewModel.ts"), "utf8");
  checkIncludes(
    "live F-01: status fallback is allowed only after authoritative REST availability and without pending identity convergence",
    operationalModel,
    "&& sourceConvergenceKey === null",
  );

  const replayControlSource = readFileSync(join(REPO_SRC_ROOT, "components/monitoring/ReplaySessionControl.tsx"), "utf8");
  const faultControlSource = readFileSync(join(REPO_SRC_ROOT, "components/monitoring/SimulatedFaultControl.tsx"), "utf8");
  checkIncludes("controls residual 2: replay component is wired to tested controller derivation", replayControlSource, "deriveReplayControlPresentation");
  checkIncludes("controls residual 2: fault component is wired to tested controller derivation", faultControlSource, "deriveFaultControlPresentation");

  const sessionProviderSource = readFileSync(join(REPO_SRC_ROOT, "components/monitoring/MonitoringSessionContext.tsx"), "utf8");
  checkIncludes("convergence residual 1: full-route REST owner watches mismatch convergence key", sessionProviderSource, "sourceConvergenceKey");
  checkIncludes("convergence residual 1: full-route REST owner uses tested shared request coordinator", sessionProviderSource, "sourceStateRequestCoordinator");
  checkIncludes("event ordering B: full-route owner uses adoptable physical request lifecycle", sessionProviderSource, "startOrAdoptRequest");
  checkIncludes("event ordering B: full-route owner registers its active result callback", sessionProviderSource, "applyDataSourceStatus(result)");
  checkIncludes("mutation ordering: full-route controls use shared mutation generations", sessionProviderSource, "startAuthoritativeMutation");

  const liveFeedProviderSource = readFileSync(join(REPO_SRC_ROOT, "components/layout/LiveFeedProvider.tsx"), "utf8");
  checkIncludes("cross-route convergence: legacy live-feed REST owner watches the shared pending key", liveFeedProviderSource, "sourceConvergenceKey");
  checkIncludes("cross-route convergence: legacy live-feed REST owner uses tested shared request coordinator", liveFeedProviderSource, "sourceStateRequestCoordinator");
  checkIncludes("event ordering B: legacy owner uses adoptable physical request lifecycle", liveFeedProviderSource, "startOrAdoptRequest");
  checkIncludes("event ordering B: legacy owner registers its active store callback", liveFeedProviderSource, "setDataSourceStatus");
  checkIncludes("mutation ordering: legacy provider binds mutations to its owner token", liveFeedProviderSource, "startAuthoritativeMutation");
  checkNotIncludes("cross-route convergence: legacy owner no longer refetches from every observed identity change", liveFeedProviderSource, "observedSourceIdentityKey");

  const dataSourceControlSource = readFileSync(join(REPO_SRC_ROOT, "components/demos/DataSourceControl.tsx"), "utf8");
  checkIncludes("mutation ordering: DataSourceControl consumes scoped legacy mutation lifecycle", dataSourceControlSource, "useLegacyAuthoritativeMutation");
  checkIncludes("mutation ordering: DataSourceControl writes only inside accepted mutation callback", dataSourceControlSource, "startAuthoritativeMutation(");
  checkNotIncludes("mutation ordering: DataSourceControl no longer awaits an uncoordinated operation", dataSourceControlSource, "const result = await operation()");
}

// ===========================================================================
// Corrective package 01 — F-02 missing confidence/HR semantics.
// ===========================================================================

{
  const missingConfidence = deriveConfidenceDisplay(null);
  const undefinedConfidence = deriveConfidenceDisplay(undefined);
  const zeroConfidence = deriveConfidenceDisplay(0);
  const presentConfidence = deriveConfidenceDisplay(82);
  checkEqual("AI F-02: null confidence is unavailable", missingConfidence.kind, "unavailable");
  checkEqual("AI F-02: undefined confidence is unavailable", undefinedConfidence.kind, "unavailable");
  checkEqual("AI F-02: unavailable confidence uses offline tone", missingConfidence.level, "offline");
  check("AI F-02: genuine numeric zero remains available", zeroConfidence.kind === "available" && zeroConfidence.value === 0);
  check("AI F-02: present confidence retains numeric value and intended nominal level", presentConfidence.kind === "available" && presentConfidence.value === 82 && presentConfidence.level === "nominal");
  checkEqual("AI F-02: missing synthetic HR uses offline tone", metricLevelForAvailability(null), "offline");
  checkEqual("AI F-02: undefined synthetic HR uses offline tone", metricLevelForAvailability(undefined), "offline");
  checkEqual("AI F-02: genuine zero HR remains a present numeric value", metricLevelForAvailability(0), "nominal");
  checkEqual("AI F-02: present HR retains nominal behavior", metricLevelForAvailability(72), "nominal");

  for (const [name, value] of [
    ["null", null],
    ["undefined", undefined],
    ["NaN", Number.NaN],
    ["positive infinity", Number.POSITIVE_INFINITY],
    ["negative infinity", Number.NEGATIVE_INFINITY],
  ] as const) {
    checkEqual(`vitals residual 3: ${name} scalar is unavailable/offline`, metricLevelForAvailability(value), "offline");
    checkEqual(`vitals residual 3: ${name} scalar is not a finite display value`, isFiniteMetricValue(value), false);
  }
  checkEqual("vitals residual 3: genuine finite zero scalar remains present", isFiniteMetricValue(0), true);
  checkEqual("vitals residual 3: genuine finite zero scalar retains normal existing level", metricLevelForAvailability(0), "nominal");
  checkEqual("vitals residual 3: valid finite scalar retains normal existing level", metricLevelForAvailability(18.5), "nominal");
  checkEqual("vitals residual 3: complete finite blood-pressure pair is present", metricGroupLevelForAvailability([120, 80]), "nominal");
  checkEqual("vitals residual 3: finite zero pair remains present rather than missing", metricGroupLevelForAvailability([0, 0]), "nominal");
  checkEqual("vitals residual 3: null systolic makes combined blood pressure unavailable", metricGroupLevelForAvailability([null, 80]), "offline");
  checkEqual("vitals residual 3: undefined diastolic makes combined blood pressure unavailable", metricGroupLevelForAvailability([120, undefined]), "offline");
  checkEqual("vitals residual 3: non-finite systolic makes combined blood pressure unavailable", metricGroupLevelForAvailability([Number.NaN, 80]), "offline");
  checkEqual("vitals residual 3: non-finite diastolic makes combined blood pressure unavailable", metricGroupLevelForAvailability([120, Number.POSITIVE_INFINITY]), "offline");
  checkEqual("vitals residual 3: empty metric group is unavailable", metricGroupLevelForAvailability([]), "offline");

  const confidencePanel = readFileSync(join(REPO_SRC_ROOT, "components/panels/AIConfidencePanel.tsx"), "utf8");
  checkNotIncludes("AI F-02: confidence panel never maps missing confidence to zero", confidencePanel, "overall_confidence ?? 0");
  checkIncludes("AI F-02: confidence panel has explicit screen-reader unavailable text", confidencePanel, 'aria-label="Overall Confidence: Unavailable"');
  check("AI F-02: gauge is conditional on an available numeric value", /overall\.kind === "available"[\s\S]*<RadialGauge/.test(confidencePanel));

  const vitalsPanel = readFileSync(join(REPO_SRC_ROOT, "components/panels/PrimaryVitalsPanel.tsx"), "utf8");
  checkIncludes("AI F-02: primary vitals derives missing-value tone explicitly", vitalsPanel, "metricLevelForAvailability(heartRate)");
  checkIncludes("AI F-02: recorded replay label remains distinct", vitalsPanel, "Recorded replay");
  checkIncludes("AI F-02: inferred PPG+IMU label remains distinct", vitalsPanel, "PPG + IMU heart-rate estimate");
  checkIncludes("AI F-02: unavailable label remains explicit", vitalsPanel, '"Unavailable"');
  checkIncludes("AI F-02: synthetic panel label remains distinct", vitalsPanel, "Cardiovascular & respiratory");
  checkIncludes("vitals residual 3: HRV tile receives explicit availability level", vitalsPanel, "level={metricLevelForAvailability(hrv)}");
  checkIncludes("vitals residual 3: respiration tile receives explicit availability level", vitalsPanel, "level={metricLevelForAvailability(respiration)}");
  checkIncludes("vitals residual 3: combined blood-pressure tile receives group availability level", vitalsPanel, "level={metricGroupLevelForAvailability([systolic, diastolic])}");
}

// ===========================================================================
// Corrective package 01 — F-03 Mission Timeline Digital Twin truth boundary.
// ===========================================================================

{
  const timelineSource = readFileSync(join(REPO_SRC_ROOT, "app/mission-timeline/page.tsx"), "utf8");
  checkNotIncludes("timeline F-03: unsafe % Adapted label is absent", timelineSource, "% Adapted");
  checkNotIncludes("timeline F-03: legacy overall_adaptation is never rendered", timelineSource, "overall_adaptation");
  checkNotIncludes("timeline F-03: legacy narrative is never rendered", timelineSource, ".narrative");
  checkNotIncludes("timeline F-03: no success/health badge is derived from a missing legacy field", timelineSource, "StatusBadge");
  checkIncludes("timeline F-03: architecture-only boundary is persistent", timelineSource, "Architecture only");
  checkIncludes("timeline F-03: untrained boundary is explicit", timelineSource, "untrained");
  checkIncludes("timeline F-03: unvalidated boundary is explicit", timelineSource, "unvalidated");
  checkIncludes("timeline F-03: not-personalized boundary is explicit", timelineSource, "not personalized");
  checkIncludes("timeline F-03: milestones are explicitly conceptual rather than measured", timelineSource, "Conceptual marker — not a measured outcome");
  checkIncludes("timeline F-03: valid legacy payload path suppresses quantitative fields", timelineSource, "quantitative fields are intentionally suppressed");
  checkIncludes("timeline F-03: unavailable/error path infers no model state", timelineSource, "Conceptual scenario data unavailable; no model state is inferred.");
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
