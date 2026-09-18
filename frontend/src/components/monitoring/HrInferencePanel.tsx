"use client";

import {
  computeCurrentWindowAbsoluteDifference,
  deriveFaultSummaryLabel,
  derivePredictionAvailability,
  inferenceStatusLabel,
  predictionAvailabilityLabel,
} from "@/lib/monitoring/inferenceState";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

// Master-prompt §8.4/§8.5 — HR inference panel. Estimate, reference,
// current-window difference, availability, and error metrics are five
// distinct concepts, never merged into one confidence number. There is no
// reference/ground-truth HR channel in the current backend contract (see
// backend/app/schemas/telemetry.py), so `referenceBpm` is always null and
// this panel always honestly reports it as unavailable rather than
// fabricating a comparison.
//
// Prompt-2 corrective pass §2: `latest` is read only through
// `useConfirmedSnapshot()`, so a late frame from a source the user has
// switched away from can never repopulate the estimate, inference status,
// or fault fields below.
export function HrInferencePanel() {
  const isReplay = useDatasetReplayMode();
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  const { snapshot: latest, isWaitingForConfirmation } = useConfirmedSnapshot();
  const connected = connectionStatus === "open";
  const prediction = isReplay ? latest?.heart_rate_prediction ?? null : null;
  const inference = isReplay ? latest?.heart_rate_inference ?? null : null;
  const fault = isReplay ? (prediction?.provenance.fault_injection ?? latest?.fault_injection ?? null) : null;

  const availability = derivePredictionAvailability({ connected, isReplay, prediction });
  const referenceBpm: number | null = null; // No reference channel exists in this runtime contract — see note above.
  const currentWindowDifference = computeCurrentWindowAbsoluteDifference(prediction?.value ?? null, referenceBpm);

  return (
    <section aria-labelledby="hr-inference-heading" className="flex flex-col gap-4 rounded-lg border border-white/10 bg-white/[0.02] p-4">
      <h2 id="hr-inference-heading" className="text-sm font-semibold text-slate-200">
        Heart-rate inference
      </h2>

      {isWaitingForConfirmation ? (
        <p role="status" className="rounded-md border border-cyan-400/20 bg-cyan-400/5 px-3 py-2 text-xs text-cyan-200">
          Waiting for a confirmed frame from the selected source.
        </p>
      ) : null}

      <dl className="grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Current HR estimate</dt>
          <dd className="mt-0.5 text-slate-200">
            {availability === "available" && prediction ? `${prediction.value.toFixed(1)} bpm` : "Unavailable"}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Reference HR</dt>
          <dd className="mt-0.5 text-slate-200">Reference HR unavailable for the current window.</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Current-window absolute difference</dt>
          <dd className="mt-0.5 text-slate-200">
            {currentWindowDifference !== null ? `${currentWindowDifference.toFixed(1)} bpm` : "Not computable — reference HR unavailable"}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Prediction availability</dt>
          <dd className="mt-0.5 text-slate-200">{predictionAvailabilityLabel(availability)}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Inference status</dt>
          <dd className="mt-0.5 text-slate-200">{inferenceStatusLabel(inference, isReplay)}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Model input modalities</dt>
          <dd className="mt-0.5 text-slate-200">
            {prediction ? prediction.provenance.input_channels.join(" + ") : "wrist_bvp + wrist_acc (required, not currently supplying a prediction)"}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Model / dataset provenance</dt>
          <dd className="mt-0.5 text-slate-200">
            {prediction
              ? `${prediction.provenance.model_id} · ${prediction.provenance.dataset_name} ${prediction.provenance.subject_id}`
              : "Not applicable — no valid prediction this window"}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Prediction window</dt>
          <dd className="mt-0.5 text-slate-200">
            {prediction
              ? `${prediction.provenance.window_start_seconds.toFixed(1)}–${(prediction.provenance.window_start_seconds + prediction.provenance.window_duration_seconds).toFixed(1)}s`
              : "Not applicable"}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Active simulated fault</dt>
          <dd className="mt-0.5 text-slate-200">{deriveFaultSummaryLabel(fault)}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Fallback status</dt>
          <dd className="mt-0.5 text-slate-200">No fallback inference source is implemented.</dd>
        </div>
      </dl>

      <p className="rounded-md border border-cyan-400/15 bg-cyan-400/[0.04] px-3 py-2 text-[11px] leading-relaxed text-slate-400">
        Error metrics are defined only for valid predictions. Prediction availability is reported separately. Applicable
        MAE/RMSE figures are frozen experimental evaluation metrics from the PPG-DaLiA robustness replay, not a live
        measurement — see Experimental Research.
      </p>
    </section>
  );
}
