"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { api } from "@/lib/api";
import {
  CANONICAL_JURY_SUBJECT_ID,
  checkCanonicalBootstrapPrerequisites,
  planDemoReset,
  runCanonicalJuryBootstrap,
  type CanonicalBootstrapResult,
  type DemoResetResult,
  type DemoResetStep,
} from "@/lib/monitoring/presenterOps";
import {
  classifySourceConvergenceStatus,
  sourceStateRequestCoordinator,
} from "@/lib/monitoring/sourceConvergence";
import type { DataSourceStatus, ReplayFaultTarget, ReplayFaultType } from "@/lib/types";
import { useMissionStore } from "@/store/missionStore";

/**
 * Single fetch boundary for `/live-monitoring`'s replay/fault session
 * (master prompt §7.3/§13 — "no request storm caused by multiple mounted
 * ... sections"). `MonitoringSourceStrip`, `ReplaySessionControl`, and
 * `SimulatedFaultControl` all need the same dataset-configured / subject /
 * pending-action state; without this context each would independently call
 * `api.getDataSourceState()` and `api.getReplaySubjects()` on mount, exactly
 * the duplicate-request pattern this stage exists to eliminate.
 */

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Data-source request failed.";
}

/**
 * Prompt-2 corrective pass §4: a request failure and a canonically-empty
 * successful response are different states and must never collapse into
 * the same UI text. `"empty"` is reserved for a genuine 200 response whose
 * `subjects` array is empty; `"error"` is reserved for the request itself
 * failing (network/5xx/etc.).
 */
export type SubjectListState = "loading" | "available" | "empty" | "error";

/**
 * Prompt-2B corrective §6 — distinct from `SubjectListState` and from the
 * per-action `pending`/`requestError` pair below. This is specifically "do
 * we have a working `/data-source/state`", independent of which request
 * last proved it (the initial load, its own retry, or any successful
 * replay action).
 */
export type SourceStateStatus = "loading" | "available" | "error";

interface MonitoringSessionValue {
  status: DataSourceStatus | null;
  /** null until `/data-source/state` resolves at least once. */
  datasetConfigured: boolean | null;
  sourceStateStatus: SourceStateStatus;
  sourceStateError: string | null;
  retrySourceState: () => void;
  subjects: string[];
  subjectListState: SubjectListState;
  subjectListError: string | null;
  retrySubjectList: () => void;
  selectedSubjectId: string;
  setSelectedSubjectId: (id: string) => void;
  pending: string | null;
  requestError: string | null;
  switchToSynthetic: () => Promise<void>;
  loadSubject: (subjectId: string) => Promise<void>;
  play: () => Promise<void>;
  pause: () => Promise<void>;
  reset: () => Promise<void>;
  setSpeed: (speed: 1 | 5 | 10) => Promise<void>;
  configureFault: (config: { fault_type: ReplayFaultType; target: ReplayFaultTarget; severity: number; seed: number }) => Promise<void>;
  clearFault: () => Promise<void>;
  /**
   * Prompt-4 §22 — run the one-click demo reset's backend steps (pause / reset
   * to start / speed 1× / clear fault, as applicable to the current source),
   * returning a structured result so the caller can report partial failure
   * honestly. Preserves the current source and subject; never switches to
   * synthetic and never loads a subject.
   */
  resetDemoState: () => Promise<DemoResetResult>;
  /**
   * Stage 3B — the explicit "Load Canonical Jury Demo" bootstrap: switches to
   * recorded PPG-DaLiA replay, subject S14 specifically, paused at the start,
   * 1×, no active fault. Fails closed with the exact missing prerequisite
   * (dataset not configured / subject list unavailable / S14 absent) BEFORE
   * issuing any request — never silently falls back to synthetic. Idempotent
   * and race-safe: reuses the same authoritative-mutation ticket lifecycle as
   * `resetDemoState`, so a superseding call (a second invocation, a route
   * change, an owner transfer, or unmount) makes an in-flight sequence stop
   * issuing further requests and never overwrites newer state.
   */
  loadCanonicalJuryDemo: () => Promise<CanonicalBootstrapResult>;
}

const MonitoringSessionCtx = createContext<MonitoringSessionValue | null>(null);

