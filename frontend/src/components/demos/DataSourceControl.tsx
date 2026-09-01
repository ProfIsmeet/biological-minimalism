"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { Database } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { api } from "@/lib/api";
import type { DataSourceStatus } from "@/lib/types";
import { useMissionStore } from "@/store/missionStore";

const SPEEDS = [1, 5, 10] as const;

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Data-source request failed.";
}

export function DataSourceControl() {
  const [status, setStatus] = useState<DataSourceStatus | null>(null);
  const [subjects, setSubjects] = useState<string[]>([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const latestSource = useMissionStore((state) => state.latest?.source);

  useEffect(() => {
    let cancelled = false;
    api.getDataSourceState().then((result) => {
      if (!cancelled) setStatus(result);
    }).catch((reason: unknown) => {
      if (!cancelled) setError(errorMessage(reason));
    });
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
      setStatus(await operation());
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setPending(null);
    }
  }

  const isReplay = (status?.source_type ?? latestSource?.source_type) === "dataset_replay";
  const latestMatchesStatus = latestSource?.source_type === status?.source_type && latestSource?.subject_id === status?.subject_id;
  const playbackState = status?.playback_state === "playing" && latestMatchesStatus
    ? (latestSource?.playback_state ?? status.playback_state)
    : (status?.playback_state ?? latestSource?.playback_state);
  const speed = status?.playback_speed ?? latestSource?.playback_speed ?? 1;
  const position = playbackState === "playing" || playbackState === "ended"
    ? (latestSource?.replay_position_seconds ?? status?.replay_position_seconds ?? 0)
    : (status?.replay_position_seconds ?? latestSource?.replay_position_seconds ?? 0);
  const duration = status?.duration_seconds ?? latestSource?.duration_seconds ?? 0;
  const activeSubject = status?.subject_id ?? latestSource?.subject_id;

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
            <p className="mt-1 text-slate-500">Previously recorded synchronized human data; not live hardware or trained-model inference.</p>
          </div>
        ) : null}
        {!status?.dataset_configured && !subjects.length ? (
          <p className="text-xs text-slate-500">Set <span className="tabular-nums-mono">BIOMIN_PPG_DALIA_PATH</span> in the backend environment to enable replay.</p>
        ) : null}
        {error ? <p className="text-xs text-signal-critical">{error}</p> : null}
      </div>
    </Panel>
  );
}
