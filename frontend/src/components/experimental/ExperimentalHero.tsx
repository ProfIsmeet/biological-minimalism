import { FlaskConical } from "lucide-react";

// Master-prompt §9.1 — exact required hero copy for the Experimental
// Research route. Ochre/experimental accent, never the final-system teal.
export function ExperimentalHero() {
  return (
    <header className="flex flex-col gap-4 border-b border-jury-border-subtle pb-8">
      <div className="flex items-center gap-2 text-experimental">
        <FlaskConical size={16} strokeWidth={2.25} aria-hidden="true" />
        <span className="text-[11px] font-semibold uppercase tracking-[0.1em]">
          Biological Minimalism / Research Archive
        </span>
      </div>
      <h1 className="max-w-[760px] text-[34px] font-semibold leading-[1.08] tracking-[-0.035em] text-ink-primary sm:text-[38px] lg:text-[44px]">
        Experimental sensor studies
      </h1>
      <p className="max-w-[720px] text-[17px] leading-[1.55] text-ink-secondary">
        Candidate-sensor investigations, sensitivity analyses, and mixed or negative findings that informed—but were
        not carried into—the final CORE_PLUS_CONTEXT architecture.
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-md border border-experimental/40 bg-experimental-soft px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-experimental">
          Research evidence — not final system
        </span>
      </div>
      <p className="max-w-[720px] text-sm leading-[1.55] text-ink-muted">
        These sensors and experiments are excluded from the final sensing inventory unless explicitly stated
        otherwise.
      </p>
    </header>
  );
}
