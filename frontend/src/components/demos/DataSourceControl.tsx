"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { Database } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { api } from "@/lib/api";
import { deriveFaultSummaryLabel } from "@/lib/monitoring/inferenceState";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import type { DataSourceStatus, ReplayFaultTarget, ReplayFaultType } from "@/lib/types";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

const SPEEDS = [1, 5, 10] as const;
const FAULT_TYPES: { value: ReplayFaultType; label: string }[] = [
  { value: "modality_dropout", label: "Modality dropout" },
  { value: "packet_loss", label: "Packet/sample loss" },
  { value: "frozen_sensor", label: "Frozen sensor" },
  { value: "additive_noise", label: "Additive noise" },
  { value: "saturation", label: "Saturation/clipping" },
];

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Data-source request failed.";
}

/**
 * Prompt-2B corrective §4.1 — this control used to keep its own local
 * `status` copy of `DataSourceStatus`, fetched independently on mount, in
 * addition to the canonical `missionStore.dataSourceStatus` that
 * `LiveFeedProvider` (root layout) already populates on every route before
 * any page content mounts. Two independent copies of the same authoritative
 * value can only ever diverge, never help, so this now reads
 * `dataSourceStatus` directly from the store — there is exactly one
 * representation of "the current REST-confirmed source state" in the app.
 * The only fetch this component still performs on mount is the
 * control-specific subject list, which nothing else on this route already
 * loads. Per-frame information (fault, position) is read only through
 * `useConfirmedSnapshot()`, never a raw `latest`.
 */
