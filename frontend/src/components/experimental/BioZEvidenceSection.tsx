"use client";

import { DataStateError } from "@/components/ui/DataStateError";
import { titleCase } from "@/lib/format";
import { useResearchStore } from "@/store/researchStore";
import type { Stage3EvidenceEntry } from "@/lib/types";

// Master-prompt §9.3 (corrective pass §3) — Thoracic and leg BioZ/EIS
// evidence. Sourced from the real /research/stage3-evidence entries whose
// family_id is lbnp_thoracic_eis or qde_v2_leg_bioz (see backend/app/
// research/stage3_evidence.py _EXTRACTORS) — every field rendered here is a
// real, typed value from that artifact, never fabricated.
const BIOZ_FAMILY_IDS = ["lbnp_thoracic_eis", "qde_v2_leg_bioz"];

function EvidenceCard({ entry }: { entry: Stage3EvidenceEntry }) {
  return (
    <article className="rounded-md border border-jury-border-subtle bg-surface-2 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-base font-semibold text-ink-primary">{titleCase(entry.family_id)}</h3>
        {entry.classification ? (
          <span className="rounded-[4px] border border-experimental/40 bg-experimental-soft px-2 py-0.5 text-[11px] font-semibold text-experimental">
            {entry.classification}
          </span>
        ) : null}
      </div>
      {entry.summary ? <p className="mt-2 text-sm leading-relaxed text-ink-secondary">{entry.summary}</p> : null}
      <dl className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {entry.primary_comparison_label ? (
          <div>
            <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">{entry.primary_comparison_label}</dt>
            <dd className="mt-0.5 font-mono text-sm text-ink-primary">
              {entry.primary_effect_value !== null ? entry.primary_effect_value.toFixed(3) : "N/A"} {entry.primary_effect_unit ?? ""}
            </dd>
          </div>
        ) : null}
        {entry.secondary_comparison_label ? (
          <div>
            <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">{entry.secondary_comparison_label}</dt>
            <dd className="mt-0.5 font-mono text-sm text-ink-primary">
              {entry.secondary_effect_value !== null ? entry.secondary_effect_value.toFixed(3) : "N/A"} {entry.secondary_effect_unit ?? ""}
            </dd>
          </div>
        ) : null}
        {entry.biological_subject_n !== null ? (
          <div>
            <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Biological subjects</dt>
            <dd className="mt-0.5 text-sm text-ink-primary">{entry.biological_subject_n}</dd>
          </div>
        ) : null}
      </dl>
      {entry.heterogeneity_note ? (
        <p className="mt-3 rounded-md border border-jury-warning/30 bg-jury-warning-soft px-3 py-2 text-[12px] leading-relaxed text-ink-secondary">
          Heterogeneity: {entry.heterogeneity_note}
        </p>
      ) : null}
      {entry.limitation ? (
        <p className="mt-2 text-[12px] leading-relaxed text-ink-muted">Limitation: {entry.limitation}</p>
      ) : null}
      <p className="mt-3 border-t border-jury-border-subtle pt-2 font-mono text-[10px] text-ink-disabled">{entry.artifact_path}</p>
    </article>
  );
}

export function BioZEvidenceSection() {
  const stage3Evidence = useResearchStore((state) => state.stage3Evidence);
  const stage3EvidenceError = useResearchStore((state) => state.stage3EvidenceError);
  const loading = useResearchStore((state) => state.loading);
  const load = useResearchStore((state) => state.load);

  const entries = stage3Evidence?.entries.filter((entry) => BIOZ_FAMILY_IDS.includes(entry.family_id)) ?? [];

  return (
    <section aria-labelledby="bioz-evidence-heading" className="flex flex-col gap-4">
      <div>
        <h2 id="bioz-evidence-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
          Thoracic and leg BioZ/EIS
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
          Real controlled-evaluation results for the two bioimpedance candidates. Only verified fields from the
          canonical Stage-3 evidence artifact are rendered.
        </p>
      </div>

      {loading && !stage3Evidence ? (
        <p className="text-sm text-ink-muted">Loading canonical evidence…</p>
      ) : stage3EvidenceError && entries.length === 0 ? (
        <DataStateError
          title="Stage-3 evidence unavailable"
          source="/research/stage3-evidence"
          cause={stage3EvidenceError}
          onRetry={() => void load()}
        />
      ) : entries.length === 0 ? (
        <p className="text-sm text-ink-muted">No canonical BioZ/EIS result payload is available in the current frontend data source.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {entries.map((entry) => (
            <EvidenceCard key={entry.family_id} entry={entry} />
          ))}
        </div>
      )}
    </section>
  );
}
