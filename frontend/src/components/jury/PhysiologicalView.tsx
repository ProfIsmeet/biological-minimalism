"use client";

import { FinalSensorLedger } from "@/components/jury/FinalSensorLedger";
import { deriveFaultSummaryLabel } from "@/lib/monitoring/inferenceState";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";
import type { ModelInferenceStatus } from "@/lib/types";

const INFERENCE_MESSAGE: Record<ModelInferenceStatus, string> = {
  warming_up: "Model is warming up.",
  available: "Model available.",
  input_unavailable: "Required PPG + IMU input window is unavailable.",
  model_unavailable: "HR model is unavailable.",
  error: "Inference error.",
};

// Master-prompt §7.5 — physiological view: one HR inference panel + the
// final-sensor ledger. Reuses the same replay/synthetic split already
// proven correct in PrimaryVitalsPanel (heart_rate_prediction only exists
// in replay mode; synthetic mode has no AI-estimated HR, only the mock
// engine's vitals.heart_rate_bpm) — never conflates the two, never shows a
// default/zero HR when missing.
function HrInferencePanel() {
  const isReplay = useDatasetReplayMode();
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  const { snapshot: latest, isWaitingForConfirmation } = useConfirmedSnapshot();
  const prediction = isReplay ? latest?.heart_rate_prediction : null;
  const inference = isReplay ? latest?.heart_rate_inference : null;
  const fault = isReplay ? (prediction?.provenance.fault_injection ?? latest?.fault_injection) : null;
  const syntheticHr = !isReplay ? latest?.vitals?.heart_rate_bpm : null;

  if (connectionStatus !== "open") {
    return (
      <div className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-5">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Heart rate inference</span>
        <p className="text-lg font-semibold text-ink-primary">HR unavailable</p>
        <p className="text-xs leading-relaxed text-ink-secondary">
          {connectionStatus === "connecting" ? "Connecting to the data source." : "The data source is disconnected."}
        </p>
      </div>
    );
  }

  if (isWaitingForConfirmation) {
    return (
      <div className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-5">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Heart rate inference</span>
        <p className="text-lg font-semibold text-ink-primary">Waiting for confirmation</p>
        <p className="text-xs leading-relaxed text-ink-secondary">
          Waiting for a confirmed frame from the selected source.
        </p>
      </div>
    );
  }

  if (isReplay) {
    if (prediction) {
      const windowEnd = prediction.provenance.window_start_seconds + prediction.provenance.window_duration_seconds;
      // Never derived from fault-absence alone: also requires the inference
      // pipeline itself to report "available".
      const nominal = !fault?.active && inference?.status === "available";
      return (
        <div className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-5">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Heart rate inference</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-semibold tabular-nums text-ink-primary">{prediction.value.toFixed(1)}</span>
            <span className="text-sm text-ink-muted">bpm</span>
            <span
              className={
                nominal
                  ? "ml-2 rounded-[4px] border border-jury-success/40 bg-jury-success-soft px-1.5 py-0.5 text-[11px] font-semibold text-jury-success"
                  : "ml-2 rounded-[4px] border border-jury-warning/40 bg-jury-warning-soft px-1.5 py-0.5 text-[11px] font-semibold text-jury-warning"
              }
            >
              {nominal ? "Nominal" : "Degraded"}
            </span>
          </div>
          <p className="text-xs leading-relaxed text-ink-secondary">
            Source: AI-estimated · PPG + IMU model · {prediction.provenance.dataset_name} {prediction.provenance.subject_id} ·
            window {prediction.provenance.window_start_seconds.toFixed(1)}–{windowEnd.toFixed(1)} s
          </p>
          {fault?.active ? (
            <p className="text-xs leading-relaxed text-jury-warning">
              {deriveFaultSummaryLabel(fault)}
            </p>
          ) : null}
        </div>
      );
    }
    return (
      <div className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-5">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Heart rate inference</span>
        <p className="text-lg font-semibold text-ink-primary">HR unavailable</p>
        <p className="text-xs leading-relaxed text-ink-secondary">
          {inference ? INFERENCE_MESSAGE[inference.status] : "Waiting for a valid recorded-replay PPG + IMU window."}
        </p>
      </div>
    );
  }

  if (syntheticHr == null) {
    return (
      <div className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-5">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Heart rate inference</span>
        <p className="text-lg font-semibold text-ink-primary">HR unavailable</p>
        <p className="text-xs leading-relaxed text-ink-secondary">The synthetic demo source has not provided a value yet.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-5">
      <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Heart rate inference</span>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-semibold tabular-nums text-ink-primary">{syntheticHr.toFixed(0)}</span>
        <span className="text-sm text-ink-muted">bpm</span>
      </div>
      <p className="text-xs leading-relaxed text-ink-secondary">
        Source: synthetic demo value (mock data engine) — not AI-estimated. Fault-aware AI inference activates during
        recorded replay.
      </p>
    </div>
  );
}

export function PhysiologicalView() {
  return (
    <section aria-labelledby="physiological-view-heading" className="flex flex-col gap-4">
      <div>
        <h2 id="physiological-view-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
          Physiological view
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
          A source-aware view of the final sensing architecture. Values reflect the active dashboard source and are
          not scientific outcome metrics.
        </p>
      </div>
      <HrInferencePanel />
      <FinalSensorLedger />
    </section>
  );
}
