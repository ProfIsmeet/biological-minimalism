"use client";

import Link from "next/link";

import { ERROR_METRIC_QUALIFIER } from "@/lib/architecture";
import { deriveFaultAwareInferenceView } from "@/lib/monitoring/faultAwareInferenceView";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { deriveConnectionLabel, deriveSourceLabel } from "@/lib/sourceLabel";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

// Master-prompt corrective pass §7 — fault-aware HR inference detail.
// Source scope, connection state, prediction availability, and fault state
// are kept as four independently-derived fields; none is inferred from
// another. "Current valid prediction" (not "Last valid prediction") because
// this component only reads the latest snapshot — it does not search
// mission history for a prior valid window, so a "last" claim would assert
// persistence that isn't implemented.
//
// Prompt-2C §4/§7 — every current-frame-dependent field below is produced by
// the pure, independently-tested deriveFaultAwareInferenceView() helper
// (lib/monitoring/faultAwareInferenceView.ts) instead of being derived
// inline field-by-field, so a confirmed-source mismatch
// (isWaitingForConfirmation) provably overrides every field at once rather
// than relying on each field remembering to check it individually.
export function FaultAwareInference() {
  const isReplay = useDatasetReplayMode();
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  const { snapshot: latest, isWaitingForConfirmation } = useConfirmedSnapshot();
  const prediction = isReplay ? latest?.heart_rate_prediction : null;
  const inference = isReplay ? latest?.heart_rate_inference : null;
  const fault = isReplay ? (prediction?.provenance.fault_injection ?? latest?.fault_injection) : null;

  const connected = connectionStatus === "open";
  const sourceLabel = deriveSourceLabel({ connectionStatus, isReplay });
  const connectionLabel = deriveConnectionLabel(connectionStatus);

  const {
    status,
    currentInferenceSource,
    primaryVsFallback,
    activeFaultCondition,
    predictionAvailability,
    currentValidPrediction,
    inferenceModelStatus,
  } = deriveFaultAwareInferenceView({ connected, isReplay, isWaitingForConfirmation, prediction, inference, fault });

  return (
    <section aria-labelledby="fault-aware-heading" className="flex flex-col gap-4 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="fault-aware-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
            Fault-aware HR inference
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
            Inference quality is shown together with sensor availability so that missing or degraded input is not
            hidden behind a single confidence number.
          </p>
        </div>
        <span
          className={
            status === "Nominal"
              ? "rounded-[4px] border border-jury-success/40 bg-jury-success-soft px-2 py-1 text-[11px] font-semibold text-jury-success"
              : status === "Degraded"
                ? "rounded-[4px] border border-jury-warning/40 bg-jury-warning-soft px-2 py-1 text-[11px] font-semibold text-jury-warning"
                : "rounded-[4px] border border-ink-disabled/40 bg-surface-2 px-2 py-1 text-[11px] font-semibold text-ink-disabled"
          }
        >
          {status}
        </span>
      </div>

      <dl className="grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Source scope</dt>
          <dd className="mt-0.5 text-ink-primary">{sourceLabel}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Connection state</dt>
          <dd className="mt-0.5 text-ink-primary">{connectionLabel}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Current inference source</dt>
          <dd className="mt-0.5 text-ink-primary">{currentInferenceSource}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Primary vs. fallback</dt>
          <dd className="mt-0.5 text-ink-primary">{primaryVsFallback}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Active fault condition</dt>
          <dd className="mt-0.5 text-ink-primary">{activeFaultCondition}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Prediction availability</dt>
          <dd className="mt-0.5 text-ink-primary">{predictionAvailability}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Current valid prediction</dt>
          <dd className="mt-0.5 text-ink-primary">{currentValidPrediction}</dd>
        </div>
        <div>
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Inference model status</dt>
          <dd className="mt-0.5 text-ink-primary">{inferenceModelStatus}</dd>
        </div>
      </dl>

      <div className="rounded-md border border-information/30 bg-information-soft px-4 py-3">
        <p className="text-xs leading-relaxed text-ink-secondary">
          Applicable error metric: MAE/RMSE from the PPG-DaLiA robustness replay — a frozen experimental evaluation
          artifact, not a live measurement.{" "}
          <Link href="/research/experimental" className="font-medium text-information underline underline-offset-2">
            See Experimental Research
          </Link>
          .
        </p>
        <p className="mt-2 text-xs leading-relaxed text-ink-muted">{ERROR_METRIC_QUALIFIER}</p>
      </div>
    </section>
  );
}
