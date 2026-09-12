"use client";

import { HeartPulse } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { MetricTile } from "@/components/ui/MetricTile";
import type { ModelInferenceStatus } from "@/lib/types";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

const INFERENCE_VALUE: Record<ModelInferenceStatus, string> = {
  warming_up: "Waiting",
  available: "Unavailable",
  input_unavailable: "Input unavailable",
  model_unavailable: "Model unavailable",
  error: "Inference error",
};

export function PrimaryVitalsPanel() {
  const latest = useMissionStore((state) => state.latest);
  const isReplay = useDatasetReplayMode();
  const prediction = isReplay ? latest?.heart_rate_prediction : null;
  const inference = isReplay ? latest?.heart_rate_inference : null;
  const fault = isReplay
    ? (prediction?.provenance.fault_injection ?? latest?.fault_injection)
    : null;
  const vitals = isReplay ? null : latest?.vitals;
  const heartRate = isReplay ? prediction?.value : vitals?.heart_rate_bpm;
  const hrv = vitals?.hrv_rmssd_ms;
  const respiration = vitals?.respiration_rate_bpm;
  const systolic = vitals?.blood_pressure_systolic_mmhg;
  const diastolic = vitals?.blood_pressure_diastolic_mmhg;
  const inferenceStatus = inference?.status;
  const replayHeartRateValue = prediction
    ? prediction.value.toFixed(1)
    : INFERENCE_VALUE[inferenceStatus ?? "warming_up"];
  const windowEnd = prediction
    ? prediction.provenance.window_start_seconds + prediction.provenance.window_duration_seconds
    : null;
  const heartRateHint = isReplay
    ? prediction
      ? `AI Estimated · PPG + IMU model · ${prediction.provenance.dataset_name} ${prediction.provenance.subject_id} · window ${prediction.provenance.window_start_seconds.toFixed(1)}–${windowEnd?.toFixed(1)} s${fault?.active ? ` · FAULT-INJECTED ${fault.target?.toUpperCase()} (${fault.fault_type?.replaceAll("_", " ")}, severity ${fault.severity}, seed ${fault.seed})` : ""}`
      : (inference?.message ?? "AI Estimated · Waiting for recorded replay data.")
    : undefined;
  const heartRateLevel: "nominal" | "warning" | "offline" = !isReplay || prediction
    ? "nominal"
    : inferenceStatus === "warming_up" || inferenceStatus === undefined
      ? "warning"
      : "offline";

  return (
    <Panel
      title="Primary Vitals"
      subtitle={isReplay ? (fault?.active ? "Fault-injected replay with validated AI estimation" : "Recorded signals with validated AI estimation") : "Cardiovascular & respiratory"}
      icon={<HeartPulse size={16} />}
    >
      <div className="grid grid-cols-2 gap-3">
        <MetricTile
          label="Heart Rate"
          value={isReplay ? replayHeartRateValue : (heartRate != null ? heartRate.toFixed(0) : "Unavailable")}
          unit={heartRate != null ? "bpm" : undefined}
          level={heartRateLevel}
          hint={heartRateHint}
        />
        <MetricTile
          label="HRV (RMSSD)"
          value={hrv != null ? hrv.toFixed(0) : "Unavailable"}
          unit={hrv != null ? "ms" : undefined}
          hint={isReplay ? "Unavailable · no validated replay model" : undefined}
        />
        <MetricTile
          label="Respiration"
          value={respiration != null ? respiration.toFixed(1) : "Unavailable"}
          unit={respiration != null ? "breaths/min" : undefined}
          hint={isReplay ? "Unavailable · no validated replay model" : undefined}
        />
        <MetricTile
          label="Estimated Blood Pressure"
          value={systolic != null && diastolic != null ? `${systolic.toFixed(0)}/${diastolic.toFixed(0)}` : "Unavailable"}
          unit={systolic != null && diastolic != null ? "mmHg" : undefined}
          hint={isReplay ? "Unavailable · no validated replay model" : "Cuffless PPG-derived estimate"}
        />
      </div>
    </Panel>
  );
}
