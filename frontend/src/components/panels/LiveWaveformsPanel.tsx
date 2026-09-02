"use client";

import { Activity } from "lucide-react";

import { WaveformChart } from "@/components/charts/WaveformChart";
import { Panel } from "@/components/ui/Panel";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

export function LiveWaveformsPanel() {
  const latest = useMissionStore((state) => state.latest);
  const vitals = latest?.vitals;
  const isReplay = useDatasetReplayMode();
  const fault = latest?.fault_injection;
  const ppgIsFaulted = fault?.active && fault.target_channels.includes("wrist_bvp");
  const ppgSensor = latest?.sensor_health?.sensors.find((s) => s.sensor === "ppg");
  const isOffline = ppgSensor?.status === "offline";
  const scalarBatch = (name: string): number[] => {
    const samples = latest?.channels.find((batch) => batch.channel_name === name)?.samples;
    if (!samples?.length) return [];
    return typeof samples[0] === "number" ? (samples as number[]) : (samples as number[][]).map((row) => row[0] ?? 0);
  };
  const ppg = isReplay ? scalarBatch("wrist_bvp") : (vitals?.ppg_waveform ?? []);
  const ecg = isReplay ? scalarBatch("chest_ecg") : (vitals?.ecg_like_waveform ?? []);

  return (
    <Panel
      title="Live Waveforms"
      subtitle={isReplay ? "Real synchronized PPG-DaLiA channels" : "Synthetic PPG pulse waveform & derived ECG-like stream"}
      icon={<Activity size={16} />}
    >
      <div className="flex flex-col gap-4">
        {isReplay ? (
          <p className="text-xs text-slate-500">
            {fault?.active
              ? `Fault-injected replay: ${fault.fault_type?.replaceAll("_", " ")} targets ${fault.target}. Unaffected channels remain recorded measurements.`
              : "Recorded/measured channels: wrist PPG, wrist IMU, chest ECG, and wrist temperature when loaded."}
          </p>
        ) : null}
        <div>
          <p className="mb-1 text-[11px] uppercase tracking-wider text-slate-500">
            {ppgIsFaulted ? "Fault-injected PPG waveform" : "PPG Waveform"}
          </p>
          <WaveformChart data={ppg} color="#4fd8e8" flatline={isOffline} />
        </div>
        <div>
          <p className="mb-1 text-[11px] uppercase tracking-wider text-slate-500">
            {isReplay ? "Recorded Chest ECG" : "ECG-like Stream (PPG-timing derived)"}
          </p>
          <WaveformChart data={ecg} color="#33e0a1" flatline={isOffline} />
        </div>
      </div>
    </Panel>
  );
}
