"use client";

import { useState } from "react";
import clsx from "clsx";
import { AlertTriangle } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { api } from "@/lib/api";
import { SENSOR_NAMES, type SensorStatus } from "@/lib/types";
import { useMissionStore } from "@/store/missionStore";

const STATUS_OPTIONS: { value: SensorStatus; label: string }[] = [
  { value: "nominal", label: "Nominal" },
  { value: "degraded", label: "Degraded" },
  { value: "offline", label: "Offline" },
];

/** Demo 1 — Sensor Failure Simulation. Flips a sensor's status; the mock
 * engine recomputes AI confidence and the explanation on the next tick. */
export function SensorFailureControl() {
  const sensors = useMissionStore((state) => state.latest?.sensor_health?.sensors);
  const isReplay = useMissionStore((state) => state.latest?.source.source_type === "dataset_replay");
  const [pendingKey, setPendingKey] = useState<string | null>(null);

  async function handleSet(sensor: (typeof SENSOR_NAMES)[number]["value"], status: SensorStatus) {
    const key = `${sensor}:${status}`;
    setPendingKey(key);
    try {
      await api.setSensorFailure(sensor, status);
    } finally {
      setPendingKey(null);
    }
  }

  return (
    <Panel title="Sensor Failure Simulation" subtitle="Demo — inject a failure and watch AI Confidence react" icon={<AlertTriangle size={16} />}>
      <div className="flex flex-col gap-3">
        {SENSOR_NAMES.map(({ value, label }) => {
          const current = sensors?.find((s) => s.sensor === value)?.status ?? "nominal";
          return (
            <div key={value} className="flex items-center justify-between gap-3 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5">
              <span className="text-xs font-medium text-slate-300">{label}</span>
              <div className="flex gap-1.5">
                {STATUS_OPTIONS.map((option) => {
                  const isActive = current === option.value;
                  const isPending = pendingKey === `${value}:${option.value}`;
                  return (
                    <button
                      key={option.value}
                      type="button"
                      aria-pressed={isActive}
                      onClick={() => handleSet(value, option.value)}
                      disabled={isPending || isReplay}
                      className={clsx(
                        "rounded-md border px-2.5 py-1 text-[11px] font-medium transition-colors disabled:opacity-60",
                        isActive && option.value === "nominal" && "border-signal-nominal/40 bg-signal-nominal/10 text-signal-nominal",
                        isActive && option.value === "degraded" && "border-signal-warning/40 bg-signal-warning/10 text-signal-warning",
                        isActive && option.value === "offline" && "border-signal-critical/40 bg-signal-critical/10 text-signal-critical",
                        !isActive && "border-white/5 text-slate-500 hover:border-white/15 hover:text-slate-300",
                      )}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
      {isReplay ? <p className="mt-3 text-xs text-slate-500">Fault injection is intentionally not enabled for dataset replay in this phase.</p> : null}
    </Panel>
  );
}
