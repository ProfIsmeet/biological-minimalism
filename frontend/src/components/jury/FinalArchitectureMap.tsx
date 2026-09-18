import { FINAL_MODULES } from "@/lib/architecture";

// Master-prompt §7.3 — final sensing architecture schematic. A neutral
// vertical connecting line plus three module nodes (Frontal → Chest →
// Wrist); all information has a text equivalent, decorative line hidden
// from assistive technology.
export function FinalArchitectureMap() {
  return (
    <section aria-labelledby="final-architecture-heading" className="flex flex-col gap-4">
      <div>
        <h2 id="final-architecture-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
          Final sensing architecture
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
          Five modalities are integrated across three wearable regions. The architecture is organized by physical
          module, not by isolated sensor count.
        </p>
      </div>

      <ol className="relative flex flex-col gap-6 pl-2">
        <span
          aria-hidden="true"
          className="absolute left-[19px] top-4 bottom-4 w-px bg-jury-border-strong"
        />
        {FINAL_MODULES.map((module) => (
          <li key={module.id} className="relative flex items-start gap-4">
            <span
              aria-hidden="true"
              className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-final-accent bg-surface-1 text-[10px] font-semibold text-final-accent"
            >
              {module.order}
            </span>
            <div className="flex flex-col gap-0.5 pt-0.5">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">
                {module.order} — {module.id.toUpperCase()}
              </p>
              <p className="text-base font-semibold text-ink-primary">{module.label}</p>
              <p className="text-sm text-final-accent">{module.modalities}</p>
              <p className="text-sm text-ink-secondary">{module.description}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
