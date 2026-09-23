"use client";

import { ChevronRight } from "lucide-react";

import { useMonitoringSession } from "@/components/monitoring/MonitoringSessionContext";
import { deriveSourceLabel } from "@/lib/monitoring/sourceState";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

interface ChainStep {
  label: string;
  value: string;
}

/**
 * Prompt 3C §16 — Operational Provenance Chain: Source type → Dataset →
 * Subject → Input channels → Model → Current output, built ONLY from real
 * confirmed/provenance fields already used by ScopeProvenanceFooter (never a
 * second, divergent source of truth). A missing field fails closed to an
 * explicit "—" rather than being fabricated or silently omitted from the
 * chain, and no validation/accuracy claim is attached to any step.
 */
export function OperationalProvenanceChain() {
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  const { snapshot: latest } = useConfirmedSnapshot();
  const isReplay = useDatasetReplayMode();
  const { status } = useMonitoringSession();

  const sourceLabel = deriveSourceLabel({ connectionStatus, isReplay });
  const datasetName = latest?.source.dataset_name ?? status?.dataset_name ?? null;
  const subjectId = latest?.source.subject_id ?? status?.subject_id ?? null;
  const availableChannels = latest?.source.available_channels ?? status?.channels.map((channel) => channel.name) ?? [];
  const prediction = isReplay ? (latest?.heart_rate_prediction ?? null) : null;

  const steps: ChainStep[] = [
    { label: "Source type", value: sourceLabel },
    { label: "Dataset", value: isReplay ? (datasetName ?? "—") : "Not applicable" },
    { label: "Subject", value: isReplay ? (subjectId ?? "—") : "Not applicable" },
    { label: "Input channels", value: availableChannels.length ? availableChannels.join(" + ") : "—" },
    { label: "Model", value: prediction ? prediction.provenance.model_id : "—" },
    { label: "Current output", value: prediction ? `${prediction.value.toFixed(1)} bpm estimate` : "HR estimate unavailable" },
  ];

  return (
    <section aria-labelledby="provenance-chain-heading" className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <h2 id="provenance-chain-heading" className="text-sm font-semibold text-ink-primary">
        Operational provenance chain
      </h2>
      <ol className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-stretch sm:gap-0">
        {steps.map((step, i) => (
          <li key={step.label} className="flex items-center gap-2 sm:flex-1">
            <div className="flex min-w-0 flex-1 flex-col gap-0.5 rounded-[6px] border border-jury-border-subtle bg-surface-2 px-2.5 py-2 sm:mr-2">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-ink-muted">{step.label}</span>
              <span className="truncate text-xs font-medium text-ink-primary" title={step.value}>{step.value}</span>
            </div>
            {i < steps.length - 1 ? (
              <ChevronRight size={14} aria-hidden="true" className="hidden shrink-0 text-ink-disabled sm:block" />
            ) : null}
          </li>
        ))}
      </ol>
    </section>
  );
}
