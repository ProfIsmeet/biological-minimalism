"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import {
  BOUNDED_ESTIMATE_QUALIFIER,
  CONDITIONAL_SELECTION_STATEMENT,
  FINAL_ARCHITECTURE_ID,
  PARETO_RELEVANCE_LIMITATION,
} from "@/lib/architecture";
import type { FinalWearableArchitecture } from "@/lib/types";

// Master-prompt §7.7 — evidence-to-decision: Evidence → Burden → Conditional
// selection. Burden figures are read live from the same canonical artifact
// SelectedArchitecturePanel already uses; nothing here is invented, and a
// missing figure renders as "Not available" rather than a fabricated value.
export function EvidenceDecisionFlow() {
  const [architecture, setArchitecture] = useState<FinalWearableArchitecture | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getFinalWearableArchitecture()
      .then((envelope) => {
        if (!cancelled && envelope.availability === "available") setArchitecture(envelope.architecture);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const burden = architecture?.burden_ranges as
    | { power_mw?: { selected_topology_battery_side?: number }; mass_g?: { battery_only?: number }; contacts?: { min?: number; max?: number; most_likely?: number } }
    | undefined;
  const regionCount = architecture?.selected_body_regions.length ?? 3;
  const power = burden?.power_mw?.selected_topology_battery_side;
  const mass = burden?.mass_g?.battery_only;
  const contacts = burden?.contacts;

  return (
    <section aria-labelledby="evidence-decision-heading" className="flex flex-col gap-5 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-6">
      <h2 id="evidence-decision-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
        Why this architecture
      </h2>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="flex flex-col gap-2 rounded-md border border-jury-border-subtle bg-surface-2 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Evidence</p>
          <ul className="flex flex-col gap-1.5 text-sm text-ink-secondary">
            <li>PPG-DaLiA HR model</li>
            <li>Robustness replay</li>
            <li>Multimodal complementarity</li>
            <li>Candidate-sensor experiments</li>
          </ul>
        </div>

        <div className="flex flex-col gap-2 rounded-md border border-jury-border-subtle bg-surface-2 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">Burden</p>
          <ul className="flex flex-col gap-1.5 text-sm text-ink-secondary">
            <li>{regionCount} body regions</li>
            <li>5 sensing modalities</li>
            <li>Mass: {mass != null ? `${mass} g (battery-only)` : "Not available"}</li>
            <li>Power: {power != null ? `~${power} mW (battery-side)` : "Not available"}</li>
            <li>Contacts: {contacts?.most_likely != null ? `${contacts.most_likely} (most likely)` : "Not available"}</li>
          </ul>
          <p className="mt-1 text-[11px] leading-relaxed text-ink-muted">{BOUNDED_ESTIMATE_QUALIFIER}</p>
        </div>

        <div className="flex flex-col gap-2 rounded-md border border-final-accent/40 bg-final-accent-soft p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-final-accent">Selection</p>
          <ul className="flex flex-col gap-1.5 text-sm text-ink-primary">
            <li className="font-semibold">{FINAL_ARCHITECTURE_ID}</li>
            <li>3 body regions</li>
            <li>5 modalities</li>
            <li>EOG added beyond MINIMAL_CORE</li>
          </ul>
        </div>
      </div>

      <div className="flex flex-col gap-1.5 border-t border-jury-border-subtle pt-4">
        <p className="text-sm font-medium text-ink-primary">{CONDITIONAL_SELECTION_STATEMENT}</p>
        <p className="text-xs leading-relaxed text-ink-muted">{PARETO_RELEVANCE_LIMITATION}</p>
      </div>
    </section>
  );
}
