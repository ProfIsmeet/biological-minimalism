/**
 * Stage 2 A4 — fallback shown by `ConceptualTwinStage` when WebGL is
 * unsupported, fails to initialize, loses its context, or throws during
 * render. `ConceptualTwinStage` has no sensor anchors (unlike the
 * operational avatar), so this is a static text panel rather than
 * `StaticAvatarFallback`'s anchor map — but it preserves the exact same
 * architecture-only/untrained/unvalidated scientific boundary language the
 * live 3D disclaimer carries, and reports no rotation angle, adaptation
 * percentage, confidence value, or any other measured/invented quantity.
 * `onRetry` is supplied only when recovery is technically possible (a lost
 * context or a transient render error); omitted when WebGL is simply
 * unsupported on this device/browser.
 */
export function ConceptualTwinFallback({ onRetry }: { onRetry?: () => void }) {
  return (
    <div className="flex h-full min-h-[240px] flex-col items-center justify-center gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-2 p-6 text-center">
      <p className="text-sm font-semibold text-ink-primary">3D rendering unavailable on this device or browser</p>
      <p className="max-w-sm text-xs leading-relaxed text-ink-muted">
        This is an architecture-only, untrained, unvalidated holographic reference figure with an illustrative spatial
        scan field. It reports no adaptation percentage, confidence value, or measured quantity — the volumetric
        rendering itself could not be shown, but no information is lost, because the figure never encoded any.
      </p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-[6px] border border-jury-border-strong px-3 py-1.5 text-xs font-medium text-ink-secondary hover:bg-surface-1"
        >
          Try 3D view again
        </button>
      ) : null}
    </div>
  );
}
