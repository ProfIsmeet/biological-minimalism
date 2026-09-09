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
  COMPLETE: "border-emerald-400/25 bg-emerald-400/[0.08] text-emerald-300",
  BOUNDED_DIAGNOSTIC: "border-amber-400/25 bg-amber-400/[0.08] text-amber-300",
  BLOCKED_BY_DATA_ACCESS: "border-rose-400/25 bg-rose-400/[0.07] text-rose-300",
  PENDING: "border-slate-500/25 bg-slate-500/[0.08] text-slate-300",
  HISTORICAL: "border-slate-500/20 bg-slate-500/[0.05] text-slate-400",
  SUPERSEDED: "border-rose-400/20 bg-rose-400/[0.05] text-rose-400/90",
};

const REPLICATION_CLASS_CLASS: Record<ReplicationClass, string> = {
  EXTERNAL_REPLICATION: "border-cyan-400/25 bg-cyan-400/[0.08] text-cyan-300",
  SAME_DATASET_HOLDOUT: "border-amber-400/20 bg-amber-400/[0.06] text-amber-200",
  SINGLE_RUN: "border-slate-500/20 bg-slate-500/[0.06] text-slate-400",
  NOT_APPLICABLE: "border-slate-500/15 bg-slate-500/[0.04] text-slate-500",
};

function StatusPill({ label, className }: { label: string; className: string }) {
  return (
    <span className={clsx("rounded-full border px-2 py-0.5 text-[10px] font-semibold", className)}>{label}</span>
  );
}

// A strongly-positive aggregate benefit must never be shown without this —
// otherwise a single dominant subject/class could drive the whole headline
// number while the dashboard reads as uniform support (Phase-4 hostile-
// review finding, governing prompt §52).
function SensitivitySection({ label, block }: { label: string; block: FutureScienceSensitivityBlock }) {
  if (block.status !== "available" || block.entries.length === 0) {
    return (
      <p className="mt-2 text-[11px] text-slate-500">
        {label}: {block.status === "pending" ? "pending" : "unavailable"}
        {block.note ? ` — ${block.note}` : ""}
      </p>
    );
  }
  return (
    <details className="mt-2 rounded-lg border border-white/5 bg-white/[0.015]">
      <summary className="cursor-pointer px-3 py-2 text-[11px] font-semibold text-slate-400">
        {label} ({block.entries.length}){block.dominant_key ? ` — dominant: ${block.dominant_key}` : ""}
      </summary>
      <div className="space-y-1 border-t border-white/5 px-3 py-2">
        {block.entries.map((entry) => (
          <p key={entry.key} className="flex justify-between gap-3 font-mono text-[10px] text-slate-400">
            <span>{entry.key}</span>
            <span>{entry.value ?? "—"}{entry.note ? ` (${entry.note})` : ""}</span>
          </p>
        ))}
        {block.note ? <p className="pt-1 text-[10px] text-amber-300/80">{block.note}</p> : null}
      </div>
    </details>
  );
}

function ProjectionCard({ projection }: { projection: ManifestEntryDisplayProjection }) {
  return (
    <article className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-100">{projection.experiment_id}</h3>
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
      <p className="mt-2 font-mono text-[12px] text-slate-300">{projection.benefit_display}</p>
      <SensitivitySection label="Subject sensitivity" block={projection.subject_sensitivity} />
      {projection.class_sensitivity ? (
        <SensitivitySection label="Class sensitivity" block={projection.class_sensitivity} />
      ) : null}
      {projection.limitations.length > 0 ? (
        <ul className="mt-2 space-y-1 text-[11px] leading-relaxed text-slate-500">
          {projection.limitations.map((item) => (
            <li key={item}>• {item}</li>
          ))}
        </ul>
      ) : null}
      <p className="mt-2 break-all font-mono text-[10px] text-slate-600">{projection.provenance_source}</p>
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
        <p className="flex items-start gap-2 text-[12px] leading-relaxed text-slate-400">
          <Clock size={14} className="mt-0.5 shrink-0 text-slate-500" />
          Pending — Ismet&apos;s science-completion sprint is still in progress. No future-science manifest has
          been produced yet. This is an expected, honest state, not an error.
        </p>
      ) : null}

      {envelope.status === "INGESTION_FAILED" ? (
        <p role="alert" className="flex items-start gap-2 rounded-lg border border-rose-400/20 bg-rose-400/[0.06] px-3 py-2.5 text-[12px] leading-relaxed text-rose-200">
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
