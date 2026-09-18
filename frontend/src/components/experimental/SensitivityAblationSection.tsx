"use client";

import { DataStateError } from "@/components/ui/DataStateError";
import { titleCase } from "@/lib/format";
import { useResearchStore } from "@/store/researchStore";
import type { Stage3EvidenceEntry } from "@/lib/types";

// Master-prompt §9.4 (corrective pass §3) — Sensitivity and ablation.
// Sourced from real /research/stage3-evidence entries: capacity-control and
// shuffled-control comparisons are the project's actual ablations; the
// interaction and bounded-diagnostic families are the project's actual
// sensitivity analyses (see backend/app/research/stage3_evidence.py
// _EXTRACTORS). Mixed/negative findings are never hidden — heterogeneity
// and limitation text is rendered verbatim from the artifact.
const SENSITIVITY_ABLATION_FAMILY_IDS = [
  "ppg_dalia_capacity_control",
  "sleep_edf_shuffled_control_c",
  "sleep_edf_interaction",
  "hmc_bounded_diagnostic",
  "ds003838_bounded_diagnostic",
];

function AblationRow({ entry }: { entry: Stage3EvidenceEntry }) {
  return (
    <div className="border-b border-jury-border-subtle py-4 last:border-0">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-ink-primary">{titleCase(entry.family_id)}</h3>
        {entry.classification ? (
          <span className="rounded-[4px] border border-jury-border-strong px-2 py-0.5 text-[11px] font-semibold text-ink-secondary">
            {entry.classification}
          </span>
        ) : null}
      </div>
      {entry.summary ? <p className="mt-1.5 text-sm leading-relaxed text-ink-secondary">{entry.summary}</p> : null}
      {entry.primary_comparison_label ? (
        <p className="mt-2 text-[12px] leading-relaxed text-ink-muted">
          <span className="font-medium text-ink-secondary">{entry.primary_comparison_label}:</span>{" "}
          <span className="font-mono text-ink-primary">
            {entry.primary_effect_value !== null ? entry.primary_effect_value.toFixed(4) : "N/A"} {entry.primary_effect_unit ?? ""}
          </span>
        </p>
      ) : null}
      {entry.heterogeneity_note ? (
        <p className="mt-1 text-[12px] leading-relaxed text-jury-warning">Mixed/heterogeneous: {entry.heterogeneity_note}</p>
      ) : null}
      {entry.limitation ? <p className="mt-1 text-[12px] leading-relaxed text-ink-muted">{entry.limitation}</p> : null}
      <p className="mt-2 font-mono text-[10px] text-ink-disabled">{entry.artifact_path}</p>
    </div>
  );
}

export function SensitivityAblationSection() {
  const stage3Evidence = useResearchStore((state) => state.stage3Evidence);
  const stage3EvidenceError = useResearchStore((state) => state.stage3EvidenceError);
  const loading = useResearchStore((state) => state.loading);
  const load = useResearchStore((state) => state.load);

  const entries = stage3Evidence?.entries.filter((entry) => SENSITIVITY_ABLATION_FAMILY_IDS.includes(entry.family_id)) ?? [];

  return (
    <section aria-labelledby="sensitivity-ablation-heading" className="flex flex-col gap-4">
      <div>
        <h2 id="sensitivity-ablation-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
          Sensitivity and ablation
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
          Capacity-controlled and shuffled-control ablations, plus bounded-diagnostic sensitivity checks. Negative and
          mixed results are shown, not hidden.
        </p>
      </div>

      {loading && !stage3Evidence ? (
        <p className="text-sm text-ink-muted">Loading canonical evidence…</p>
      ) : stage3EvidenceError && entries.length === 0 ? (
        <DataStateError
          title="Sensitivity/ablation evidence unavailable"
          source="/research/stage3-evidence"
          cause={stage3EvidenceError}
          onRetry={() => void load()}
        />
      ) : entries.length === 0 ? (
        <p className="text-sm text-ink-muted">No canonical sensitivity/ablation result payload is available in the current frontend data source.</p>
      ) : (
        <div className="rounded-[10px] border border-jury-border-subtle bg-surface-1 px-5">
          {entries.map((entry) => (
            <AblationRow key={entry.family_id} entry={entry} />
          ))}
        </div>
      )}
    </section>
  );
}
