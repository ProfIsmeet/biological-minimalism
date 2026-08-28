"use client";

import { Activity } from "lucide-react";

import { WaveformChart } from "@/components/charts/WaveformChart";
import { Panel } from "@/components/ui/Panel";
import { useMissionStore } from "@/store/missionStore";

export function LiveWaveformsPanel() {
  const vitals = useMissionStore((state) => state.latest?.vitals);
  const ppgSensor = useMissionStore((state) => state.latest?.sensor_health.sensors.find((s) => s.sensor === "ppg"));
  const isOffline = ppgSensor?.status === "offline";

  return (
    <Panel title="Live Waveforms" subtitle="PPG pulse waveform & derived ECG-like stream" icon={<Activity size={16} />}>
      <div className="flex flex-col gap-4">
        <div>
          <p className="mb-1 text-[11px] uppercase tracking-wider text-slate-500">PPG Waveform</p>
          <WaveformChart data={vitals?.ppg_waveform ?? []} color="#4fd8e8" flatline={isOffline} />
        </div>
        <div>
          <p className="mb-1 text-[11px] uppercase tracking-wider text-slate-500">ECG-like Stream (PPG-timing derived)</p>
          <WaveformChart data={vitals?.ecg_like_waveform ?? []} color="#33e0a1" flatline={isOffline} />
        </div>
      </div>
    </Panel>
  );
}
