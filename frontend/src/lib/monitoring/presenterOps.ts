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

// ---------------------------------------------------------------------------
// Stage 3B — canonical jury demo bootstrap
// ---------------------------------------------------------------------------

/**
 * The single canonical jury-demo subject (master prompt Milestone C):
 * recorded PPG-DaLiA replay, this specific participant, at the start,
 * 1×, no active fault. This is real recorded human research data — never
 * astronaut data, never presented as such (see MissionStatusBar's
 * "Recorded human-data replay · Not live astronaut monitoring" copy, which
 * this bootstrap's resulting state renders through unchanged).
 */
export const CANONICAL_JURY_SUBJECT_ID = "S14";

export type CanonicalBootstrapPrerequisiteFailure = "dataset_not_configured" | "subject_list_unavailable" | "s14_not_present";

export interface CanonicalBootstrapPrerequisiteInput {
  datasetConfigured: boolean | null;
  subjectListState: SubjectListState;
  subjects: string[];
}

export interface CanonicalBootstrapPrerequisiteResult {
  ok: boolean;
  failure: CanonicalBootstrapPrerequisiteFailure | null;
  detail: string;
}

/**
 * Fail-closed prerequisite gate, checked BEFORE any mutating request is
 * issued. Never infers readiness from the absence of an error — an
 * unresolved ("loading") subject list is treated the same as an explicit
 * failure, since neither proves S14 is actually available. HR-checkpoint
 * readiness is deliberately not checked here: the current backend contract
 * does not expose it (see `derivePresenterPreflight`'s honest "unknown" for
 * the same fact) — this function never fabricates a check it cannot
 * actually perform. A missing checkpoint would surface honestly as a
 * failed `load-subject` step if it ever causes that request to fail.
 */
export function checkCanonicalBootstrapPrerequisites(input: CanonicalBootstrapPrerequisiteInput): CanonicalBootstrapPrerequisiteResult {
  if (input.datasetConfigured !== true) {
    return {
      ok: false,
      failure: "dataset_not_configured",
      detail: "Recorded PPG-DaLiA replay dataset is not configured on this backend.",
    };
  }
  if (input.subjectListState !== "available") {
    return {
      ok: false,
      failure: "subject_list_unavailable",
      detail:
        input.subjectListState === "error"
          ? "The replay subject list could not be loaded."
          : input.subjectListState === "empty"
            ? "The replay subject list is empty."
            : "The replay subject list has not finished loading.",
    };
  }
  if (!input.subjects.includes(CANONICAL_JURY_SUBJECT_ID)) {
    return {
      ok: false,
      failure: "s14_not_present",
      detail: `Subject ${CANONICAL_JURY_SUBJECT_ID} is not present in the current replay subject list.`,
    };
  }
  return { ok: true, failure: null, detail: "Prerequisites satisfied." };
}

/** Ordered REST steps the bootstrap runs once prerequisites pass. */
export type CanonicalBootstrapStep = "load-subject" | "reset" | "speed-1x" | "clear-fault";

export const CANONICAL_BOOTSTRAP_STEPS: readonly CanonicalBootstrapStep[] = ["load-subject", "reset", "speed-1x", "clear-fault"];

export interface CanonicalBootstrapRunners {
  loadSubject: () => Promise<DataSourceStatus>;
  reset: () => Promise<DataSourceStatus>;
  setSpeed1x: () => Promise<DataSourceStatus>;
  clearFault: () => Promise<DataSourceStatus>;
}

/**
 * Explicit discriminant for how a bootstrap attempt ended. `"success"` is the
 * ONLY outcome that means "the canonical demo is now loaded" — every other
 * value must never be summarised as loaded/complete. Modelling this as its
 * own field (rather than inferring success from `failedSteps.length === 0`)
 * is what closes the corrective-review defect: a sequence that was
 * superseded mid-run has an EMPTY `failedSteps` (nothing failed — it was
 * simply stopped), so `failedSteps.length === 0` alone is not sufficient
 * evidence of success.
 */
export type CanonicalBootstrapOutcome = "success" | "step-failure" | "superseded";

export interface CanonicalBootstrapRunResult {
  outcome: CanonicalBootstrapOutcome;
  /** True only when outcome === "success". Kept alongside `outcome` for convenient boolean checks. */
  ok: boolean;
  ranSteps: CanonicalBootstrapStep[];
  failedSteps: CanonicalBootstrapStep[];
  /**
   * The last successful step's returned status — but ONLY when it is safe to
   * apply. Deliberately forced to `null` whenever `outcome === "superseded"`,
   * even though an individual step's REST call may have returned a real
   * status internally: a superseded sequence must never let its result be
   * applied by the caller, and making the field itself `null` makes that
   * true even if a caller forgot to check `outcome` first.
   */
  lastStatus: DataSourceStatus | null;
}

