"use client";

import type { ReactNode } from "react";

/**
 * Stage 6 — shared responsive chart shell. Every new/redesigned quantitative
 * visualization uses this so title size, unit placement, evidence-class tag,
 * and the accessible summary/table affordance stay consistent across
 * components instead of each chart inventing its own header.
 *
 * Deliberately NOT a generic charting framework — it owns layout and
 * accessibility scaffolding only; the actual marks are rendered by the
 * caller (Recharts or raw SVG), consistent with "prefer existing primitives,
 * do not build a bigger framework than the project needs".
 *
 * Stage 6 fresh-session audit correction (S6A-FIND-02, CRITICAL): the chart
 * body originally used `min-h-[Npx]` (min-height, auto height). A Recharts
 * `<ResponsiveContainer>` sets `height: 100%` on itself, and CSS percentage
 * heights do not resolve against an `auto`-height parent — only against a
 * *definite* height — so every Recharts chart mounted here silently
 * rendered at 0×0 (an empty `<div class="recharts-responsive-container">`
 * with no `<svg>` child at all, confirmed via direct DOM inspection during a
 * real populated fault/recovery timeline run) whenever the parent wasn't
 * independently given a definite height by its own layout context (a plain
 * flex-column section, as `FaultRecoveryTimeline` sits in). It happened to
 * *look* fine for `SensitivitySmallMultiples` only because that component's
 * `ChartFrame`s sit inside a CSS Grid, and grid-item stretch (the grid
 * default) establishes a definite height per spec, coincidentally masking
 * the same underlying bug. Now `h-[Npx]` (an explicit, definite height),
 * matching the pattern the pre-existing `RecentHrEstimateTrend.tsx` already
 * used correctly.
 */
export function ChartFrame({
  id,
  title,
  unit,
  evidenceClassLabel,
  summary,
  children,
  footer,
  heightClassName = "h-[220px]",
}: {
  id: string;
  title: string;
  unit?: string;
  evidenceClassLabel?: string;
  /** Plain-language one-sentence summary, read by assistive tech before the plot. */
  summary: string;
  children: ReactNode;
  footer?: ReactNode;
  heightClassName?: string;
}) {
  const headingId = `${id}-heading`;
  const summaryId = `${id}-summary`;
  return (
    <section aria-labelledby={headingId} aria-describedby={summaryId} className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id={headingId} className="text-base font-semibold leading-tight text-ink-primary sm:text-lg">
          {title}
          {unit ? <span className="ml-2 text-xs font-normal uppercase tracking-wide text-ink-muted">({unit})</span> : null}
        </h2>
        {evidenceClassLabel ? (
          <span className="rounded-[4px] border border-jury-border-subtle bg-surface-2 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-ink-muted">
            {evidenceClassLabel}
          </span>
        ) : null}
      </div>
      <p id={summaryId} className="text-sm leading-relaxed text-ink-secondary">
        {summary}
      </p>
      <div className={`w-full ${heightClassName}`}>{children}</div>
      {footer}
    </section>
  );
}

/** Accessible exact-value table, used as the non-visual equivalent for every quantitative mark rendered above it. */
export function SemanticTable({
  caption,
  columns,
  rows,
  className,
}: {
  caption: string;
  columns: string[];
  rows: { key: string; cells: ReactNode[] }[];
  className?: string;
}) {
  return (
    <div className={`overflow-x-auto ${className ?? ""}`}>
      <table className="w-full min-w-[480px] text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="border-b border-jury-border-subtle text-xs uppercase tracking-wide text-ink-muted">
          <tr>
            {columns.map((col) => (
              <th key={col} scope="col" className="px-3 py-2 font-semibold">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-jury-border-subtle">
          {rows.map((row) => (
            <tr key={row.key}>
              {row.cells.map((cell, i) => (
                <td key={i} className="px-3 py-2 align-top tabular-nums text-ink-secondary">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Categorical status pill — text/label-driven, never color-only. */
export function StatusPill({ label, tone }: { label: string; tone: "nominal" | "warning" | "fault" | "muted" | "info" }) {
  const toneClass: Record<typeof tone, string> = {
    nominal: "border-jury-success/40 bg-jury-success-soft text-jury-success",
    warning: "border-jury-warning/40 bg-jury-warning-soft text-jury-warning",
    fault: "border-jury-fault/40 bg-jury-fault-soft text-jury-fault",
    muted: "border-jury-border-subtle bg-surface-2 text-ink-muted",
    info: "border-information/40 bg-information-soft text-information",
  } as const;
  return (
    <span className={`inline-flex items-center rounded-[4px] border px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ${toneClass[tone]}`}>
      {label}
    </span>
  );
}
