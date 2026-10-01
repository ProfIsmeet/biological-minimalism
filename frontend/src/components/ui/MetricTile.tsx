import clsx from "clsx";

import type { StatusLevel } from "@/components/ui/StatusBadge";

const VALUE_COLOR: Record<StatusLevel, string> = {
  nominal: "text-ink-primary",
  warning: "text-signal-warning",
  critical: "text-signal-critical",
  offline: "text-signal-offline",
};

interface MetricTileProps {
  label: string;
  value: string;
  unit?: string;
  level?: StatusLevel;
  hint?: string;
}

export function MetricTile({ label, value, unit, level = "nominal", hint }: MetricTileProps) {
  // Status words ("Unavailable", "Input unavailable", "Model unavailable")
  // are far longer than the numeric readings (e.g. "66", "90/55") this tile
  // is otherwise sized for. At the numeric-reading size (text-2xl) a long
  // word overflows the tile's fixed grid column and visually overlaps the
  // next tile rather than wrapping. Long values get a smaller, wrapping
  // treatment; short numeric readings keep the large tabular-numeral size.
  const isLongValue = value.length > 6;

  return (
    <div className="flex min-w-0 flex-col gap-1 rounded-lg border border-jury-border-subtle bg-surface-2 px-3.5 py-3">
      <span className="text-xs uppercase tracking-wider text-ink-muted">{label}</span>
      <span className="flex min-w-0 flex-wrap items-baseline gap-1">
        <span
          className={clsx(
            "tabular-nums-mono min-w-0 break-words font-semibold",
            isLongValue ? "text-base leading-snug" : "text-2xl leading-none",
            VALUE_COLOR[level],
          )}
        >
          {value}
        </span>
        {unit ? <span className="text-xs text-ink-muted">{unit}</span> : null}
      </span>
      {hint ? <span className="text-xs text-ink-muted">{hint}</span> : null}
    </div>
  );
}
