"use client";

import { HeartPulse } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { MetricTile } from "@/components/ui/MetricTile";
import { useMissionStore } from "@/store/missionStore";

export function PrimaryVitalsPanel() {
  const vitals = useMissionStore((state) => state.latest?.vitals);
  const heartRate = vitals?.heart_rate_bpm;
  const hrv = vitals?.hrv_rmssd_ms;
  const respiration = vitals?.respiration_rate_bpm;
  const systolic = vitals?.blood_pressure_systolic_mmhg;
  const diastolic = vitals?.blood_pressure_diastolic_mmhg;

  return (
    <Panel title="Primary Vitals" subtitle="Cardiovascular & respiratory" icon={<HeartPulse size={16} />}>
      <div className="grid grid-cols-2 gap-3">
        <MetricTile label="Heart Rate" value={heartRate != null ? heartRate.toFixed(0) : "Unavailable"} unit="bpm" />
        <MetricTile label="HRV (RMSSD)" value={hrv != null ? hrv.toFixed(0) : "Unavailable"} unit="ms" />
        <MetricTile label="Respiration" value={respiration != null ? respiration.toFixed(1) : "Unavailable"} unit="breaths/min" />
        <MetricTile
          label="Estimated Blood Pressure"
          value={systolic != null && diastolic != null ? `${systolic.toFixed(0)}/${diastolic.toFixed(0)}` : "Unavailable"}
          unit="mmHg"
          hint="Cuffless PPG-derived estimate"
        />
      </div>
    </Panel>
  );
}
