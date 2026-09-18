"use client";

import { useMissionStore } from "@/store/missionStore";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { DASHBOARD_VS_RESULTS_STATEMENT } from "@/lib/architecture";
import { deriveSourceLabel } from "@/lib/sourceLabel";

// Master-prompt §7.1 — source and scope strip. Values come from the real
// connection/source state (missionStore) via the shared deriveSourceLabel
// helper, never invented. This codebase has no genuine "live hardware"
// source (only synthetic mock data and recorded PPG-DaLiA replay — see
// lib/types.ts DataSourceType), so LIVE SOURCE is never claimed here.
export function SourceStatusStrip() {
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  const dataSourceStatus = useMissionStore((state) => state.dataSourceStatus);
  const { snapshot: latest, isWaitingForConfirmation } = useConfirmedSnapshot();
  const isReplay = useDatasetReplayMode();

  const connected = connectionStatus === "open";
  // REST is authoritative for identity (corrective §3.3 precedence #1); the
  // confirmed snapshot is only a fallback, and only when it has already
  // passed snapshotMatchesConfirmedSource (precedence #2) — never a raw,
  // possibly cross-source `latest` read.
  const datasetName = dataSourceStatus?.dataset_name ?? latest?.source.dataset_name;
  const subjectId = dataSourceStatus?.subject_id ?? latest?.source.subject_id;

  const dataSourceLabel = deriveSourceLabel({ connectionStatus, isReplay });
  const sessionLabel = !connected
    ? "Unavailable"
    : isWaitingForConfirmation
      ? "Waiting for a confirmed frame from the selected source."
      : isReplay
        ? `${datasetName ?? "PPG-DaLiA"} · ${subjectId ?? "subject not loaded"}`
        : "Synthetic demo session";

  return (
    <div
      className="flex flex-col gap-3 rounded-md border border-jury-border-subtle bg-surface-1 px-4 py-3 sm:flex-row sm:flex-wrap sm:items-center sm:gap-8"
      role="status"
    >
      <div className="flex flex-col gap-0.5">
        <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-ink-muted">Data source</span>
        <span
          className={
            dataSourceLabel === "UNAVAILABLE"
              ? "text-sm font-semibold text-jury-fault"
              : "text-sm font-semibold text-information"
          }
        >
          {dataSourceLabel}
        </span>
      </div>
      <div className="flex flex-col gap-0.5">
        <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-ink-muted">Session</span>
        <span className="text-sm text-ink-secondary">{sessionLabel}</span>
      </div>
      <div className="flex flex-col gap-0.5">
        <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-ink-muted">Claim scope</span>
        <span className="text-sm font-semibold text-ink-primary">Demonstration interface</span>
      </div>
      <p className="text-xs leading-relaxed text-ink-muted sm:ml-auto sm:max-w-xs">{DASHBOARD_VS_RESULTS_STATEMENT}</p>
    </div>
  );
}
