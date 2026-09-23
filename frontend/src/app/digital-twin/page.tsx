"use client";

import dynamic from "next/dynamic";

const ConceptualTwinStage = dynamic(() => import("@/components/visualization/human/ConceptualTwinStage").then((m) => m.ConceptualTwinStage), {
  ssr: false,
  loading: () => <div className="flex h-[380px] items-center justify-center text-xs text-ink-muted sm:h-[520px]">Loading conceptual twin stage…</div>,
});

// Prompt 3A.2 §8 — Digital Twin composition rebuilt. The figure is a purely
// conceptual, architecture-only volumetric illustration, so this route no
// longer calls the backend, holds no mission-day state, and renders no
// scenario-day control (all of which only ever changed a conceptual label and
// risked implying a modeled time-series). The domains are fixed conceptual
// domains, not day-dependent state; the second right-panel card states the
// proposed computation boundary categorically, not as a metric. A single
// page-level safety badge is shown; no text is overlaid on the mannequin.
const PROPOSED_DOMAINS = ["Cardiovascular", "Cognitive", "Fluid Balance", "Thermal Regulation"];

const COMPUTATION_BOUNDARY: { label: string; value: string }[] = [
  { label: "Inputs", value: "Final sensing architecture" },
  { label: "Model layer", value: "Future personalized baseline" },
  { label: "Output boundary", value: "No trained output in this demonstrator" },
];

export default function DigitalTwinPage() {
  return (
    <div className="mx-auto flex min-w-0 max-w-[1200px] flex-col gap-5 overflow-x-hidden px-0 py-2">
      <div>
        <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-information">Reference / Digital Twin</span>
        <h1 className="mt-2 text-[28px] font-semibold leading-tight tracking-[-0.025em] text-ink-primary sm:text-[34px]">
          Digital Twin reference
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
          Conceptual architecture demonstration for a future personalized physiological model. No model is trained,
          personalized, or validated in this demonstrator.
        </p>
        <span className="mt-2 inline-block rounded-[4px] border border-jury-warning/40 bg-jury-warning-soft px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-jury-warning">
          ARCHITECTURE ONLY · UNTRAINED · UNVALIDATED
        </span>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Primary visual (§8.3): 8 columns, visually dominant, figure fully framed, no overlaid text. */}
        <div className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4 lg:col-span-8">
          <h2 className="text-sm font-semibold text-ink-primary">Conceptual architecture view</h2>
          <ConceptualTwinStage />
          <p className="text-xs leading-relaxed text-ink-secondary">
            Illustrative spatial model scaffold. No trained personalized state is active. The scan rings and wireframe
            are decorative spatial elements, not measurements — this figure reports no adaptation percentage,
            confidence value, or measured quantity.
          </p>
        </div>

        {/* Supporting information (§8.3): 4 columns. */}
        <div className="flex flex-col gap-5 lg:col-span-4">
          <div className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
            <h2 className="text-sm font-semibold text-ink-primary">Proposed model domains</h2>
            <ul className="flex flex-col gap-1 text-xs text-ink-secondary">
              {PROPOSED_DOMAINS.map((domain) => (
                <li key={domain}>{domain}</li>
              ))}
            </ul>
            <p className="text-[11px] leading-relaxed text-ink-muted">
              Conceptual domains only. No currently inferred physiological state is reported.
            </p>
          </div>

          <div className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
            <h2 className="text-sm font-semibold text-ink-primary">Proposed computation boundary</h2>
            <dl className="flex flex-col gap-2">
              {COMPUTATION_BOUNDARY.map((row) => (
                <div key={row.label} className="flex flex-col gap-0.5 border-b border-jury-border-subtle pb-2 last:border-0 last:pb-0">
                  <dt className="text-[10px] font-semibold uppercase tracking-wide text-ink-muted">{row.label}</dt>
                  <dd className="text-xs text-ink-secondary">{row.value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}
