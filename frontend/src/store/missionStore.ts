import { create } from "zustand";

import type { DataSourceStatus, LiveMetricsSnapshot } from "@/lib/types";

const MAX_HISTORY = 180;

function faultIdentity(fault: LiveMetricsSnapshot["fault_injection"] | DataSourceStatus["fault_injection"]): string {
  return fault?.active
    ? `${fault.fault_type}:${fault.target}:${fault.severity}:${fault.seed}`
    : "clean";
}

/**
 * Canonical source-identity key. Works for both a snapshot's `.source` and a
 * `DataSourceStatus`, which share `source_type`/`dataset_name`/`subject_id`.
 * Prompt 3B §19 — `dataset_name` is now part of the key so that switching to a
 * *different dataset* with the same source type and subject id is still
 * recognized as a session transition (and clears historical current-session
 * state), not just a same-dataset subject change.
 */
function sourceIdentityKey(src: { source_type: string; dataset_name: string | null; subject_id: string | null }): string {
  return `${src.source_type}:${src.dataset_name ?? ""}:${src.subject_id ?? ""}`;
}

export type ConnectionStatus = "connecting" | "open" | "closed";

interface MissionState {
  latest: LiveMetricsSnapshot | null;
  history: LiveMetricsSnapshot[];
  /**
   * Prompt 3A.1 §4 — timestamp of the most recent snapshot this client ever
   * confirmed, kept deliberately separate from `latest`. `latest` (and
   * `history`) are cleared the instant transport drops (see
   * `setConnectionStatus` below) so no stale waveform/value can survive a
   * disconnect; this field is the one explicit exception — "Last confirmed
   * frame: Xs ago" is legitimate historical context and must keep counting
   * up through a disconnect, so it is updated on every `ingest()` but never
   * touched by `setConnectionStatus`. It IS cleared on a genuine identity/
   * fault change in `setDataSourceStatus`, alongside `latest`/`history`,
   * since a new session has no "last confirmed frame" of its own yet.
   */
  lastConfirmedTimestampSeconds: number | null;
  dataSourceStatus: DataSourceStatus | null;
  connectionStatus: ConnectionStatus;
  ingest: (snapshot: LiveMetricsSnapshot) => void;
  setDataSourceStatus: (status: DataSourceStatus) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
}

export const useMissionStore = create<MissionState>((set) => ({
  latest: null,
  history: [],
  lastConfirmedTimestampSeconds: null,
  dataSourceStatus: null,
  connectionStatus: "connecting",
  ingest: (snapshot) =>
    set((state) => {
      const previousIdentity = state.latest
        ? `${state.latest.source.source_type}:${state.latest.source.subject_id ?? ""}`
        : null;
      const nextIdentity = `${snapshot.source.source_type}:${snapshot.source.subject_id ?? ""}`;
      return {
        latest: snapshot,
        history: previousIdentity === nextIdentity ? [...state.history, snapshot].slice(-MAX_HISTORY) : [snapshot],
        lastConfirmedTimestampSeconds: snapshot.timestamp,
      };
    }),
  setDataSourceStatus: (status) =>
    set((state) => {
      // Prompt 3A.2 §4 — previous *authoritative* identity, derived with
      // precedence: current snapshot's source → previous dataSourceStatus →
      // none. The snapshot alone is insufficient because
      // `setConnectionStatus("closed")` already nulls `latest`; a source/
      // subject/fault change made while disconnected would otherwise compare
      // against a null identity, fail to recognize the transition, and wrongly
      // preserve `lastConfirmedTimestampSeconds` from the *previous* session.
      // Falling back to the last known `dataSourceStatus` restores that
      // detection.
      const previousIdentity = state.latest
        ? sourceIdentityKey(state.latest.source)
        : state.dataSourceStatus
          ? sourceIdentityKey(state.dataSourceStatus)
          : null;
      const statusIdentity = sourceIdentityKey(status);
      const identityChanged = previousIdentity !== null && previousIdentity !== statusIdentity;

      const previousFaultIdentity = state.latest
        ? faultIdentity(state.latest.fault_injection)
        : state.dataSourceStatus
          ? faultIdentity(state.dataSourceStatus.fault_injection)
          : null;
      const faultChanged = previousFaultIdentity !== null && previousFaultIdentity !== faultIdentity(status.fault_injection);

      const reset = identityChanged || faultChanged;
      return {
        dataSourceStatus: status,
        latest: reset ? null : state.latest,
        history: reset ? [] : state.history,
        lastConfirmedTimestampSeconds: reset ? null : state.lastConfirmedTimestampSeconds,
      };
    }),
  // Prompt 3A.1 §4 root-cause fix — transport dropping (closed) or
  // reconnecting (connecting) must clear `latest`/`history` immediately, at
  // the single authoritative source of this data, rather than relying on
  // every downstream consumer to separately remember to gate on
  // `connectionStatus`. Before this fix `latest` was only ever cleared on an
  // identity/fault change, so a WS drop left the last-received snapshot
  // (waveforms, sample values, playback state) sitting in the store
  // indefinitely — exactly the stale-disconnected-plot defect this pass
  // exists to close. `lastConfirmedTimestampSeconds` is deliberately NOT
  // cleared here; see its own comment above.
  setConnectionStatus: (status) =>
    set(status === "open" ? { connectionStatus: status } : { connectionStatus: status, latest: null, history: [] }),
}));
