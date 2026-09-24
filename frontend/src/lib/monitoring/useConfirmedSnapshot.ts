"use client";

import { useMissionStore } from "@/store/missionStore";
import { snapshotMatchesConfirmedSource } from "@/lib/monitoring/sourceIdentity";
import type { DataSourceStatus, LiveMetricsSnapshot } from "@/lib/types";

export interface ConfirmedSnapshotResult {
  /** `latest` when it matches the authoritative source; otherwise null. */
  snapshot: LiveMetricsSnapshot | null;
  /**
   * True when identity convergence is pending, or when a snapshot exists and
   * disagrees with authoritative status. Consumers use this to show an
   * explicit transient notice instead of silently falling back to their
   * ordinary "unavailable" state.
   */
  isWaitingForConfirmation: boolean;
}

/**
 * Pure form of the confirmed read boundary, shared by the React hook and the
 * deterministic real-store regression harness. Pending identity convergence
 * always wins over an otherwise matching old REST status.
 */
export function confirmedSnapshotForState(
  latest: LiveMetricsSnapshot | null,
  status: DataSourceStatus | null,
  sourceConvergenceKey: string | null,
): ConfirmedSnapshotResult {
  if (sourceConvergenceKey !== null) {
    return { snapshot: null, isWaitingForConfirmation: true };
  }
  const confirmed = snapshotMatchesConfirmedSource(latest, status);
  return {
    snapshot: confirmed ? latest : null,
    isWaitingForConfirmation: latest !== null && status !== null && !confirmed,
  };
}

/** Pure confirmed-history boundary used by the hook and behavioral tests. */
export function confirmedHistoryForState(
  history: LiveMetricsSnapshot[],
  status: DataSourceStatus | null,
  sourceConvergenceKey: string | null,
): LiveMetricsSnapshot[] {
  if (sourceConvergenceKey !== null) return [];
  if (!status) return history;
  return history.filter((snapshot) => snapshotMatchesConfirmedSource(snapshot, status));
}

/**
 * Single call site for the fail-closed confirmed-source read (Prompt-2
 * corrective §2). Every monitoring component that renders HR prediction,
 * channels, fault state, or sensor health should read `latest` through this
 * hook instead of `useMissionStore((s) => s.latest)` directly.
 */
export function useConfirmedSnapshot(): ConfirmedSnapshotResult {
  const latest = useMissionStore((state) => state.latest);
  const status = useMissionStore((state) => state.dataSourceStatus);
  const sourceConvergenceKey = useMissionStore((state) => state.sourceConvergenceKey);
  return confirmedSnapshotForState(latest, status, sourceConvergenceKey);
}

/**
 * Prompt-2B corrective §4.4 (additional discovered raw consumer) —
 * Defense-in-depth for current-session history. The store already rejects
 * cross-source frames, but this read boundary also returns no history while
 * convergence is pending and filters every entry against authoritative REST
 * status (see TrendPanel.tsx on /ai-insights and /mission-timeline).
 */
export function useConfirmedHistory(): LiveMetricsSnapshot[] {
  const history = useMissionStore((state) => state.history);
  const status = useMissionStore((state) => state.dataSourceStatus);
  const sourceConvergenceKey = useMissionStore((state) => state.sourceConvergenceKey);
  return confirmedHistoryForState(history, status, sourceConvergenceKey);
}
