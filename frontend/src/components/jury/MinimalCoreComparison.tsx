import { CORE_PLUS_CONTEXT_SUMMARY, EOG_DELTA_NOTE, MINIMAL_CORE_SUMMARY } from "@/lib/architecture";

// Master-prompt §7.4 — MINIMAL_CORE comparison. Only the "+ EOG" delta gets
// the final-accent highlight; IMU is never presented as a difference.
export function MinimalCoreComparison() {
  return (
    <section aria-label="MINIMAL_CORE comparison" className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-5">
      <div className="flex flex-col gap-1 border-b border-jury-border-subtle pb-3 sm:flex-row sm:items-center sm:justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">MINIMAL_CORE</span>
        <span className="text-sm text-ink-secondary">{MINIMAL_CORE_SUMMARY}</span>
      </div>
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-final-accent">CORE_PLUS_CONTEXT</span>
        <span className="text-sm text-ink-primary">
          {CORE_PLUS_CONTEXT_SUMMARY.replace("+ EOG", "")}
          <span className="ml-1 rounded-[4px] border border-final-accent/50 bg-final-accent-soft px-1.5 py-0.5 text-xs font-semibold text-final-accent">
            + EOG
          </span>
        </span>
      </div>
      <p className="pt-1 text-xs leading-relaxed text-ink-muted">{EOG_DELTA_NOTE}</p>
    </section>
  );
}
