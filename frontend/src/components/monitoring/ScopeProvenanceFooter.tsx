"use client";

import Link from "next/link";

import { deriveIdentityContextDisplay } from "@/lib/monitoring/liveMonitoringPresentation";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";
import { telemetryAvailabilityLabel } from "@/lib/monitoring/telemetryAvailability";

// Master-prompt §8.8 — scope and provenance footer. Every field is read from
// the same canonical state the rest of the page uses; the three required
// notes are rendered verbatim.
//
// Corrective package 01 F-01: current provenance comes from the shared gate;
// retained REST identity is shown only with explicit configuration/history
// wording and never as current telemetry.
export function ScopeProvenanceFooter() {
  const view = useOperationalViewModel();
  const retainedContext = view.telemetryAvailability !== "active";
  const datasetDisplay = deriveIdentityContextDisplay({ kind: "Dataset", telemetry: view.telemetryAvailability, currentValue: view.datasetName, retainedValue: view.retainedDatasetName });
  const subjectDisplay = deriveIdentityContextDisplay({ kind: "Subject", telemetry: view.telemetryAvailability, currentValue: view.subjectId, retainedValue: view.retainedSubjectId });
  const datasetValue = datasetDisplay.value;
  const subjectValue = subjectDisplay.value;
  const availableChannels = view.modalities
    .filter((entry) => entry.nodeState === "confirmed" || entry.nodeState === "warmup")
    .map((entry) => entry.observation.channelName)
    .filter((channel): channel is string => channel !== null);

  return (
    <footer className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4 text-xs text-ink-secondary">
      <dl className="grid grid-cols-1 gap-x-6 gap-y-2 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-ink-muted">{retainedContext ? "Source context" : "Active source"}</dt>
          <dd className="mt-0.5 text-ink-secondary">
            {retainedContext
              ? `${view.isReplay ? "RECORDED REPLAY" : "SYNTHETIC DEMO"} — retained configuration context, not current telemetry`
              : view.sourceLabel}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-ink-muted">Dataset</dt>
          <dd className="mt-0.5 text-ink-secondary">{view.isReplay ? datasetValue : "Not applicable"}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-ink-muted">Subject</dt>
          <dd className="mt-0.5 text-ink-secondary">{view.isReplay ? subjectValue : "Not applicable"}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-ink-muted">Model identity</dt>
          <dd className="mt-0.5 break-all text-ink-secondary">{view.prediction ? view.prediction.provenance.model_id : "Not available"}</dd>
        </div>
        <div className="sm:col-span-2 lg:col-span-2">
          <dt className="text-[10px] uppercase tracking-wide text-ink-muted">Channel list</dt>
          <dd className="mt-0.5 text-ink-secondary">
            {view.telemetryAvailability === "active"
              ? availableChannels.length ? availableChannels.join(", ") : "None reported by current source"
              : telemetryAvailabilityLabel(view.telemetryAvailability)}
          </dd>
        </div>
        <div className="sm:col-span-2 lg:col-span-2">
          <dt className="text-[10px] uppercase tracking-wide text-ink-muted">Current limitation</dt>
          <dd className="mt-0.5 text-ink-secondary">
            No reference/ground-truth HR channel exists in the current runtime contract; accuracy metrics are only
            available as frozen, offline evaluation artifacts.
          </dd>
        </div>
      </dl>

      <div className="flex flex-col gap-1 border-t border-jury-border-subtle pt-3 text-ink-muted">
        <p>Recorded replay is not live astronaut monitoring.</p>
        <p>The S14 replay, when selected, is a single-participant stress test and not population validation.</p>
        <p>Dashboard values are not the source of scientific Results.</p>
      </div>

      <Link href="/research/experimental" className="w-fit text-information underline underline-offset-2">
        See Experimental Research
      </Link>
    </footer>
  );
}
