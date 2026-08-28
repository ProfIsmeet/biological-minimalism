import clsx from "clsx";

import type { StatusLevel } from "@/components/ui/StatusBadge";

const VALUE_COLOR: Record<StatusLevel, string> = {
  nominal: "text-slate-100",
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
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-white/5 bg-white/[0.02] px-3.5 py-3">
      <span className="text-[11px] uppercase tracking-wider text-slate-500">{label}</span>
      <span className="flex items-baseline gap-1">
        <span className={clsx("tabular-nums-mono text-2xl font-semibold leading-none", VALUE_COLOR[level])}>
          {value}
        </span>
        {unit ? <span className="text-xs text-slate-500">{unit}</span> : null}
      </span>
      {hint ? <span className="text-[11px] text-slate-500">{hint}</span> : null}
    </div>
  );
}
