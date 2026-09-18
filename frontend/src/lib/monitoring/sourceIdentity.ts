import type { DataSourceStatus, DataSourceType, LiveMetricsSnapshot } from "@/lib/types";

/**
 * Fail-closed confirmed-source boundary (Prompt-2 corrective pass §2).
 *
 * The WebSocket stream and the REST `/data-source/state` endpoint are two
 * independent channels. `missionStore.ingest()` deliberately keeps storing
 * every WS frame as `latest` (including one that arrives late, from a
 * source the user has since switched away from) — `LiveFeedProvider` needs
 * to keep observing raw frames so it can detect an externally-changed
 * source and re-poll REST to converge (requirement §2.6). What must NOT
 * happen is a *component* trusting a `latest` snapshot whose own source
 * identity disagrees with the authoritative REST status. These helpers are
 * the single place that comparison happens.
 */
export interface SourceIdentity {
  sourceType: DataSourceType;
  /** Only meaningful when sourceType is "dataset_replay"; null otherwise. */
  subjectId: string | null;
}

export function sourceIdentityFromStatus(status: DataSourceStatus | null | undefined): SourceIdentity | null {
  if (!status) return null;
  return {
    sourceType: status.source_type,
    subjectId: status.source_type === "dataset_replay" ? status.subject_id ?? null : null,
  };
}

export function sourceIdentityFromSnapshot(snapshot: LiveMetricsSnapshot | null | undefined): SourceIdentity | null {
  if (!snapshot) return null;
  return {
    sourceType: snapshot.source.source_type,
    subjectId: snapshot.source.source_type === "dataset_replay" ? snapshot.source.subject_id ?? null : null,
  };
}

function identitiesMatch(a: SourceIdentity, b: SourceIdentity): boolean {
  return a.sourceType === b.sourceType && a.subjectId === b.subjectId;
}

/**
 * Returns whether `snapshot`'s own source identity may be trusted for
 * rendering, given the authoritative `status`.
 *
 * - No authoritative status yet → nothing to contradict; the snapshot is
 *   provisionally trusted (this is what lets a fresh page load show data
 *   before the first `/data-source/state` response lands).
 * - Authoritative status exists but there is no snapshot at all → not
 *   confirmed (there is nothing to confirm).
 * - Authoritative status exists and the snapshot's identity matches →
 *   confirmed.
 * - Authoritative status exists and the snapshot's identity differs (wrong
 *   source type, or same replay source but a different subject) → not
 *   confirmed; the snapshot must not be used to populate HR, channels,
 *   fault, or sensor-health display.
 */
export function snapshotMatchesConfirmedSource(
  snapshot: LiveMetricsSnapshot | null | undefined,
  status: DataSourceStatus | null | undefined,
): boolean {
  const confirmed = sourceIdentityFromStatus(status);
  if (!confirmed) return true;
  const snapshotIdentity = sourceIdentityFromSnapshot(snapshot);
  if (!snapshotIdentity) return false;
  return identitiesMatch(confirmed, snapshotIdentity);
}
