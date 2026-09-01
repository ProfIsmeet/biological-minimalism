"use client";

import { Cpu, Radio, Thermometer, Waves } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { StatusBadge, type StatusLevel } from "@/components/ui/StatusBadge";
import { SENSOR_NAMES, type SensorName, type SensorStatus } from "@/lib/types";
import { useMissionStore } from "@/store/missionStore";

const SENSOR_ICONS: Record<SensorName, LucideIcon> = {
  eeg: Cpu,
  ppg: Waves,
  temperature: Thermometer,
  bioimpedance: Radio,
};

function statusToLevel(status: SensorStatus): StatusLevel {
  if (status === "offline") return "offline";
  if (status === "degraded") return "warning";
  return "nominal";
}

export function SensorHealthPanel() {
  const sensors = useMissionStore((state) => state.latest?.sensor_health?.sensors);
  const isReplay = useMissionStore((state) => state.latest?.source.source_type === "dataset_replay");

  return (
    <Panel title="Sensor Health" subtitle="Four-sensor minimal architecture" icon={<Radio size={16} />}>
      <div className="grid grid-cols-2 gap-3">
        {SENSOR_NAMES.map(({ value, label }) => {
          const reading = sensors?.find((s) => s.sensor === value);
          const Icon = SENSOR_ICONS[value];
          const level = statusToLevel(reading?.status ?? "nominal");
          return (
            <div key={value} className="flex flex-col gap-2 rounded-lg border border-white/5 bg-white/[0.02] p-3">
              <div className="flex items-center gap-2 text-slate-300">
                <Icon size={15} className="text-cyan-400" />
                <span className="text-xs font-medium">{label}</span>
              </div>
              <StatusBadge level={level} label={reading ? `${reading.status[0]!.toUpperCase()}${reading.status.slice(1)}` : isReplay ? "Unavailable" : "Nominal"} />
              <span className="tabular-nums-mono text-[11px] text-slate-500">
                Signal quality {reading ? `${(reading.signal_quality * 100).toFixed(0)}%` : "—"}
              </span>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}