export function MonitoringSessionProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<DataSourceStatus | null>(null);
  const [datasetConfigured, setDatasetConfigured] = useState<boolean | null>(null);
  const [sourceStateStatus, setSourceStateStatus] = useState<SourceStateStatus>("loading");
  const [sourceStateError, setSourceStateError] = useState<string | null>(null);
  const [subjects, setSubjects] = useState<string[]>([]);
  const [subjectListState, setSubjectListState] = useState<SubjectListState>("loading");
  const [subjectListError, setSubjectListError] = useState<string | null>(null);
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [sourceStateReloadToken, setSourceStateReloadToken] = useState(0);
  const [subjectsReloadToken, setSubjectsReloadToken] = useState(0);
  const setDataSourceStatus = useMissionStore((state) => state.setDataSourceStatus);
  const sourceConvergenceKey = useMissionStore((state) => state.sourceConvergenceKey);
  const requestOwnerRef = useRef(Symbol("full-monitoring-source-state-owner"));
  const handledSourceStateReloadTokenRef = useRef(0);

  // The full-route provider owns one source-state request epoch. The shared
  // coordinator transfers that epoch safely to/from the legacy route owner
  // and preserves a same-token in-flight request through Strict Mode replay.
  useEffect(() => {
    const owner = requestOwnerRef.current;
    sourceStateRequestCoordinator.activateOwner(owner);
    return () => {
      sourceStateRequestCoordinator.releaseOwner(owner);
    };
  }, []);

  // Applied on every successful DataSourceStatus response — the initial
  // load, its own retry, or any replay action (play/pause/load/fault/etc.).
  // "Do we have a working authoritative source state" is one fact,
  // independent of which request most recently proved it; this is what lets
  // the strip recover after backend restoration without requiring the user
  // to specifically hit the source-state retry (corrective §6).
  const applyDataSourceStatus = useCallback(
    (result: DataSourceStatus) => {
      const missionState = useMissionStore.getState();
      const convergenceDisposition = classifySourceConvergenceStatus(
        result,
        missionState.sourceConvergenceKey,
        missionState.sourceConvergenceBaseKey,
      );
      setStatus(result);
      setDatasetConfigured(result.dataset_configured);
      setDataSourceStatus(result);
      if (convergenceDisposition === "unchanged_pre_convergence_authority") {
        setSourceStateStatus("error");
        setSourceStateError("Observed telemetry identity is not yet confirmed by authoritative source state.");
        return false;
      }
      setSourceStateStatus("available");
      setSourceStateError(null);
      return true;
    },
    [setDataSourceStatus],
  );

  // Initial seed, explicit source-state retry, and identity convergence share
  // one lifecycle. Mounting with pending B plans only B (not seed + B), while
  // request generations reject stale promise completions.
  useEffect(() => {
    const owner = requestOwnerRef.current;
    sourceStateRequestCoordinator.activateOwner(owner);
    const forceRetry = sourceStateReloadToken !== handledSourceStateReloadTokenRef.current;
    handledSourceStateReloadTokenRef.current = sourceStateReloadToken;
    const registration = sourceStateRequestCoordinator.startOrAdoptRequest(
      owner,
      sourceConvergenceKey,
      api.getDataSourceState,
      (result) => {
        applyDataSourceStatus(result);
        setSelectedSubjectId((current) => current || result.subject_id || "");
      },
      (reason) => {
        setSourceStateStatus("error");
        setSourceStateError(errorMessage(reason));
      },
      { force: forceRetry },
    );
    if (!registration) return;

    setSourceStateStatus("loading");
    setSourceStateError(null);
  }, [sourceConvergenceKey, sourceStateReloadToken, applyDataSourceStatus]);

  // Subject-list fetch. A request failure (network/5xx) and a genuine 200
  // response with an empty array are kept as distinct states — see
  // SubjectListState above.
  useEffect(() => {
    let cancelled = false;
    setSubjectListState("loading");
    setSubjectListError(null);
    api
      .getReplaySubjects()
      .then((result) => {
        if (cancelled) return;
        setSubjects(result.subjects);
        setSubjectListState(result.subjects.length ? "available" : "empty");
        setSelectedSubjectId((current) => current || result.subjects[0] || "");
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        setSubjects([]);
        setSubjectListState("error");
        setSubjectListError(errorMessage(reason));
      });
    return () => {
      cancelled = true;
    };
  }, [subjectsReloadToken]);

  const run = useCallback(
    async (key: string, operation: () => Promise<DataSourceStatus>) => {
      setPending(key);
      setRequestError(null);
      const registration = sourceStateRequestCoordinator.startAuthoritativeMutation(
        requestOwnerRef.current,
        operation,
        (result) => {
          applyDataSourceStatus(result);
          setPending(null);
        },
        (reason) => {
          setRequestError(errorMessage(reason));
          setPending(null);
        },
      );
      if (!registration) {
        setPending(null);
        return;
      }
      await registration.outcome;
    },
    [applyDataSourceStatus],
  );

  // §22 — the compound demo reset. Runs only the backend steps that apply to
  // the current status (see planDemoReset), collecting per-step failures so a
  // partial failure is never reported as full success. The non-backend parts
  // of the reset (clearing the session event log, returning the mission
  // modality to PPG, scrolling to the top) are owned by the drawer, which
  // sequences them after this resolves.
  const resetDemoState = useCallback(async (): Promise<DemoResetResult> => {
    setPending("reset-demo");
    setRequestError(null);
    const plan = planDemoReset(status);
    if (!plan.steps.length) {
      setPending(null);
      return { ok: true, ranSteps: [], failedSteps: [] };
    }
    const mutationTicket = sourceStateRequestCoordinator.beginAuthoritativeMutation(requestOwnerRef.current);
    if (!mutationTicket) {
      setPending(null);
      return { ok: false, ranSteps: [], failedSteps: [] };
    }
    const runners: Record<DemoResetStep, () => Promise<DataSourceStatus>> = {
      pause: api.pauseReplay,
      reset: api.resetReplay,
      "speed-1x": () => api.setReplaySpeed(1),
      "clear-fault": api.clearReplayFault,
    };
    const ranSteps: DemoResetStep[] = [];
    const failedSteps: DemoResetStep[] = [];
    let lastStatus: DataSourceStatus | null = null;
    // Prompt-4A HIGH-2 — `pending` is cleared in `finally` so an unexpected
    // throw (e.g. applyDataSourceStatus) can never leave the controls stuck in
    // a pending/disabled state.
    try {
      for (const step of plan.steps) {
        if (!sourceStateRequestCoordinator.isAuthoritativeMutationCurrent(mutationTicket)) break;
        try {
          lastStatus = await runners[step]();
          ranSteps.push(step);
        } catch {
          failedSteps.push(step);
        }
      }
      if (lastStatus) {
        sourceStateRequestCoordinator.acceptAuthoritativeMutation(
          mutationTicket,
          lastStatus,
          applyDataSourceStatus,
        );
      }
    } finally {
      if (sourceStateRequestCoordinator.isAuthoritativeMutationCurrent(mutationTicket)) {
        setPending(null);
      }
    }
    const ok = failedSteps.length === 0;
    if (!ok && sourceStateRequestCoordinator.isAuthoritativeMutationCurrent(mutationTicket)) {
      setRequestError(`Reset incomplete — ${failedSteps.join(", ")} failed. Other steps applied.`);
    }
    return { ok, ranSteps, failedSteps };
  }, [status, applyDataSourceStatus]);

  // Stage 3B — canonical jury demo bootstrap. The prerequisite gate runs
  // BEFORE any mutation ticket is taken, so a missing prerequisite never
  // touches the coordinator's generation counter at all (a genuinely
  // no-op failure, safe to call repeatedly). Once prerequisites pass, the
  // four-step sequence itself is delegated to the pure, independently
  // tested `runCanonicalJuryBootstrap` — this function's only job is
  // wiring that sequencer to the real `api` calls and the coordinator's
  // authoritative-mutation ticket, exactly mirroring `resetDemoState`
  // above.
  const loadCanonicalJuryDemo = useCallback(async (): Promise<CanonicalBootstrapResult> => {
    const prerequisite = checkCanonicalBootstrapPrerequisites({ datasetConfigured, subjectListState, subjects });
    if (!prerequisite.ok) {
      return { outcome: "prerequisite-block", ok: false, blockedOnPrerequisite: prerequisite.failure, blockedDetail: prerequisite.detail, ranSteps: [], failedSteps: [] };
    }
    setPending("canonical-bootstrap");
    setRequestError(null);
    const mutationTicket = sourceStateRequestCoordinator.beginAuthoritativeMutation(requestOwnerRef.current);
    if (!mutationTicket) {
      setPending(null);
      return { outcome: "superseded", ok: false, blockedOnPrerequisite: null, blockedDetail: null, ranSteps: [], failedSteps: [] };
    }
    let sequenceResult: Awaited<ReturnType<typeof runCanonicalJuryBootstrap>>;
    try {
      sequenceResult = await runCanonicalJuryBootstrap(
        {
          loadSubject: () => api.loadReplaySubject(CANONICAL_JURY_SUBJECT_ID),
          reset: api.resetReplay,
          setSpeed1x: () => api.setReplaySpeed(1),
          clearFault: api.clearReplayFault,
        },
        () => sourceStateRequestCoordinator.isAuthoritativeMutationCurrent(mutationTicket),
      );
      if (sequenceResult.lastStatus) {
        sourceStateRequestCoordinator.acceptAuthoritativeMutation(mutationTicket, sequenceResult.lastStatus, applyDataSourceStatus);
      }
    } finally {
      if (sourceStateRequestCoordinator.isAuthoritativeMutationCurrent(mutationTicket)) {
        setPending(null);
      }
    }
    const { outcome, ok, ranSteps, failedSteps } = sequenceResult;
    // Guarded by the same ticket-currency check used throughout: a
    // superseded sequence's ticket is, by construction, never current again
    // once superseded (generation only increases), so this can never fire
    // for a stale/superseded attempt and can never clear or overwrite a
    // newer owner's pending/error state.
    if (outcome === "step-failure" && sourceStateRequestCoordinator.isAuthoritativeMutationCurrent(mutationTicket)) {
      setRequestError(`Canonical jury demo load incomplete — ${failedSteps.join(", ")} did not complete.`);
    }
    return { outcome, ok, blockedOnPrerequisite: null, blockedDetail: null, ranSteps, failedSteps };
  }, [datasetConfigured, subjectListState, subjects, applyDataSourceStatus]);

  const value = useMemo<MonitoringSessionValue>(
    () => ({
      status,
      datasetConfigured,
      sourceStateStatus,
      sourceStateError,
      retrySourceState: () => setSourceStateReloadToken((token) => token + 1),
      subjects,
      subjectListState,
      subjectListError,
      retrySubjectList: () => setSubjectsReloadToken((token) => token + 1),
      selectedSubjectId,
      setSelectedSubjectId,
      pending,
      requestError,
      switchToSynthetic: () => run("synthetic", api.useSyntheticSource),
      loadSubject: (subjectId: string) => run("load", () => api.loadReplaySubject(subjectId)),
      play: () => run("play", api.playReplay),
      pause: () => run("pause", api.pauseReplay),
      reset: () => run("reset", api.resetReplay),
      setSpeed: (speed: 1 | 5 | 10) => run(`speed-${speed}`, () => api.setReplaySpeed(speed)),
      configureFault: (config) => run("fault-enable", () => api.configureReplayFault(config)),
      clearFault: () => run("fault-disable", api.clearReplayFault),
      resetDemoState,
      loadCanonicalJuryDemo,
    }),
    [
      status,
      datasetConfigured,
      sourceStateStatus,
      sourceStateError,
      subjects,
      subjectListState,
      subjectListError,
      selectedSubjectId,
      pending,
      requestError,
      run,
      resetDemoState,
      loadCanonicalJuryDemo,
    ],
  );

  return <MonitoringSessionCtx.Provider value={value}>{children}</MonitoringSessionCtx.Provider>;
}

export function useMonitoringSession(): MonitoringSessionValue {
  const context = useContext(MonitoringSessionCtx);
  if (!context) throw new Error("useMonitoringSession must be used within MonitoringSessionProvider");
  return context;
}
