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

// Master-prompt 3 §8.8 — HR inference panel. Estimate, reference,
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
  const hasEstimate = availability === "available" && Boolean(prediction);

  return (
    <section aria-labelledby="hr-inference-heading" className="flex flex-col gap-4 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <h2 id="hr-inference-heading" className="text-sm font-semibold text-ink-primary">
        Heart-rate inference
      </h2>

      {isWaitingForConfirmation ? (
        <p role="status" className="rounded-md border border-information/25 bg-information-soft px-3 py-2 text-xs text-information">
          Waiting for a confirmed frame from the selected source.
        </p>
      ) : null}

      <div className="flex items-baseline gap-2 border-b border-jury-border-subtle pb-4">
        {hasEstimate ? (
          <>
            <span className="font-mono text-[38px] font-medium leading-none tabular-nums text-ink-primary">
              {prediction!.value.toFixed(1)}
            </span>
            <span className="text-sm text-ink-muted">bpm</span>
          </>
        ) : (
          <span className="font-mono text-[38px] font-medium leading-none text-ink-disabled">Unavailable</span>
        )}
      </div>

      <dl className="grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Availability</dt>
          <dd className="mt-0.5 text-ink-primary">{predictionAvailabilityLabel(availability)}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Inference status</dt>
          <dd className="mt-0.5 text-ink-primary">{inferenceStatusLabel(inference, isReplay)}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Model input modalities</dt>
          <dd className="mt-0.5 text-ink-primary">
            {prediction ? prediction.provenance.input_channels.join(" + ") : "wrist_bvp + wrist_acc (required, not currently supplying a prediction)"}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Provenance</dt>
          <dd className="mt-0.5 text-ink-primary">
            {prediction
              ? `${prediction.provenance.model_id} · ${prediction.provenance.dataset_name} ${prediction.provenance.subject_id}`
              : "Not applicable — no valid prediction this window"}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Prediction window</dt>
          <dd className="mt-0.5 text-ink-primary">
            {prediction
              ? `${prediction.provenance.window_start_seconds.toFixed(1)}–${(prediction.provenance.window_start_seconds + prediction.provenance.window_duration_seconds).toFixed(1)}s`
              : "Not applicable"}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Reference HR</dt>
          <dd className="mt-0.5 text-ink-secondary">Reference HR unavailable for the current window.</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Current-window difference</dt>
          <dd className="mt-0.5 text-ink-secondary">
            {currentWindowDifference !== null ? `${currentWindowDifference.toFixed(1)} bpm` : "Not computable — reference HR unavailable"}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Active simulated fault</dt>
          <dd className={fault?.active ? "mt-0.5 text-jury-fault" : "mt-0.5 text-ink-secondary"}>{deriveFaultSummaryLabel(fault)}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Fallback status</dt>
          <dd className="mt-0.5 text-ink-secondary">No fallback inference source is implemented.</dd>
        </div>
      </dl>

      <p className="rounded-md border border-information/25 bg-information-soft px-3 py-2 text-[11px] leading-relaxed text-ink-secondary">
        Error metrics are defined only for valid predictions. Prediction availability is reported separately. Applicable
        MAE/RMSE figures are frozen experimental evaluation metrics from the PPG-DaLiA robustness replay, not a live
        measurement — see Experimental Research.
      </p>
    </section>
  );
}
