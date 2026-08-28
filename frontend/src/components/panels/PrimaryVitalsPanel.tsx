"use client";

import { HeartPulse } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { MetricTile } from "@/components/ui/MetricTile";
import { useMissionStore } from "@/store/missionStore";

export function PrimaryVitalsPanel() {
  const vitals = useMissionStore((state) => state.latest?.vitals);

  return (
    <Panel title="Primary Vitals" subtitle="Cardiovascular & respiratory" icon={<HeartPulse size={16} />}>
      <div className="grid grid-cols-2 gap-3">
        <MetricTile label="Heart Rate" value={vitals ? vitals.heart_rate_bpm.toFixed(0) : "—"} unit="bpm" />
        <MetricTile label="HRV (RMSSD)" value={vitals ? vitals.hrv_rmssd_ms.toFixed(0) : "—"} unit="ms" />
        <MetricTile label="Respiration" value={vitals ? vitals.respiration_rate_bpm.toFixed(1) : "—"} unit="breaths/min" />
        <MetricTile
          label="Estimated Blood Pressure"
          value={vitals ? `${vitals.blood_pressure_systolic_mmhg.toFixed(0)}/${vitals.blood_pressure_diastolic_mmhg.toFixed(0)}` : "—"}
          unit="mmHg"
          hint="Cuffless PPG-derived estimate"
        />
      </div>
    </Panel>
  );
}
