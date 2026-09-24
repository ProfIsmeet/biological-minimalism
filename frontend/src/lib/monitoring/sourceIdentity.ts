import type { DataSourceStatus, DataSourceType, LiveMetricsSnapshot } from "@/lib/types";

/**
 * Fail-closed confirmed-source boundary (Prompt-2 corrective pass §2).
 *
 * The WebSocket stream and the REST `/data-source/state` endpoint are two
 * independent channels. `missionStore.ingest()` records an observed identity
 * key for REST convergence, but rejects a frame from `latest` and `history`
 * when its full identity disagrees with authoritative REST state. These
 * helpers are the single place that comparison happens.
 */
export interface SourceIdentity {
  sourceType: DataSourceType;
  /**
   * Dataset identity is tagged rather than flattened to a string so an
   * unreported dataset can never collide with a real dataset whose name
   * happens to resemble an "unknown" sentinel.
   */
  dataset: { kind: "reported"; name: string } | { kind: "unconfirmed" };
  /** Only meaningful when sourceType is "dataset_replay"; null otherwise. */
  subjectId: string | null;
}

function datasetIdentity(datasetName: string | null | undefined): SourceIdentity["dataset"] {
  return datasetName == null ? { kind: "unconfirmed" } : { kind: "reported", name: datasetName };
}

/** Stable, collision-safe key for current-session history segmentation. */
export function sourceIdentityKey(identity: SourceIdentity): string {
  return JSON.stringify([
    identity.sourceType,
    identity.dataset.kind,
    identity.dataset.kind === "reported" ? identity.dataset.name : null,
    identity.subjectId,
  ]);
}

export function sourceIdentityFromStatus(status: DataSourceStatus | null | undefined): SourceIdentity | null {
  if (!status) return null;
  return {
    sourceType: status.source_type,
    dataset: datasetIdentity(status.dataset_name),
    subjectId: status.source_type === "dataset_replay" ? status.subject_id ?? null : null,
  };
}

export function sourceIdentityFromSnapshot(snapshot: LiveMetricsSnapshot | null | undefined): SourceIdentity | null {
  if (!snapshot) return null;
  return {
    sourceType: snapshot.source.source_type,
    dataset: datasetIdentity(snapshot.source.dataset_name),
    subjectId: snapshot.source.source_type === "dataset_replay" ? snapshot.source.subject_id ?? null : null,
  };
}

function identitiesMatch(a: SourceIdentity, b: SourceIdentity): boolean {
  return sourceIdentityKey(a) === sourceIdentityKey(b);
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
 *   fault, sensor-health display, or current-session history. Dataset is
 *   part of this comparison, including the tagged unconfirmed state.
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
