"use client";

import { useState } from "react";
import clsx from "clsx";
import { Sun } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { api } from "@/lib/api";
import { MISSION_MODES } from "@/lib/types";
import { useMissionStore } from "@/store/missionStore";

/** Demo 2 — Solar Storm Mode. Switches the mock engine's operational
 * context; the effect (noise, risk, charts) shows up on the next WS frame. */
export function MissionModeSwitcher() {
  const currentMode = useMissionStore((state) => state.latest?.mission_mode);
  const isReplay = useMissionStore((state) => state.latest?.source.source_type === "dataset_replay");
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSelect(mode: (typeof MISSION_MODES)[number]["value"]) {
    setPending(mode);
    setError(null);
    try {
      await api.setMissionMode(mode);
    } catch {
      setError("Could not reach the mission control API.");
    } finally {
      setPending(null);
    }
  }

  return (
    <Panel title="Mission Mode" subtitle="Demo — Solar Storm Mode" icon={<Sun size={16} />}>
      <div className="grid grid-cols-2 gap-2">
        {MISSION_MODES.map((mode) => {
          const isActive = currentMode === mode.value;
          return (
            <button
              key={mode.value}
              type="button"
              onClick={() => handleSelect(mode.value)}
              disabled={pending !== null || isReplay}
              aria-pressed={isActive}
              className={clsx(
                "rounded-lg border px-3 py-2.5 text-left text-xs font-medium transition-colors disabled:opacity-60",
                isActive
                  ? "border-cyan-400/40 bg-cyan-500/10 text-cyan-300"
                  : "border-white/5 bg-white/[0.02] text-slate-400 hover:border-white/10 hover:text-slate-200",
                mode.value === "solar_event" && isActive && "border-amber-400/50 bg-amber-500/10 text-amber-300",
              )}
            >
              {mode.label}
              {pending === mode.value ? <span className="ml-1 text-slate-500">…</span> : null}
            </button>
          );
        })}
      </div>
      {error ? <p className="mt-2 text-xs text-signal-critical">{error}</p> : null}
      {isReplay ? <p className="mt-2 text-xs text-slate-500">Mission-mode simulation is unavailable during real dataset replay.</p> : null}
    </Panel>
  );
}
