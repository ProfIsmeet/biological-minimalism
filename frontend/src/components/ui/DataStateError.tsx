"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";

interface DataStateErrorProps {
  title: string;
  source: string;
  cause: string;
  onRetry?: () => void;
}

/**
 * Shared accessible error/recovery pattern for API-backed sections
 * (corrective-pass §10). Distinct from an empty-but-valid state: this
 * component is only for an actual request failure, never for "canonically
 * empty". No stack trace, no fabricated fallback value.
 */
export function DataStateError({ title, source, cause, onRetry }: DataStateErrorProps) {
  return (
    <div role="alert" className="flex flex-col gap-2 rounded-md border border-jury-fault/30 bg-jury-fault-soft px-4 py-3">
      <div className="flex items-start gap-2">
        <AlertTriangle size={15} className="mt-0.5 shrink-0 text-jury-fault" aria-hidden="true" />
        <div>
          <p className="text-xs font-semibold text-ink-primary">{title}</p>
          <p className="mt-0.5 text-[11px] text-ink-muted">Source: {source}</p>
          <p className="mt-1 text-[11px] leading-relaxed text-ink-secondary">{cause}</p>
        </div>
      </div>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="flex w-fit items-center gap-1.5 rounded-[4px] border border-jury-border-strong px-2.5 py-1.5 text-[11px] font-medium text-ink-secondary transition-colors duration-150 hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
        >
          <RefreshCw size={12} aria-hidden="true" /> Retry
        </button>
      ) : null}
    </div>
  );
}
