"use client";

import dynamic from "next/dynamic";

import { DIGITAL_TWIN_SCOPE_LABEL, FINAL_MODULES } from "@/lib/architecture";

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
const COMPUTATION_BOUNDARY: { label: string; value: string }[] = [
  { label: "Current input", value: "Static CORE_PLUS_CONTEXT architecture facts" },
  { label: "Future model layer", value: "Longitudinal personalized baseline, not implemented here" },
  { label: "Current output", value: "Anatomical placement and topology only" },
];

export default function DigitalTwinPage() {
  return (
    <div className="mx-auto flex min-w-0 max-w-[1320px] flex-col gap-6 overflow-x-hidden px-0 py-2">
      <header className="max-w-3xl">
        <span className="text-xs font-semibold uppercase tracking-[0.1em] text-information">System reference / Stage 7</span>
        <h1 className="mt-2 text-[28px] font-semibold leading-tight tracking-[-0.025em] text-ink-primary sm:text-[34px]">
          Biological Digital Twin architecture
        </h1>
        <p className="mt-2 text-base leading-relaxed text-ink-secondary">
          Inspect how the accepted wrist, chest, and frontal sensing modules map onto a future physiological-model
          scaffold. This view explains system topology; it does not display a person-specific twin or live physiology.
        </p>
        <span className="mt-3 inline-block rounded-[5px] border border-jury-warning/40 bg-jury-warning-soft px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-jury-warning">
          ARCHITECTURE ONLY · UNTRAINED · UNVALIDATED
        </span>
      </header>

      <div className="grid min-w-0 grid-cols-1 gap-6 xl:grid-cols-12">
        <div className="min-w-0 rounded-[12px] border border-jury-border-subtle bg-surface-1 p-4 sm:p-5 xl:col-span-9">
          <ConceptualTwinStage />
        </div>

        <aside className="flex min-w-0 flex-col gap-5 xl:col-span-3" aria-label="Digital Twin limitations and architecture boundary">
          <div className="rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
            <h2 className="text-base font-semibold text-ink-primary">What is represented</h2>
            <ol className="mt-3 flex flex-col gap-3">
              {FINAL_MODULES.map((module) => (
                <li key={module.id} className="border-l-2 border-information/45 pl-3">
                  <p className="text-sm font-semibold text-ink-primary">{module.order} · {module.label}</p>
                  <p className="mt-1 text-xs text-ink-secondary">{module.modalities}</p>
                </li>
              ))}
            </ol>
            <p className="mt-4 text-xs leading-relaxed text-ink-muted">
              Landmark glow means “selected in this viewer,” never sensor health, fault severity, or confidence.
            </p>
          </div>

          <div className="rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
            <h2 className="text-base font-semibold text-ink-primary">Proposed computation boundary</h2>
            <dl className="mt-3 flex flex-col gap-3">
              {COMPUTATION_BOUNDARY.map((row) => (
                <div key={row.label} className="border-b border-jury-border-subtle pb-3 last:border-0 last:pb-0">
                  <dt className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{row.label}</dt>
                  <dd className="mt-1 text-sm leading-relaxed text-ink-secondary">{row.value}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="rounded-[10px] border border-jury-warning/30 bg-jury-warning-soft p-4">
            <h2 className="text-sm font-semibold text-jury-warning">Scientific boundary</h2>
            <p className="mt-2 text-sm leading-relaxed text-ink-secondary">{DIGITAL_TWIN_SCOPE_LABEL}</p>
            <p className="mt-2 text-xs leading-relaxed text-ink-muted">
              No astronaut calibration, clinical interpretation, diagnostic result, adaptation score, or trained Digital
              Twin output exists in this route.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