export function DataSourceControl() {
  const status = useMissionStore((state) => state.dataSourceStatus);
  const setDataSourceStatus = useMissionStore((state) => state.setDataSourceStatus);
  const { snapshot: latest } = useConfirmedSnapshot();
  const isReplay = useDatasetReplayMode();

  const [subjects, setSubjects] = useState<string[]>([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [faultType, setFaultType] = useState<ReplayFaultType>("modality_dropout");
  const [faultTarget, setFaultTarget] = useState<ReplayFaultTarget>("ppg");
  const [faultSeverity, setFaultSeverity] = useState(1);
  const [faultSeed, setFaultSeed] = useState(0);

  useEffect(() => {
    let cancelled = false;
    api.getReplaySubjects().then((result) => {
      if (cancelled) return;
      setSubjects(result.subjects);
      setSelectedSubject((current) => current || result.subjects[0] || "");
    }).catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  async function run(key: string, operation: () => Promise<DataSourceStatus>) {
    setPending(key);
    setError(null);
    try {
      const result = await operation();
      setDataSourceStatus(result);
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setPending(null);
    }
  }

  const latestSource = latest?.source;
  const latestFault = latest?.fault_injection;
  const playbackState = status?.playback_state ?? latestSource?.playback_state;
  const speed = status?.playback_speed ?? latestSource?.playback_speed ?? 1;
  // Prompt-2C §5 — replay position is continuously advancing frame telemetry,
  // not identity/configuration, so it must prefer the confirmed WebSocket
  // snapshot over REST. `status.replay_position_seconds` is only a snapshot
  // taken at the moment of the last control action (play/pause/seek) and
  // does not advance on its own between REST polls; `latestSource` comes
  // from `useConfirmedSnapshot()`, so it is already fail-closed to the
  // authoritative source type and replay subject, and therefore safe to
  // prefer here without risking a cross-source position leak.
  const position = latestSource?.replay_position_seconds ?? status?.replay_position_seconds ?? 0;
  const duration = status?.duration_seconds ?? latestSource?.duration_seconds ?? 0;
  const activeSubject = status?.subject_id ?? latestSource?.subject_id;
  // A rejected (mismatched-source) snapshot's fault must never override the
  // current REST fault state — `latestFault` here already comes only from
  // the confirmed snapshot, so falling back to `status.fault_injection`
  // (part of the same authoritative REST payload as `status` itself) is
  // always safe.
  const activeFault = latestFault?.active ? latestFault : status?.fault_injection;
  const severityIsConfigurable = faultType === "packet_loss" || faultType === "additive_noise" || faultType === "saturation";

  return (
    <Panel title="Data Source" subtitle="Synthetic demo or real PPG-DaLiA recording" icon={<Database size={16} />}>
      <div className="flex flex-col gap-4 text-sm">
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => run("synthetic", api.useSyntheticSource)}
            disabled={pending !== null}
            className={clsx(
              "rounded-lg border px-3 py-2.5 text-left text-xs font-medium transition-colors disabled:opacity-60",
              !isReplay ? "border-cyan-400/40 bg-cyan-500/10 text-cyan-300" : "border-white/5 text-slate-400",
            )}
          >
            Synthetic Demo
          </button>
          <div className={clsx(
            "rounded-lg border px-3 py-2.5 text-xs font-medium",
            isReplay ? "border-cyan-400/40 bg-cyan-500/10 text-cyan-300" : "border-white/5 text-slate-400",
          )}>
            PPG-DaLiA Replay
          </div>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row">
          <select
            value={selectedSubject}
            onChange={(event) => setSelectedSubject(event.target.value)}
            disabled={!subjects.length || pending !== null}
            className="min-w-40 rounded-lg border border-white/10 bg-space-900 px-3 py-2 text-xs text-slate-200 disabled:opacity-50"
          >
            {subjects.length ? subjects.map((subject) => <option key={subject}>{subject}</option>) : <option>Dataset not configured</option>}
          </select>
          <button
            type="button"
            onClick={() => run("load", () => api.loadReplaySubject(selectedSubject))}
            disabled={!selectedSubject || pending !== null}
            className="rounded-lg border border-cyan-400/30 bg-cyan-500/10 px-3 py-2 text-xs font-medium text-cyan-300 disabled:opacity-50"
          >
            {pending === "load" ? "Loading real subject…" : "Load Subject"}
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          <button type="button" disabled={!isReplay || pending !== null || playbackState === "ended"} onClick={() => run("play", api.playReplay)} className="rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 disabled:opacity-40">Play</button>
          <button type="button" disabled={!isReplay || pending !== null} onClick={() => run("pause", api.pauseReplay)} className="rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 disabled:opacity-40">Pause</button>
          <button type="button" disabled={!isReplay || pending !== null} onClick={() => run("reset", api.resetReplay)} className="rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-300 disabled:opacity-40">Reset</button>
          <span className="mx-1 self-center text-[10px] uppercase tracking-wider text-slate-600">Speed</span>
          {SPEEDS.map((value) => (
            <button
              key={value}
              type="button"
              disabled={!isReplay || pending !== null}
              onClick={() => run(`speed-${value}`, () => api.setReplaySpeed(value))}
              className={clsx(
                "rounded-md border px-2.5 py-1.5 text-xs disabled:opacity-40",
                speed === value ? "border-cyan-400/40 text-cyan-300" : "border-white/10 text-slate-500",
              )}
            >
              {value}x
            </button>
          ))}
        </div>

        {isReplay ? (
          <div className="rounded-lg border border-cyan-400/15 bg-cyan-500/5 p-3 text-xs text-slate-400">
            <p className="font-semibold uppercase tracking-wider text-cyan-300">Real Recorded Data — Replay Mode</p>
            <p className="mt-1">PPG-DaLiA · {activeSubject} · {playbackState} · {position.toFixed(1)} / {duration.toFixed(1)} s · {speed}x</p>
            <p className="mt-1 text-slate-500">Recorded/measured: wrist PPG, wrist IMU, chest ECG, and temperature when loaded.</p>
            <p className="mt-1 text-slate-500">AI estimated: PPG + IMU heart-rate estimate. Not live astronaut monitoring.</p>
            {activeSubject === "S14" ? (
              <p className="mt-1 text-amber-300/90">S14 single-participant robustness demonstration; not population validation.</p>
            ) : null}
          </div>
        ) : null}
        {isReplay ? (
          <div className="rounded-lg border border-amber-400/20 bg-amber-400/5 p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-amber-300">Simulated fault injection</p>
            <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
              <select
                value={faultType}
                onChange={(event) => {
                  const value = event.target.value as ReplayFaultType;
                  setFaultType(value);
                  setFaultSeverity(value === "modality_dropout" || value === "frozen_sensor" ? 1 : 0.25);
                }}
                disabled={pending !== null}
                className="rounded-lg border border-white/10 bg-space-900 px-3 py-2 text-xs text-slate-200 disabled:opacity-50"
              >
                {FAULT_TYPES.map((fault) => <option key={fault.value} value={fault.value}>{fault.label}</option>)}
              </select>
              <select
                value={faultTarget}
                onChange={(event) => setFaultTarget(event.target.value as ReplayFaultTarget)}
                disabled={pending !== null}
                className="rounded-lg border border-white/10 bg-space-900 px-3 py-2 text-xs text-slate-200 disabled:opacity-50"
              >
                <option value="ppg">PPG</option>
                <option value="imu">IMU</option>
                <option value="both">PPG + IMU</option>
              </select>
              <label className="flex items-center gap-2 text-xs text-slate-400">
                Severity
                <input
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={faultSeverity}
                  disabled={!severityIsConfigurable || pending !== null}
                  onChange={(event) => setFaultSeverity(Number(event.target.value))}
                  className="w-20 rounded-md border border-white/10 bg-space-900 px-2 py-1.5 text-slate-200 disabled:opacity-40"
                />
              </label>
              <label className="flex items-center gap-2 text-xs text-slate-400">
                Seed
                <input
                  type="number"
                  min={0}
                  step={1}
                  value={faultSeed}
                  disabled={pending !== null}
                  onChange={(event) => setFaultSeed(Number(event.target.value))}
                  className="w-24 rounded-md border border-white/10 bg-space-900 px-2 py-1.5 text-slate-200 disabled:opacity-40"
                />
              </label>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              <button
                type="button"
                disabled={pending !== null}
                onClick={() => run("fault-enable", () => api.configureReplayFault({
                  fault_type: faultType,
                  target: faultTarget,
                  severity: severityIsConfigurable ? faultSeverity : 1,
                  seed: faultSeed,
                }))}
                className="rounded-md border border-amber-400/30 bg-amber-400/10 px-3 py-1.5 text-xs font-medium text-amber-300 disabled:opacity-40"
              >
                Enable fault
              </button>
              <button
                type="button"
                disabled={!activeFault?.active || pending !== null}
                onClick={() => run("fault-disable", api.clearReplayFault)}
                className="rounded-md border border-white/10 px-3 py-1.5 text-xs text-slate-400 disabled:opacity-40"
              >
                Disable / clear
              </button>
            </div>
            {activeFault?.active ? (
              <p className="mt-2 text-xs text-amber-200">{deriveFaultSummaryLabel(activeFault)} · seed {activeFault.seed}</p>
            ) : (
              <p className="mt-2 text-xs text-slate-500">Disabled — clean replay samples pass through unchanged.</p>
            )}
          </div>
        ) : null}
        {!status?.dataset_configured && !subjects.length ? (
          <p className="text-xs text-slate-500">Recorded PPG-DaLiA replay is not available on this deployment. Contact the demo administrator or run the presenter preflight to enable it.</p>
        ) : null}
        {error ? <p className="text-xs text-signal-critical">{error}</p> : null}
      </div>
    </Panel>
  );
}
