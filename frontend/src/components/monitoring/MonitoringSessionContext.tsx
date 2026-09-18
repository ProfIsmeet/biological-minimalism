"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api } from "@/lib/api";
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

  // Applied on every successful DataSourceStatus response — the initial
  // load, its own retry, or any replay action (play/pause/load/fault/etc.).
  // "Do we have a working authoritative source state" is one fact,
  // independent of which request most recently proved it; this is what lets
  // the strip recover after backend restoration without requiring the user
  // to specifically hit the source-state retry (corrective §6).
  const applyDataSourceStatus = useCallback(
    (result: DataSourceStatus) => {
      setStatus(result);
      setDatasetConfigured(result.dataset_configured);
      setDataSourceStatus(result);
      setSourceStateStatus("available");
      setSourceStateError(null);
    },
    [setDataSourceStatus],
  );

  // Data-source/state fetch — independent from the subject-list fetch below
  // (Prompt-2 corrective §4/§6: a subject-list retry must not duplicate this
  // request, and this retry must not duplicate the subject-list request).
  useEffect(() => {
    let cancelled = false;
    setSourceStateStatus("loading");
    setSourceStateError(null);
    api
      .getDataSourceState()
      .then((result) => {
        if (cancelled) return;
        applyDataSourceStatus(result);
        setSelectedSubjectId((current) => current || result.subject_id || "");
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        setSourceStateStatus("error");
        setSourceStateError(errorMessage(reason));
      });
    return () => {
      cancelled = true;
    };
  }, [sourceStateReloadToken, applyDataSourceStatus]);

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
      try {
        const result = await operation();
        applyDataSourceStatus(result);
      } catch (reason) {
        setRequestError(errorMessage(reason));
      } finally {
        setPending(null);
      }
    },
    [applyDataSourceStatus],
  );

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
    }),
    [status, datasetConfigured, sourceStateStatus, sourceStateError, subjects, subjectListState, subjectListError, selectedSubjectId, pending, requestError, run],
  );

  return <MonitoringSessionCtx.Provider value={value}>{children}</MonitoringSessionCtx.Provider>;
}

export function useMonitoringSession(): MonitoringSessionValue {
  const context = useContext(MonitoringSessionCtx);
  if (!context) throw new Error("useMonitoringSession must be used within MonitoringSessionProvider");
  return context;
}