/**
 * Pure, framework-free sequencing of the four canonical-bootstrap REST steps
 * (load S14 → reset to start → speed 1× → clear fault). Framework-free
 * deliberately: this is the actual race-safety-critical logic (the part a
 * behavioral test can and must exercise directly, per the master prompt's
 * "structural guards may supplement but must not be the sole evidence where
 * runtime behavior can be tested"), so it takes its REST calls and its
 * "am I still the current authoritative mutation" check as injected
 * dependencies rather than reaching into React state or the request
 * coordinator itself.
 *
 * `isCurrent()` is checked before every step (not only once at the start)
 * AND once more after the loop exits — the latter catches the narrow window
 * where the final step's request resolves successfully but the sequence is
 * superseded before this function hands control back to the caller for
 * acceptance. Either check failing sets `outcome: "superseded"`
 * unconditionally: superseded always means "not ok", regardless of how many
 * steps happened to complete or whether any of them failed.
 *
 * Success (`outcome: "success"`) requires ALL of: not superseded, every one
 * of the four canonical steps present in `ranSteps` (not just "no failures"
 * — a superseded run can just as easily have zero failures with only two
 * steps completed), and zero failed steps. This is the explicit invariant
 * the corrective review required, checked directly rather than inferred.
 *
 * If `load-subject` itself fails, the remaining steps are skipped (they
 * would fail anyway with no active replay to reset/speed/clear-fault on,
 * and running them would only produce confusing extra failure entries for
 * a single root cause) — this is a `"step-failure"` outcome, not
 * `"superseded"`.
 */
export async function runCanonicalJuryBootstrap(
  runners: CanonicalBootstrapRunners,
  isCurrent: () => boolean,
): Promise<CanonicalBootstrapRunResult> {
  const stepRunner: Record<CanonicalBootstrapStep, () => Promise<DataSourceStatus>> = {
    "load-subject": runners.loadSubject,
    reset: runners.reset,
    "speed-1x": runners.setSpeed1x,
    "clear-fault": runners.clearFault,
  };
  const ranSteps: CanonicalBootstrapStep[] = [];
  const failedSteps: CanonicalBootstrapStep[] = [];
  let lastStatus: DataSourceStatus | null = null;
  let superseded = false;

  for (const step of CANONICAL_BOOTSTRAP_STEPS) {
    if (!isCurrent()) {
      superseded = true;
      break;
    }
    try {
      lastStatus = await stepRunner[step]();
      ranSteps.push(step);
    } catch {
      failedSteps.push(step);
      if (step === "load-subject") break;
    }
  }

  // Catches supersession landing in the gap between the final step's request
  // resolving and this function returning — the loop's own per-step guard
  // cannot see this, since there is no further iteration to check it on.
  if (!superseded && !isCurrent()) {
    superseded = true;
  }

  if (superseded) {
    return { outcome: "superseded", ok: false, ranSteps, failedSteps, lastStatus: null };
  }

  const completedAllSteps = CANONICAL_BOOTSTRAP_STEPS.every((step) => ranSteps.includes(step));
  const success = completedAllSteps && failedSteps.length === 0;
  return {
    outcome: success ? "success" : "step-failure",
    ok: success,
    ranSteps,
    failedSteps,
    lastStatus,
  };
}

export type CanonicalBootstrapResultOutcome = CanonicalBootstrapOutcome | "prerequisite-block" | "unexpected-failure";

export interface CanonicalBootstrapResult {
  outcome: CanonicalBootstrapResultOutcome;
  /** True only when outcome === "success". */
  ok: boolean;
  blockedOnPrerequisite: CanonicalBootstrapPrerequisiteFailure | null;
  /** The exact prerequisite-check detail string, present iff blockedOnPrerequisite is set. */
  blockedDetail: string | null;
  ranSteps: CanonicalBootstrapStep[];
  failedSteps: CanonicalBootstrapStep[];
}

/**
 * Accessible, honest summary (mirrors `summariseDemoReset`'s three-case
 * shape, extended with the two additional outcomes this type now
 * distinguishes). Dispatches on the explicit `outcome` discriminant rather
 * than inferring success from `ok`/`failedSteps` shape — this is what
 * prevents a superseded result (empty `failedSteps`, since nothing actually
 * failed) from ever being summarised as loaded.
 */
export function summariseCanonicalBootstrap(result: CanonicalBootstrapResult): string {
  switch (result.outcome) {
    case "prerequisite-block":
      return `Canonical jury demo not loaded — ${result.blockedDetail ?? "a prerequisite is not satisfied"}`;
    case "success":
      return `Canonical jury demo loaded — recorded replay, subject ${CANONICAL_JURY_SUBJECT_ID}, paused at start, 1×, no active fault.`;
    case "step-failure":
      return `Canonical jury demo load partially failed — ${result.failedSteps.join(", ")} did not complete.`;
    case "superseded":
      return "Canonical jury demo load was superseded by a newer control action. No state was applied by this attempt.";
    case "unexpected-failure":
    default:
      return "Canonical jury demo load failed unexpectedly. Source state may be only partially updated.";
  }
}
