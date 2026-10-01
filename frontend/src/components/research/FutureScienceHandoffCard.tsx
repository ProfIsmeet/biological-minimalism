import clsx from "clsx";
import { Clock, FlaskConical, ShieldAlert } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import type {
  ExperimentCompletionState,
  FutureScienceManifestEnvelope,
  FutureScienceSensitivityBlock,
  ManifestEntryDisplayProjection,
  ReplicationClass,
} from "@/lib/types";

// Renders ONLY `display_projections` — never `envelope.manifest?.entries`
// directly. The backend (`app.research.future_science_ingestion.project_for_display`)
// has already applied the promotion gate and state-separation guards to every
// projection; reading only this field means this component structurally
// cannot render a fabricated headline number for a non-COMPLETE entry, and
// cannot blur HISTORICAL into SUPERSEDED or infer a replication class the
// manifest did not declare (Phase-3 consumer-guard requirement).

const COMPLETION_STATE_CLASS: Record<ExperimentCompletionState, string> = {
  COMPLETE: "border-jury-success/25 bg-jury-success/[0.08] text-jury-success",
  BOUNDED_DIAGNOSTIC: "border-jury-warning/25 bg-jury-warning/[0.08] text-jury-warning",
  BLOCKED_BY_DATA_ACCESS: "border-jury-fault/25 bg-jury-fault/[0.07] text-jury-fault",
  PENDING: "border-jury-border-subtle bg-ink-muted/[0.08] text-ink-secondary",
  HISTORICAL: "border-jury-border-subtle bg-ink-muted/[0.05] text-ink-secondary",
  SUPERSEDED: "border-jury-fault/20 bg-jury-fault/[0.05] text-jury-fault/90",
};

const REPLICATION_CLASS_CLASS: Record<ReplicationClass, string> = {
  EXTERNAL_REPLICATION: "border-final-accent/25 bg-final-accent/[0.08] text-final-accent",
  SAME_DATASET_HOLDOUT: "border-jury-warning/20 bg-jury-warning/[0.06] text-jury-warning",
  SINGLE_RUN: "border-jury-border-subtle bg-ink-muted/[0.06] text-ink-secondary",
  NOT_APPLICABLE: "border-jury-border-subtle bg-ink-muted/[0.04] text-ink-muted",
};

function StatusPill({ label, className }: { label: string; className: string }) {
  return (
    <span className={clsx("rounded-full border px-2 py-0.5 text-xs font-semibold", className)}>{label}</span>
  );
}

// A strongly-positive aggregate benefit must never be shown without this —
// otherwise a single dominant subject/class could drive the whole headline
// number while the dashboard reads as uniform support (Phase-4 hostile-
// review finding, governing prompt §52).
function SensitivitySection({ label, block }: { label: string; block: FutureScienceSensitivityBlock }) {
  if (block.status !== "available" || block.entries.length === 0) {
    return (
      <p className="mt-2 text-xs text-ink-muted">
        {label}: {block.status === "pending" ? "pending" : "unavailable"}
        {block.note ? ` — ${block.note}` : ""}
      </p>
    );
  }
  return (
    <details className="mt-2 rounded-lg border border-jury-border-subtle bg-surface-2">
      <summary className="cursor-pointer px-3 py-2 text-xs font-semibold text-ink-secondary">
        {label} ({block.entries.length}){block.dominant_key ? ` — dominant: ${block.dominant_key}` : ""}
      </summary>
      <div className="space-y-1 border-t border-jury-border-subtle px-3 py-2">
        {block.entries.map((entry) => (
          <p key={entry.key} className="flex justify-between gap-3 font-mono text-xs text-ink-secondary">
            <span>{entry.key}</span>
            <span>{entry.value ?? "—"}{entry.note ? ` (${entry.note})` : ""}</span>
          </p>
        ))}
        {block.note ? <p className="pt-1 text-xs text-jury-warning/80">{block.note}</p> : null}
      </div>
    </details>
  );
}

function ProjectionCard({ projection }: { projection: ManifestEntryDisplayProjection }) {
  return (
    <article className="rounded-xl border border-jury-border-subtle bg-surface-2 p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-ink-primary">{projection.experiment_id}</h3>
        <div className="flex flex-wrap items-center gap-1.5">
          <StatusPill
            label={projection.completion_state_label}
            className={COMPLETION_STATE_CLASS[projection.completion_state]}
          />
          {projection.replication_class !== "NOT_APPLICABLE" ? (
            <StatusPill
              label={projection.replication_class_label}
              className={REPLICATION_CLASS_CLASS[projection.replication_class]}
            />
          ) : null}
        </div>
      </div>
      <p className="mt-2 font-mono text-[12px] text-ink-secondary">{projection.benefit_display}</p>
      {/* Two separate, semantically distinct lines — never merged into one
          ambiguous "n", and training seeds are never implied to be
          biological replication (Phase-4 close-out). */}
      <p className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-ink-muted">
        <span>{projection.biological_subject_n_display}</span>
        <span>{projection.optimization_seed_n_display}</span>
      </p>
      <SensitivitySection label="Subject sensitivity" block={projection.subject_sensitivity} />
      {projection.class_sensitivity ? (
        <SensitivitySection label="Class sensitivity" block={projection.class_sensitivity} />
      ) : null}
      {projection.limitations.length > 0 ? (
        <ul className="mt-2 space-y-1 text-xs leading-relaxed text-ink-muted">
          {projection.limitations.map((item) => (
            <li key={item}>• {item}</li>
          ))}
        </ul>
      ) : null}
      <p className="mt-2 break-all font-mono text-xs text-ink-muted">{projection.provenance_source}</p>
    </article>
  );
}

export function FutureScienceHandoffCard({ envelope }: { envelope: FutureScienceManifestEnvelope }) {
  return (
    <Panel
      title="Stage 2-4 Science Handoff"
      subtitle="Ismet's in-progress science-completion sprint — ingested only when frozen and validated"
      icon={<FlaskConical size={16} />}
      contentClassName="space-y-3"
    >
      {envelope.status === "PENDING_SCIENCE_HANDOFF" ? (
        <p className="flex items-start gap-2 text-[12px] leading-relaxed text-ink-secondary">
          <Clock size={14} className="mt-0.5 shrink-0 text-ink-muted" />
          Pending — Ismet&apos;s science-completion sprint is still in progress. No future-science manifest has
          been produced yet. This is an expected, honest state, not an error.
        </p>
      ) : null}

      {envelope.status === "INGESTION_FAILED" ? (
        <p role="alert" className="flex items-start gap-2 rounded-lg border border-jury-fault/20 bg-jury-fault/[0.06] px-3 py-2.5 text-[12px] leading-relaxed text-jury-fault">
          <ShieldAlert size={14} className="mt-0.5 shrink-0" />
          Ingestion failed ({envelope.error_code ?? "UNKNOWN"}): {envelope.error ?? "no further detail."} No
          fallback to any prior or cached result was used.
        </p>
      ) : null}

      {envelope.status === "INGESTED" ? (
        <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
          {envelope.display_projections.map((projection) => (
            <ProjectionCard key={projection.experiment_id} projection={projection} />
          ))}
        </div>
      ) : null}
    </Panel>
  );
}
