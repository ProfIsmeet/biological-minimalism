"use client";

import { DataStateError } from "@/components/ui/DataStateError";
import { CANDIDATE_DISPOSITION_DISPLAY } from "@/lib/architecture";
import { useResearchStore } from "@/store/researchStore";

// Master-prompt §9.5 (corrective pass §3) — why candidates were not carried
// forward. Sequence: observed evidence → boundary/limitation → final
// disposition, using only results/final_wearable_architecture.json's own
// exclusion_rationale text verbatim. This interface does not assert a
// causal integration-burden explanation beyond what each entry's `reason`
// already states, per the required fallback sentence below.
//
// Prompt-2 fix (master prompt §7.1): this used to call
// api.getFinalWearableArchitecture() independently, duplicating the fetch
// ResearchDataLoader already triggers once for the whole route. It now reads
// the same store slice as every other experimental-route section.
export function CandidateSelectionRationale() {
  const architecture = useResearchStore((store) => store.finalWearableArchitecture);
  const architectureError = useResearchStore((store) => store.finalWearableArchitectureError);
  const loading = useResearchStore((store) => store.loading);
  const load = useResearchStore((store) => store.load);

  const state: "loading" | "available" | "empty" | "error" = loading && !architecture
    ? "loading"
    : architectureError && !architecture
      ? "error"
      : !architecture || Object.keys(architecture.exclusion_rationale).length === 0
        ? "empty"
        : "available";
  const errorMessage = architectureError;

  const entries = architecture ? Object.entries(architecture.exclusion_rationale) : [];

  return (
    <section aria-labelledby="selection-rationale-heading" className="flex flex-col gap-4">
      <div>
        <h2 id="selection-rationale-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
          Why they were not carried forward
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
          The final disposition is recorded, but this interface does not assert a stronger causal explanation than the
          available evidence supports.
        </p>
      </div>

      {state === "loading" ? (
        <p className="text-sm text-ink-muted">Loading canonical rationale…</p>
      ) : state === "error" ? (
        <DataStateError
          title="Selection rationale unavailable"
          source="results/final_wearable_architecture.json"
          cause={errorMessage ?? "The canonical architecture artifact could not be loaded."}
          onRetry={() => void load()}
        />
      ) : state === "empty" ? (
        <p className="text-sm text-ink-muted">Outcome not available in the current canonical source.</p>
      ) : (
        <div className="flex flex-col gap-4">
          {entries.map(([key, entry]) => (
            <article key={key} className="rounded-[10px] border border-jury-border-subtle bg-surface-1 p-5">
              <h3 className="text-base font-semibold text-ink-primary">
                {CANDIDATE_DISPOSITION_DISPLAY[key]?.label ?? key.replace(/_/g, " ")}
              </h3>
              <ol className="mt-3 flex flex-col gap-3 border-l border-jury-border-strong pl-4 text-sm">
                <li>
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">1. Observed evidence</p>
                  <p className="mt-0.5 leading-relaxed text-ink-secondary">{entry.reason}</p>
                </li>
                <li>
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">2. Boundary / what this does not mean</p>
                  <p className="mt-0.5 leading-relaxed text-ink-secondary">{entry.prohibited_claim}</p>
                </li>
                <li>
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">3. Final disposition</p>
                  <span className="mt-0.5 inline-flex rounded-[4px] border border-experimental/40 bg-experimental-soft px-2 py-0.5 text-[11px] font-semibold text-experimental">
                    {entry.excluded_from_final_architecture ? "Not selected for CORE_PLUS_CONTEXT" : "Disposition pending"}
                  </span>
                </li>
              </ol>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
