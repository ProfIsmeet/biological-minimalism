/**
 * Prompt-4 Part VI (§21, §22) — presenter-reliability primitives.
 *
 * PURE logic only (no React, no api, no browser) so the preflight semantics
 * and the reset plan are asserted deterministically in
 * scripts/verify-monitoring-state.ts. The DemoControlDrawer and the
 * MonitoringSessionContext are thin shells that render / execute these
 * results; every truth decision lives here.
 */

import type { DataSourceStatus } from "@/lib/types";

// ---------------------------------------------------------------------------
// §21 — Presenter preflight
// ---------------------------------------------------------------------------

/**
 * The five allowed states (§21). "unknown" is the honest answer when the
 * current backend contract does not expose the fact — it is NEVER inferred to
 * "ready" from the mere absence of an error.
 */
export type PreflightState = "ready" | "not-ready" | "unavailable" | "unknown" | "n/a";

export interface PreflightFact {
  id: string;
  label: string;
  state: PreflightState;
  detail: string;
}

export type SourceStateStatus = "loading" | "available" | "error";
export type SubjectListState = "loading" | "available" | "empty" | "error";
export type ConnectionStatus = "connecting" | "open" | "closed";

export interface PreflightInputs {
  /** `/data-source/state` fetch health (MonitoringSession). */
  sourceStateStatus: SourceStateStatus;
  /** Live-feed WebSocket state (missionStore). */
  connectionStatus: ConnectionStatus;
  /** Whether the backend reports a replay dataset is configured. */
  datasetConfigured: boolean | null;
  /** `/data-source/subjects` fetch health. */
  subjectListState: SubjectListState;
  /** Returned subject ids (authoritative for the S14 item). */
  subjects: string[];
  /** Latest authoritative source status, or null before it resolves. */
  status: DataSourceStatus | null;
  /**
   * Whether a valid HR inference is currently being produced, or null if that
   * cannot yet be determined. Computed by the caller from the operational
   * view model — kept as an input so this function stays pure/testable.
   */
  inferenceReady: boolean | null;
}

const S14_SUBJECT_ID = "S14";

/**
 * Derive the ten independent preflight facts (§21). Order is stable so the UI
 * and the tests agree on indices.
 */
export function derivePresenterPreflight(input: PreflightInputs): PreflightFact[] {
  const facts: PreflightFact[] = [];

  // 1. Backend REST reachability.
  facts.push({
    id: "backend-rest",
    label: "Backend REST reachability",
    state: input.sourceStateStatus === "available" ? "ready" : input.sourceStateStatus === "error" ? "unavailable" : "unknown",
    detail:
      input.sourceStateStatus === "available"
        ? "/data-source/state responding"
        : input.sourceStateStatus === "error"
          ? "/data-source/state unreachable"
          : "checking…",
  });

  // 2. WebSocket state.
  facts.push({
    id: "websocket",
    label: "Live-feed WebSocket",
    state: input.connectionStatus === "open" ? "ready" : input.connectionStatus === "closed" ? "unavailable" : "unknown",
    detail: input.connectionStatus === "open" ? "connected" : input.connectionStatus === "closed" ? "disconnected" : "connecting…",
  });

  // 3. Final architecture definition availability — a bundled client constant,
  //    always present regardless of backend state.
  facts.push({
    id: "architecture",
    label: "Final architecture definition",
    state: "ready",
    detail: "CORE_PLUS_CONTEXT available",
  });

  // 4. Recorded replay dataset configuration.
  facts.push({
    id: "dataset",
    label: "Recorded replay dataset",
    state: input.datasetConfigured === true ? "ready" : input.datasetConfigured === false ? "not-ready" : "unknown",
    detail:
      input.datasetConfigured === true
        ? "configured"
        : input.datasetConfigured === false
          ? "not configured on backend"
          : "unknown",
  });

  // 5. Replay subject-list availability.
  facts.push({
    id: "subject-list",
    label: "Replay subject list",
    state:
      input.subjectListState === "available"
        ? "ready"
        : input.subjectListState === "empty"
          ? "not-ready"
          : input.subjectListState === "error"
            ? "unavailable"
            : "unknown",
    detail:
      input.subjectListState === "available"
        ? `${input.subjects.length} subject(s)`
        : input.subjectListState === "empty"
          ? "list returned empty"
          : input.subjectListState === "error"
            ? "subject list request failed"
            : "loading…",
  });

  // 6. S14 availability — derived from the returned subject list, never
  //    hard-coded, and always labelled as a single-participant robustness
  //    demonstration (§21, §4 truth lock).
  const s14Known = input.subjectListState === "available" || input.subjectListState === "empty";
  const s14Present = input.subjects.includes(S14_SUBJECT_ID);
  facts.push({
    id: "s14",
    label: "S14 (single-participant robustness demonstration)",
    state: !s14Known ? "unknown" : s14Present ? "ready" : "n/a",
    detail: !s14Known
      ? "pending subject list"
      : s14Present
        ? "available — single-participant stress test, not population validation"
        : "not present in current subject list",
  });

  // 7. HR model / checkpoint readiness — the current backend contract does not
  //    expose an authoritative readiness signal, so this is honestly Unknown
  //    rather than a fabricated green check (§21).
  facts.push({
    id: "hr-model",
    label: "HR model / checkpoint readiness",
    state: "unknown",
    detail: "Unknown — not exposed by current backend contract",
  });

  // 8. Active source.
  facts.push({
    id: "active-source",
    label: "Active source",
    state: input.status ? "ready" : "unknown",
    detail: input.status
      ? input.status.source_type === "dataset_replay"
        ? `recorded replay${input.status.subject_id ? ` — ${input.status.subject_id}` : ""}`
        : "synthetic"
      : "unknown",
  });

  // 9. Active fault state. An active injected fault is a deliberate demo state,
  //    but for a presenter about to begin it is "not ready" (clear it first).
  const faultActive = input.status?.fault_injection?.active ?? null;
  facts.push({
    id: "active-fault",
    label: "Active simulated fault",
    state: faultActive === null ? "unknown" : faultActive ? "not-ready" : "ready",
    detail:
      faultActive === null
        ? "unknown"
        : faultActive
          ? `fault active${input.status?.fault_injection?.target ? ` on ${input.status.fault_injection.target}` : ""}`
          : "none",
  });

  // 10. Current inference readiness.
  facts.push({
    id: "inference",
    label: "Current inference readiness",
    state: input.inferenceReady === true ? "ready" : input.inferenceReady === false ? "not-ready" : "unknown",
    detail:
      input.inferenceReady === true
        ? "valid HR inference"
        : input.inferenceReady === false
          ? "no valid HR inference yet"
          : "unknown",
  });

  return facts;
}

