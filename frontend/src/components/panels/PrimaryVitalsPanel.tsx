"use client";

import { HeartPulse } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { MetricTile } from "@/components/ui/MetricTile";
import { deriveFaultSummaryLabel } from "@/lib/monitoring/inferenceState";
import { isFiniteMetricValue, metricGroupLevelForAvailability, metricLevelForAvailability } from "@/lib/monitoring/insightDisplay";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import type { ModelInferenceStatus } from "@/lib/types";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

const INFERENCE_VALUE: Record<ModelInferenceStatus, string> = {
  warming_up: "Waiting",
  available: "Unavailable",
  input_unavailable: "Input unavailable",
  model_unavailable: "Model unavailable",
  error: "Inference error",
};

export function PrimaryVitalsPanel() {
  const { snapshot: latest, isWaitingForConfirmation } = useConfirmedSnapshot();
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
  const heartRateAvailable = isFiniteMetricValue(heartRate);
  const hrvAvailable = isFiniteMetricValue(hrv);
  const respirationAvailable = isFiniteMetricValue(respiration);
  const bloodPressureAvailable = isFiniteMetricValue(systolic) && isFiniteMetricValue(diastolic);
  const inferenceStatus = inference?.status;
  const replayHeartRateValue = isWaitingForConfirmation
    ? "Waiting"
    : prediction
      ? prediction.value.toFixed(1)
      : INFERENCE_VALUE[inferenceStatus ?? "warming_up"];
  const windowEnd = prediction
    ? prediction.provenance.window_start_seconds + prediction.provenance.window_duration_seconds
    : null;
  const heartRateHint = isReplay
    ? isWaitingForConfirmation
      ? "Waiting for a confirmed frame from the selected source."
      : prediction
        ? `PPG + IMU heart-rate estimate · ${prediction.provenance.dataset_name} ${prediction.provenance.subject_id} · window ${prediction.provenance.window_start_seconds.toFixed(1)}–${windowEnd?.toFixed(1)} s${fault?.active ? ` · ${deriveFaultSummaryLabel(fault)}` : ""}`
        : (inference?.message ?? "PPG + IMU heart-rate estimate · Waiting for recorded replay data.")
    : undefined;
  const heartRateLevel = isWaitingForConfirmation
    ? "warning"
    : !isReplay
      ? metricLevelForAvailability(heartRate)
      : prediction
        ? "nominal"
      : inferenceStatus === "warming_up" || inferenceStatus === undefined
        ? "warning"
        : "offline";

  return (
    <Panel
      title="Primary Vitals"
      subtitle={
        isReplay
          ? isWaitingForConfirmation
            ? "Waiting for a confirmed frame from the selected source"
            : fault?.active
              ? "Recorded replay with an active simulated input fault"
              : "Recorded replay with a PPG + IMU heart-rate estimate"
          : "Cardiovascular & respiratory"
      }
      icon={<HeartPulse size={16} />}
    >
      <div className="grid grid-cols-2 gap-3">
        <MetricTile
          label="Heart Rate"
          value={isReplay ? replayHeartRateValue : (heartRateAvailable ? heartRate.toFixed(0) : "Unavailable")}
          unit={heartRateAvailable ? "bpm" : undefined}
          level={heartRateLevel}
          hint={heartRateHint}
        />
        <MetricTile
          label="HRV (RMSSD)"
          value={hrvAvailable ? hrv.toFixed(0) : "Unavailable"}
          unit={hrvAvailable ? "ms" : undefined}
          level={metricLevelForAvailability(hrv)}
          hint={isReplay ? "Unavailable · PPG + IMU model does not estimate this" : undefined}
        />
        <MetricTile
          label="Respiration"
          value={respirationAvailable ? respiration.toFixed(1) : "Unavailable"}
          unit={respirationAvailable ? "breaths/min" : undefined}
          level={metricLevelForAvailability(respiration)}
          hint={isReplay ? "Unavailable · PPG + IMU model does not estimate this" : undefined}
        />
        <MetricTile
          label="Estimated Blood Pressure"
          value={bloodPressureAvailable ? `${systolic.toFixed(0)}/${diastolic.toFixed(0)}` : "Unavailable"}
          unit={bloodPressureAvailable ? "mmHg" : undefined}
          level={metricGroupLevelForAvailability([systolic, diastolic])}
          hint={isReplay ? "Unavailable · PPG + IMU model does not estimate this" : "Cuffless PPG-derived estimate"}
        />
      </div>
    </Panel>
  );
}
