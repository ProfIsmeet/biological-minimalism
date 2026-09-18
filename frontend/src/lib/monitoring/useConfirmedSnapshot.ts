"use client";

import { useMissionStore } from "@/store/missionStore";
import { snapshotMatchesConfirmedSource } from "@/lib/monitoring/sourceIdentity";
import type { LiveMetricsSnapshot } from "@/lib/types";

export interface ConfirmedSnapshotResult {
  /** `latest` when it matches the authoritative source; otherwise null. */
  snapshot: LiveMetricsSnapshot | null;
  /**
   * True only when a snapshot exists AND authoritative status exists AND
   * they disagree — i.e. a real cross-source race, not merely "no data
   * yet". Consumers use this to show an explicit transient notice instead
   * of silently falling back to their ordinary "unavailable" state.
   */
  isWaitingForConfirmation: boolean;
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
  const confirmed = snapshotMatchesConfirmedSource(latest, status);
  return {
    snapshot: confirmed ? latest : null,
    isWaitingForConfirmation: latest !== null && status !== null && !confirmed,
  };
}

/**
 * Prompt-2B corrective §4.4 (additional discovered raw consumer) —
 * `missionStore.history` is built by the same unfiltered `ingest()` path as
 * `latest`, and while `setDataSourceStatus` already resets it on a
 * confirmed identity change, a single late cross-source frame can still
 * land in it during the same race window `useConfirmedSnapshot` closes for
 * `latest` (see TrendPanel.tsx, rendered on /ai-insights and
 * /mission-timeline). This filters the history array down to entries whose
 * own source identity matches the authoritative status, so a trend chart
 * can never plot a stray wrong-source data point as "current".
 */
export function useConfirmedHistory(): LiveMetricsSnapshot[] {
  const history = useMissionStore((state) => state.history);
  const status = useMissionStore((state) => state.dataSourceStatus);
  if (!status) return history;
  return history.filter((snapshot) => snapshotMatchesConfirmedSource(snapshot, status));
}
