"use client";

import { DataStateError } from "@/components/ui/DataStateError";
import { titleCase } from "@/lib/format";
import { useResearchStore } from "@/store/researchStore";

// Master-prompt §9.6 (corrective pass §3) — research provenance. Concise
// source names in the main list; full repository paths only inside the
// disclosure, per §9.6's "do not fill the main UI with repository paths".
export function ExperimentalProvenance() {
  const stage3Evidence = useResearchStore((state) => state.stage3Evidence);
  const stage3EvidenceError = useResearchStore((state) => state.stage3EvidenceError);
  const finalWearableArchitecture = useResearchStore((state) => state.finalWearableArchitecture);
  const loading = useResearchStore((state) => state.loading);
  const load = useResearchStore((state) => state.load);

  const entries = stage3Evidence?.entries ?? [];
  const hasAnything = entries.length > 0 || Boolean(finalWearableArchitecture);
  const provenance = finalWearableArchitecture?.provenance as
    | { accepted_stage3_sha?: string; source_artifacts?: string[] }
    | undefined;

  return (
    <section aria-labelledby="provenance-heading" className="flex flex-col gap-4">
      <div>
        <h2 id="provenance-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
          Research provenance
        </h2>
      </div>

      {loading && !stage3Evidence && !finalWearableArchitecture ? (
        <p className="text-sm text-ink-muted">Loading provenance…</p>
      ) : stage3EvidenceError && !hasAnything ? (
        <DataStateError
          title="Provenance unavailable"
          source="/research/stage3-evidence"
          cause={stage3EvidenceError}
          onRetry={() => void load()}
        />
      ) : !hasAnything ? (
        <p className="text-sm text-ink-muted">No canonical provenance record is available in the current frontend data source.</p>
      ) : (
        <>
          <ul className="divide-y divide-jury-border-subtle rounded-[10px] border border-jury-border-subtle bg-surface-1">
            {entries.map((entry) => (
              <li key={entry.family_id} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3 text-sm">
                <span className="font-medium text-ink-primary">{titleCase(entry.family_id)}</span>
                <span className="text-ink-muted">
                  {entry.experiment_id ? `Experiment ${entry.experiment_id} · ` : ""}
                  {entry.biological_subject_n !== null ? `n=${entry.biological_subject_n} · ` : ""}
                  {entry.artifact_type}
                </span>
              </li>
            ))}
            {provenance?.accepted_stage3_sha ? (
              <li className="flex flex-wrap items-center justify-between gap-2 px-5 py-3 text-sm">
                <span className="font-medium text-ink-primary">Final architecture closure</span>
                <span className="text-ink-muted">accepted Stage-3 SHA {provenance.accepted_stage3_sha.slice(0, 12)}…</span>
              </li>
            ) : null}
          </ul>

          <details className="rounded-md border border-jury-border-subtle bg-surface-2">
            <summary className="cursor-pointer px-4 py-3 text-xs font-medium text-ink-muted">Full artifact paths</summary>
            <div className="border-t border-jury-border-subtle px-4 py-3">
              {entries.map((entry) => (
                <p key={entry.family_id} className="break-all font-mono text-[10px] text-ink-disabled">
                  {entry.family_id}: {entry.artifact_path}
                </p>
              ))}
              {provenance?.source_artifacts?.map((path) => (
                <p key={path} className="break-all font-mono text-[10px] text-ink-disabled">
                  {path}
                </p>
              ))}
            </div>
          </details>
        </>
      )}
    </section>
  );
}
