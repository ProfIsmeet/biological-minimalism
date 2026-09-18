"use client";

import clsx from "clsx";
import { Wifi, WifiOff } from "lucide-react";

import { MissionClock } from "@/components/layout/MissionClock";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { confidenceLevel } from "@/lib/format";
import { formatFaultTypeLabel } from "@/lib/monitoring/formatMonitoringValue";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { deriveConnectionLabel, deriveSourceLabel } from "@/lib/sourceLabel";
import { MISSION_MODES } from "@/lib/types";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

// Legacy Mission-Control-style top bar. As of this corrective pass it is
// rendered only on secondary/reference routes (live-monitoring, digital-twin,
// ai-insights, mission-timeline, settings) — /mission-overview, /research,
// and /research/experimental render PresentationHeader instead (see
// components/layout/AppHeader.tsx). Even here, synthetic data must never be
// labeled "Live" — the connection badge below uses the shared
// deriveSourceLabel/deriveConnectionLabel helpers, same as every other
// source-scope surface in the app.
//
// Prompt-2 corrective pass §1/§2: every fault-derived field below is read
// through `useConfirmedSnapshot()` rather than raw `latest`, so a
// late-arriving WebSocket frame from a source the user has since switched
// away from can never repopulate this bar with a stale fault, dataset, or
// subject label. `dataSourceStatus.fault_injection` is part of the same
// authoritative REST response as `dataSourceStatus` itself, so it is always
// safe to use as a fallback — it can never be "from the wrong source".
export function TopBar() {
  const dataSourceStatus = useMissionStore((state) => state.dataSourceStatus);
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  const isReplay = useDatasetReplayMode();
  const { snapshot: confirmedLatest } = useConfirmedSnapshot();

  const modeLabel = MISSION_MODES.find((m) => m.value === confirmedLatest?.mission_mode)?.label ?? "Earth Orbit";
  const confidence = isReplay ? null : (confirmedLatest?.ai_confidence?.overall_confidence ?? null);
  const missionDay = confirmedLatest?.mission_day ?? 1;
  const datasetName = dataSourceStatus?.dataset_name ?? confirmedLatest?.source.dataset_name;
  const subjectId = dataSourceStatus?.subject_id ?? confirmedLatest?.source.subject_id;
  const fault = confirmedLatest?.fault_injection?.active
    ? confirmedLatest.fault_injection
    : dataSourceStatus?.fault_injection;

  return (
    <header className="flex items-center justify-between gap-4 border-b border-white/5 bg-space-900/60 px-4 py-3 backdrop-blur-sm sm:px-6">
      <div className="flex items-center gap-3">
        <p className="text-sm font-semibold text-slate-100">Mission Control</p>
        <span className="hidden text-slate-600 sm:inline">/</span>
        <span className="hidden text-xs uppercase tracking-wider text-slate-400 sm:inline">
          {isReplay ? `${datasetName ?? "PPG-DaLiA"} · ${subjectId ?? "subject not loaded"}` : modeLabel}
        </span>
      </div>

      <div className="flex items-center gap-3 sm:gap-5">
        {isReplay && fault?.active ? (
          <span className="hidden rounded-full border border-amber-400/30 bg-amber-400/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-amber-300 md:inline">
            Simulated Fault Active · {fault.target} · {formatFaultTypeLabel(fault.fault_type)}
            {fault.severity !== null && fault.severity !== undefined ? ` · severity ${fault.severity}` : ""}
          </span>
        ) : null}
        {isReplay ? (
          <span className="hidden text-[10px] font-semibold uppercase tracking-wider text-cyan-300 lg:inline">
            Real Recorded Data — Replay Mode
          </span>
        ) : (
          <span className="hidden text-xs uppercase tracking-wider text-slate-500 sm:inline">
            Mission Day <span className="tabular-nums-mono text-slate-300">{missionDay.toFixed(1)}</span>
          </span>
        )}
        <MissionClock />
        {confidence !== null ? (
          <StatusBadge level={confidenceLevel(confidence)} label={`AI Confidence ${confidence.toFixed(0)}%`} />
        ) : null}
        <span
          className={clsx(
            "flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-wide",
            connectionStatus === "open"
              ? "border-signal-nominal/30 bg-signal-nominal/10 text-signal-nominal"
              : "border-signal-warning/30 bg-signal-warning/10 text-signal-warning",
          )}
        >
          {connectionStatus === "open" ? <Wifi size={12} /> : <WifiOff size={12} />}
          {deriveSourceLabel({ connectionStatus, isReplay })} · {deriveConnectionLabel(connectionStatus)}
        </span>
      </div>
    </header>
  );
}
