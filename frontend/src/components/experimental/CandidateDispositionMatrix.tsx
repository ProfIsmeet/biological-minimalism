"use client";

import { Archive } from "lucide-react";

import { DataStateError } from "@/components/ui/DataStateError";
import { CANDIDATE_DISPOSITION_DISPLAY } from "@/lib/architecture";
import type { FinalWearableArchitecture } from "@/lib/types";
import { useResearchStore } from "@/store/researchStore";

// Master-prompt §9.2 (corrective pass §8) — Candidate sensor disposition.
// Every row is read live from results/final_wearable_architecture.json's
// exclusion_rationale; a key absent from the artifact does not render, and
// no outcome is invented. Provenance is cross-referenced against
// /research/stage3-evidence by family_id where one exists (see
// CANDIDATE_DISPOSITION_DISPLAY.stage3FamilyId) — never fabricated when no
// family evaluates a candidate (wrist_temperature_light has none: the
// artifact's own reason is TIER_P_PENDING, absence of evidence).
//
// Prompt-2 fix (master prompt §7.1): this used to independently fetch both
// api.getFinalWearableArchitecture() and api.getStage3Evidence(), duplicating
// the single load ResearchDataLoader already triggers for the whole route.
// It now reads both from the shared store.
export function CandidateDispositionMatrix() {
  const architecture = useResearchStore((store) => store.finalWearableArchitecture);
  const architectureError = useResearchStore((store) => store.finalWearableArchitectureError);
  const stage3Evidence = useResearchStore((store) => store.stage3Evidence);
  const loading = useResearchStore((store) => store.loading);
  const load = useResearchStore((store) => store.load);

  const stage3Entries = stage3Evidence?.entries ?? [];
  const state: "loading" | "available" | "empty" | "error" = loading && !architecture
    ? "loading"
    : architectureError && !architecture
      ? "error"
      : !architecture || Object.keys(architecture.exclusion_rationale).length === 0
        ? "empty"
        : "available";
  const errorMessage = architectureError;

  const entries = architecture ? Object.entries(architecture.exclusion_rationale) : [];

  function provenanceFor(key: string): { label: string; path: string | null } {
    const familyId = CANDIDATE_DISPOSITION_DISPLAY[key]?.stage3FamilyId;
    if (!familyId) return { label: "No canonical evidence family recorded", path: null };
    const stage3Entry = stage3Entries.find((entry) => entry.family_id === familyId);
    if (!stage3Entry) return { label: "No canonical evidence family recorded", path: null };
    const path = stage3Entry.artifact_path;
    const basename = path?.split("/").pop() ?? familyId;
    return { label: basename, path };
  }

  function dispositionFor(entry: FinalWearableArchitecture["exclusion_rationale"][string]): string {
    return entry.excluded_from_final_architecture ? "Not selected for CORE_PLUS_CONTEXT" : "Disposition pending";
  }

  return (
    <section className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-6">
      <div>
        <h2 className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
          Candidate sensor disposition
        </h2>
      </div>

      {state === "loading" ? (
        <p className="text-sm text-ink-muted">Loading canonical disposition record…</p>
      ) : state === "error" ? (
        <DataStateError
          title="Candidate disposition unavailable"
          source="results/final_wearable_architecture.json"
          cause={errorMessage ?? "The canonical architecture artifact could not be loaded."}
          onRetry={() => void load()}
        />
      ) : state === "empty" ? (
        <p className="text-sm text-ink-muted">Outcome not available in the current canonical source.</p>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden overflow-x-auto sm:block">
            <table className="w-full min-w-[960px] text-left text-sm">
              <thead className="border-b border-jury-border-subtle text-[11px] uppercase tracking-wide text-ink-muted">
                <tr>
                  <th className="px-3 py-2 font-semibold">Candidate / experiment</th>
                  <th className="px-3 py-2 font-semibold">Body region</th>
                  <th className="px-3 py-2 font-semibold">Candidate description</th>
                  <th className="px-3 py-2 font-semibold">Evidence status</th>
                  <th className="px-3 py-2 font-semibold">Final disposition</th>
                  <th className="px-3 py-2 font-semibold">Provenance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-jury-border-subtle">
                {entries.map(([key, entry]) => {
                  const display = CANDIDATE_DISPOSITION_DISPLAY[key];
                  const provenance = provenanceFor(key);
                  return (
                    <tr key={key}>
                      <td className="px-3 py-3 align-top font-medium text-ink-primary">
                        {display?.label ?? key.replace(/_/g, " ")}
                      </td>
                      <td className="px-3 py-3 align-top text-ink-secondary">{display?.region ?? "Not specified"}</td>
                      <td className="px-3 py-3 align-top text-ink-secondary">
                        {display?.evaluationRole ?? "Candidate sensing modality"}
                      </td>
                      <td className="max-w-[280px] px-3 py-3 align-top text-ink-secondary">{entry.reason}</td>
                      <td className="px-3 py-3 align-top">
                        <span className="inline-flex rounded-[4px] border border-experimental/40 bg-experimental-soft px-2 py-0.5 text-[11px] font-semibold text-experimental">
                          {dispositionFor(entry)}
                        </span>
                      </td>
                      <td className="px-3 py-3 align-top font-mono text-[11px] text-ink-muted" title={provenance.path ?? undefined}>
                        {provenance.label}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile stacked list */}
          <ul className="flex flex-col gap-3 sm:hidden">
            {entries.map(([key, entry]) => {
              const display = CANDIDATE_DISPOSITION_DISPLAY[key];
              const provenance = provenanceFor(key);
              return (
                <li key={key} className="rounded-md border border-jury-border-subtle bg-surface-2 p-3">
                  <p className="font-medium text-ink-primary">{display?.label ?? key.replace(/_/g, " ")}</p>
                  <p className="mt-1 text-xs text-ink-muted">{display?.region ?? "Not specified"}</p>
                  <p className="mt-1 text-xs text-ink-secondary">{display?.evaluationRole ?? "Candidate sensing modality"}</p>
                  <p className="mt-2 text-xs text-ink-secondary">{entry.reason}</p>
                  <span className="mt-2 inline-flex rounded-[4px] border border-experimental/40 bg-experimental-soft px-2 py-0.5 text-[11px] font-semibold text-experimental">
                    {dispositionFor(entry)}
                  </span>
                  <p className="mt-2 font-mono text-[10px] text-ink-muted">Provenance: {provenance.label}</p>
                </li>
              );
            })}
          </ul>

          <details className="mt-1 rounded-md border border-jury-border-subtle bg-surface-2">
            <summary className="flex cursor-pointer items-center gap-2 px-3 py-2 text-xs font-medium text-ink-muted">
              <Archive size={13} aria-hidden="true" /> Provenance detail
            </summary>
            <div className="border-t border-jury-border-subtle px-3 py-2 text-[11px] leading-relaxed text-ink-muted">
              <p>Disposition source: results/final_wearable_architecture.json (exclusion_rationale).</p>
              {entries.map(([key]) => {
                const provenance = provenanceFor(key);
                return provenance.path ? (
                  <p key={key} className="mt-1 break-all font-mono text-[10px] text-ink-muted">
                    {CANDIDATE_DISPOSITION_DISPLAY[key]?.label ?? key}: {provenance.path}
                  </p>
                ) : null;
              })}
              <p className="mt-2">
                Prohibited claims per entry: BioZ is not presented as generally useless, and generalization beyond the
                tested terrestrial endpoint is not asserted.
              </p>
            </div>
          </details>
        </>
      )}
    </section>
  );
}
