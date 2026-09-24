import { create } from "zustand";

import {
  snapshotMatchesConfirmedSource,
  sourceIdentityFromSnapshot,
  sourceIdentityFromStatus,
  sourceIdentityKey,
} from "@/lib/monitoring/sourceIdentity";
import { classifySourceConvergenceStatus } from "@/lib/monitoring/sourceConvergence";
import type { DataSourceStatus, LiveMetricsSnapshot } from "@/lib/types";

const MAX_HISTORY = 180;

function faultIdentity(fault: LiveMetricsSnapshot["fault_injection"] | DataSourceStatus["fault_injection"]): string {
  return fault?.active
    ? `${fault.fault_type}:${fault.target}:${fault.severity}:${fault.seed}`
    : "clean";
}

export type ConnectionStatus = "connecting" | "open" | "closed";

interface MissionState {
  latest: LiveMetricsSnapshot | null;
  history: LiveMetricsSnapshot[];
  /** Raw observed identity only; never a source of displayed telemetry. */
  observedSourceIdentityKey: string | null;
  /** Mismatched observed identity awaiting one authoritative REST convergence request. */
  sourceConvergenceKey: string | null;
  /** Authoritative identity in force when the current convergence transition began. */
  sourceConvergenceBaseKey: string | null;
  /** Pending identities superseded during the current unresolved transition. */
  sourceConvergenceSupersededKeys: string[];
  /** Recently retired authoritative/speculative identities; late frames cannot reopen them. */
  retiredSourceIdentityKeys: string[];
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
  observedSourceIdentityKey: null,
  sourceConvergenceKey: null,
  sourceConvergenceBaseKey: null,
  sourceConvergenceSupersededKeys: [],
  retiredSourceIdentityKeys: [],
  lastConfirmedTimestampSeconds: null,
  dataSourceStatus: null,
  connectionStatus: "connecting",
  ingest: (snapshot) =>
    set((state) => {
      const nextIdentity = sourceIdentityFromSnapshot(snapshot);
      const nextIdentityKey = nextIdentity ? sourceIdentityKey(nextIdentity) : null;
      // Pending convergence is a global fail-closed boundary, not merely a
      // trigger for a route-owned REST request. Until authoritative REST
      // confirms the pending identity, no frame may repopulate current data.
      //
      // In particular, a frame matching the *old* REST identity must not
      // replace the observed pending target or re-enter latest/history. A
      // genuinely different non-authoritative identity may replace the
      // target so the shared convergence owners can request it once.
      if (state.sourceConvergenceKey !== null) {
        const matchesOldAuthoritativeStatus = state.dataSourceStatus
          ? snapshotMatchesConfirmedSource(snapshot, state.dataSourceStatus)
          : false;
        const replacesPendingTarget =
          !matchesOldAuthoritativeStatus
          && nextIdentityKey !== null
          && nextIdentityKey !== state.sourceConvergenceKey
          && !state.sourceConvergenceSupersededKeys.includes(nextIdentityKey);

        return {
          latest: null,
          history: [],
          observedSourceIdentityKey: replacesPendingTarget
            ? nextIdentityKey
            : state.observedSourceIdentityKey,
          sourceConvergenceKey: replacesPendingTarget
            ? nextIdentityKey
            : state.sourceConvergenceKey,
          sourceConvergenceBaseKey: state.sourceConvergenceBaseKey,
          sourceConvergenceSupersededKeys: replacesPendingTarget
            ? [...new Set([...state.sourceConvergenceSupersededKeys, state.sourceConvergenceKey])]
            : state.sourceConvergenceSupersededKeys,
        };
      }
      // REST source state is authoritative once available. A late frame from
      // the previous dataset/source/subject is rejected before it can replace
      // `latest`, advance the timestamp, or enter active session history. The
      // previously-current frame/history are also invalidated immediately:
      // REST has not converged yet, so neither A nor B may remain current.
      if (state.dataSourceStatus && !snapshotMatchesConfirmedSource(snapshot, state.dataSourceStatus)) {
        const authoritativeIdentity = sourceIdentityFromStatus(state.dataSourceStatus);
        // If REST has already moved to a new identity, a frame carrying the
        // last observed identity is a known late frame from the retired
        // session or an identity retired by an earlier authoritative
        // transition. Reject it without disturbing current telemetry or
        // reopening convergence back to that stale identity. REST can still
        // authoritatively select that identity again in a later transition.
        if (
          nextIdentityKey !== null
          && (nextIdentityKey === state.observedSourceIdentityKey || state.retiredSourceIdentityKeys.includes(nextIdentityKey))
        ) {
          return {};
        }
        return {
          latest: null,
          history: [],
          observedSourceIdentityKey: nextIdentityKey,
          sourceConvergenceKey: nextIdentityKey,
          sourceConvergenceBaseKey: authoritativeIdentity ? sourceIdentityKey(authoritativeIdentity) : null,
          sourceConvergenceSupersededKeys: [],
        };
      }

      const previousIdentity = state.latest ? sourceIdentityFromSnapshot(state.latest) : null;
      const sameSession =
        previousIdentity !== null
        && nextIdentity !== null
        && sourceIdentityKey(previousIdentity) === sourceIdentityKey(nextIdentity);
      return {
        latest: snapshot,
        history: sameSession ? [...state.history, snapshot].slice(-MAX_HISTORY) : [snapshot],
        observedSourceIdentityKey: nextIdentityKey,
        sourceConvergenceKey: state.sourceConvergenceKey,
        sourceConvergenceBaseKey: state.sourceConvergenceBaseKey,
        sourceConvergenceSupersededKeys: state.sourceConvergenceSupersededKeys,
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
        ? sourceIdentityFromSnapshot(state.latest)
        : state.dataSourceStatus
          ? sourceIdentityFromStatus(state.dataSourceStatus)
          : null;
      const statusIdentity = sourceIdentityFromStatus(status);
      const identityChanged =
        previousIdentity !== null
        && statusIdentity !== null
        && sourceIdentityKey(previousIdentity) !== sourceIdentityKey(statusIdentity);
      const previousIdentityKey = previousIdentity ? sourceIdentityKey(previousIdentity) : null;

      const previousFaultIdentity = state.latest
        ? faultIdentity(state.latest.fault_injection)
        : state.dataSourceStatus
          ? faultIdentity(state.dataSourceStatus.fault_injection)
          : null;
      const faultChanged = previousFaultIdentity !== null && previousFaultIdentity !== faultIdentity(status.fault_injection);

      const reset = identityChanged || faultChanged;
      const convergenceDisposition = classifySourceConvergenceStatus(
        status,
        state.sourceConvergenceKey,
        state.sourceConvergenceBaseKey,
      );
      const convergenceResolved =
        convergenceDisposition === "confirmed_pending_identity"
        || convergenceDisposition === "advanced_to_third_authority";
      const statusIdentityKey = statusIdentity ? sourceIdentityKey(statusIdentity) : null;
      const newlyRetiredKeys = [
        ...(identityChanged && previousIdentityKey ? [previousIdentityKey] : []),
        ...(convergenceResolved && state.sourceConvergenceKey ? [state.sourceConvergenceKey] : []),
        ...(convergenceResolved ? state.sourceConvergenceSupersededKeys : []),
      ];
      const retiredSourceIdentityKeys = [...new Set([...state.retiredSourceIdentityKeys, ...newlyRetiredKeys])]
        .filter((key) => key !== statusIdentityKey);
      return {
        dataSourceStatus: status,
        latest: reset ? null : state.latest,
        history: reset ? [] : state.history,
        sourceConvergenceKey: convergenceResolved ? null : state.sourceConvergenceKey,
        sourceConvergenceBaseKey:
          convergenceResolved || state.sourceConvergenceKey === null
            ? null
            : state.sourceConvergenceBaseKey,
        sourceConvergenceSupersededKeys: convergenceResolved ? [] : state.sourceConvergenceSupersededKeys,
        retiredSourceIdentityKeys,
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