// ---------------------------------------------------------------------------
// §22 — One-click demo reset
// ---------------------------------------------------------------------------

/** Ordered replay/fault REST steps a reset may run. */
export type DemoResetStep = "pause" | "reset" | "speed-1x" | "clear-fault";

export interface DemoResetPlan {
  /** Ordered backend calls to run. Empty when the source is synthetic. */
  steps: DemoResetStep[];
  /** Always true — return the mission modality selection to PPG. */
  resetModalityToPpg: true;
  /** Always true — clear the session-only operational event history. */
  clearEventHistory: true;
  /** Always true — return /mission-overview to the top of the document. */
  scrollToTop: true;
  /**
   * Always true — the reset PRESERVES the current source and subject. It never
   * switches to synthetic and never invents / loads S14 (§22 truth locks).
   */
  preserveSourceAndSubject: true;
}

/**
 * Plan a demo reset from the current authoritative status (§22). Redundant
 * calls are avoided: `pause` only when actually playing, `speed-1x` only when
 * the speed is not already 1×, `clear-fault` only when a fault is active, and
 * no replay steps at all under a synthetic source.
 */
export function planDemoReset(status: DataSourceStatus | null): DemoResetPlan {
  const steps: DemoResetStep[] = [];
  const isReplay = status?.source_type === "dataset_replay";
  const hasSubject = Boolean(status?.subject_id);

  if (isReplay && hasSubject) {
    if (status?.playback_state === "playing") steps.push("pause");
    steps.push("reset");
    if (status?.playback_speed !== 1) steps.push("speed-1x");
  }
  if (status?.fault_injection?.active) steps.push("clear-fault");

  return {
    steps,
    resetModalityToPpg: true,
    clearEventHistory: true,
    scrollToTop: true,
    preserveSourceAndSubject: true,
  };
}

export interface DemoResetResult {
  ok: boolean;
  ranSteps: DemoResetStep[];
  failedSteps: DemoResetStep[];
}

/**
 * Summarise a completed reset run into an accessible announcement (§22 /
 * Prompt-4A HIGH-2 — "report partial failure honestly"). Success is claimed
 * ONLY when `ok === true` AND no steps failed, so an unexpected exception
 * (which produces `ok: false` with an empty `failedSteps`) can never be
 * announced as "complete".
 *
 * Three cases:
 *  1. ok, no failed steps            → full-success message.
 *  2. one or more named failed steps → partial-failure naming every step.
 *  3. not ok, no named failed steps  → explicit unexpected-failure message
 *                                       (never contains "complete").
 */
export function summariseDemoReset(result: DemoResetResult): string {
  if (result.ok && result.failedSteps.length === 0) {
    return "Demo state reset complete.";
  }
  if (result.failedSteps.length > 0) {
    return `Demo reset partially failed — ${result.failedSteps.join(", ")} did not complete. Other steps applied.`;
  }
  return "Demo reset failed unexpectedly. The current source and controls may be only partially reset.";
}
