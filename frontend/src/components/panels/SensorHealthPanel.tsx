"use client";

import { Cpu, Radio, Thermometer, Waves } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { StatusBadge, type StatusLevel } from "@/components/ui/StatusBadge";
import { SENSOR_NAMES, type SensorName, type SensorStatus } from "@/lib/types";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

const SENSOR_ICONS: Record<SensorName, LucideIcon> = {
  eeg: Cpu,
  ppg: Waves,
  temperature: Thermometer,
  bioimpedance: Radio,
};

// Channels emitted by the synthetic mock-data engine that are NOT part of the
// frozen selected architecture (CORE_PLUS_CONTEXT = PPG+IMU / ECG / EEG+EOG).
// Peripheral temperature and bio-impedance were evaluated but not selected;
// they are tagged here so a viewer never mistakes the demo signal stream for
// the deployed sensor set (see SelectedArchitecturePanel).
const NOT_SELECTED_SENSORS: ReadonlySet<SensorName> = new Set(["temperature", "bioimpedance"]);

function statusToLevel(status: SensorStatus): StatusLevel {
  if (status === "offline") return "offline";
  if (status === "degraded") return "warning";
  return "nominal";
}

export function SensorHealthPanel() {
  const sensors = useMissionStore((state) => state.latest?.sensor_health?.sensors);
  const liveChannels = useMissionStore((state) => state.latest?.source.available_channels);
  const configuredChannelMetadata = useMissionStore((state) => state.dataSourceStatus?.channels);
  const fault = useMissionStore((state) => state.latest?.fault_injection);
  const isReplay = useDatasetReplayMode();
  const configuredChannels = configuredChannelMetadata?.map((channel) => channel.name) ?? [];
  const availableChannels = liveChannels?.length ? liveChannels : configuredChannels;

  return (
    <Panel
      title="Sensor Health"
      subtitle="Synthetic demo signal stream — not the selected flight architecture"
      icon={<Radio size={16} />}
    >
      <div className="grid grid-cols-2 gap-3">
        {SENSOR_NAMES.map(({ value, label }) => {
          const notSelected = NOT_SELECTED_SENSORS.has(value);
          const reading = sensors?.find((s) => s.sensor === value);
          const recorded = isReplay && (
            (value === "ppg" && availableChannels.includes("wrist_bvp"))
            || (value === "temperature" && availableChannels.includes("wrist_temp"))
          );
          const faulted = Boolean(
            fault?.active
            && value === "ppg"
            && fault.target_channels.includes("wrist_bvp"),
          );
          const Icon = SENSOR_ICONS[value];
          const level: StatusLevel = reading
            ? statusToLevel(reading.status)
            : faulted
              ? "warning"
            : recorded
              ? "nominal"
              : isReplay
                ? "offline"
                : "nominal";
          return (
            <div key={value} className="flex flex-col gap-2 rounded-lg border border-white/5 bg-white/[0.02] p-3">
              <div className="flex items-center gap-2 text-slate-300">
                <Icon size={15} className={notSelected ? "text-amber-400/70" : "text-cyan-400"} />
                <span className="text-xs font-medium">{label}</span>
                {notSelected ? (
                  <span
                    className="ml-auto rounded-full border border-amber-400/25 bg-amber-400/[0.08] px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-amber-300"
                    title="Evaluated but not part of the selected architecture"
                  >
                    Not selected
                  </span>
                ) : null}
              </div>
              <StatusBadge level={level} label={reading ? `${reading.status[0]!.toUpperCase()}${reading.status.slice(1)}` : faulted ? "Fault injected" : recorded ? "Recorded" : isReplay ? "Unavailable" : "Nominal"} />
              <span className="tabular-nums-mono text-[11px] text-slate-500">
                {faulted ? "Corrupted replay signal · quality not inferred" : recorded ? "Signal quality not assessed" : `Signal quality ${reading ? `${(reading.signal_quality * 100).toFixed(0)}%` : "—"}`}
              </span>
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-[10px] leading-relaxed text-slate-500">
        These are the synthetic mock-data engine&apos;s demo channels, not the deployed sensor set. Peripheral temperature and
        bio-impedance were evaluated but are not in the selected architecture — see Selected Architecture above for the frozen
        Wrist (PPG + IMU) · Chest (ECG) · Head (frontal EEG + EOG) selection.
      </p>
    </Panel>
  );
}
