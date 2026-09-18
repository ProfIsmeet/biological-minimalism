import { FlaskConical } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import type { Stage3EvidenceEntry, Stage3EvidenceEnvelope } from "@/lib/types";

// Renders the Stage-3 accepted governing science ONLY through the typed
// display projection the backend already resolved via the integrity-verified
// resolver (governing prompt Part IV/VI). This component performs no
// arithmetic, invents no classification, and never distinguishes "positive"
// vs "negative" results visually — a mixed/negative finding (LBNP, QDE,
// PTT) is rendered with the exact same visual weight as a supportive one
// (governing prompt §30: negative results must remain visible).

function formatEffect(value: number | null, unit: string | null): string | null {
  if (value === null) return null;
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(4)}${unit ? ` ${unit}` : ""}`;
}

function NPill({ label, value }: { label: string; value: number | null }) {
  if (value === null) return null;
  return (
    <span className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5 text-[10px] text-slate-400">
      {label}: <span className="font-mono text-slate-200">{value}</span>
    </span>
  );
}

function ExperimentCard({ entry }: { entry: Stage3EvidenceEntry }) {
  const primary = formatEffect(entry.primary_effect_value, entry.primary_effect_unit);
  const secondary = formatEffect(entry.secondary_effect_value, entry.secondary_effect_unit);
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-mono text-[11px] text-slate-300">{entry.family_id}</span>
        {entry.classification ? (
          <span className="rounded-full border border-cyan-400/20 bg-cyan-400/[0.06] px-2 py-0.5 text-[10px] font-semibold text-cyan-300">
            {entry.classification}
          </span>
        ) : (
          <span className="rounded-full border border-slate-500/20 bg-slate-500/[0.06] px-2 py-0.5 text-[10px] text-slate-500">
            classification: unknown
          </span>
        )}
      </div>

      <div className="mt-2 flex flex-wrap gap-1.5">
        <NPill label="biological n" value={entry.biological_subject_n} />
        <NPill label="held-out/reduced n" value={entry.held_out_or_reduced_n} />
        <NPill label="full-cohort target n" value={entry.full_cohort_target_n} />
        <NPill label="seeds" value={entry.optimization_seed_n} />
      </div>

      {entry.primary_comparison_label ? (
        <div className="mt-2 border-t border-white/5 pt-2 text-[11px]">
          <p className="text-slate-500">{entry.primary_comparison_label}</p>
          <p className="font-mono text-[13px] text-slate-100">{primary ?? "unavailable"}</p>
        </div>
      ) : null}

      {entry.secondary_comparison_label ? (
        <div className="mt-1 text-[11px]">
          <p className="text-slate-500">{entry.secondary_comparison_label}</p>
          <p className="font-mono text-[13px] text-slate-100">{secondary ?? "unavailable"}</p>
        </div>
      ) : null}

      {entry.heterogeneity_note ? (
        <p className="mt-2 text-[10px] leading-relaxed text-amber-300/80">{entry.heterogeneity_note}</p>
      ) : null}

      {entry.limitation ? (
        <p className="mt-1 text-[10px] leading-relaxed text-slate-500">{entry.limitation}</p>
      ) : null}

      <p className="mt-2 truncate font-mono text-[9px] text-slate-600" title={entry.artifact_path}>
        {entry.artifact_path}
      </p>
    </div>
  );
}

function ProvenanceRow({ entry }: { entry: Stage3EvidenceEntry }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-white/5 py-1.5 last:border-0">
      <span className="font-mono text-[10px] text-slate-400">{entry.family_id}</span>
      <span className="max-w-[60%] truncate text-[10px] text-slate-500" title={entry.summary ?? undefined}>
        {entry.summary ?? "—"}
      </span>
      <span className="font-mono text-[9px] text-slate-600" title={entry.artifact_path}>
        {entry.artifact_type}
      </span>
    </div>
  );
}

export function Stage3EvidenceView({ evidence }: { evidence: Stage3EvidenceEnvelope }) {
  const experimentEntries = evidence.entries.filter((e) => e.primary_comparison_label !== null);
  const provenanceEntries = evidence.entries.filter((e) => e.primary_comparison_label === null);

  return (
    <Panel
      title="Stage 3 Accepted Governing Science"
      subtitle="Resolved live through the integrity-verified resolver — registry + semantic + hash checks, never a hard-coded path"
      icon={<FlaskConical size={16} />}
      contentClassName="space-y-3"
    >
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {experimentEntries.map((entry) => (
          <ExperimentCard key={entry.family_id} entry={entry} />
        ))}
      </div>

      <div>
        <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          Governance &amp; provenance artifacts
        </p>
        {provenanceEntries.map((entry) => (
          <ProvenanceRow key={entry.family_id} entry={entry} />
        ))}
      </div>

      <p className="text-[10px] text-slate-600">
        pre-closure input snapshot — final_architecture: {evidence.final_architecture_status} · formal_pareto: {evidence.formal_pareto_status} ·
        source: {evidence.source_registry}
      </p>
    </Panel>
  );
}
