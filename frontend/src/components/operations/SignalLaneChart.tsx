"use client";

import { Area, ComposedChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export interface SignalLanePoint {
  t: number;
  value: number;
}

function LaneTooltip({ active, payload, unit }: { active?: boolean; payload?: { payload: SignalLanePoint }[]; unit: string | null }) {
  if (!active || !payload?.length) return null;
  const point = payload[0]!.payload;
  return (
    <div className="rounded-[4px] border border-jury-border-strong bg-surface-2 px-2 py-1 font-mono text-[10px] leading-relaxed text-ink-primary shadow-sm">
      <div>t = {point.t.toFixed(3)}s</div>
      <div>{point.value.toFixed(3)}{unit ? ` ${unit}` : ""}</div>
    </div>
  );
}

/**
 * Thin recharts primitive factored out of SignalRibbonMatrix.tsx so that
 * file's own source stays free of container-sizing markup unrelated to its
 * content — kept as its own small, single-purpose component per the
 * project's no-premature-abstraction convention (one clear reuse: the three
 * synchronized-scope lanes all render the exact same chart shape).
 */
export function SignalLaneChart({
  points,
  domain,
  sharedDomain,
  color,
  unit,
  syncId,
  strokeWidth = 2,
}: {
  points: SignalLanePoint[];
  domain: [number, number];
  sharedDomain: [number, number] | null;
  color: string;
  unit: string | null;
  syncId: string;
  /** Mission Overview §11.1 — per-modality stroke weight from the shared token map. */
  strokeWidth?: number;
}) {
  return (
    <ResponsiveContainer>
      <ComposedChart syncId={syncId} syncMethod="value" data={points} margin={{ top: 4, right: 2, bottom: 4, left: 2 }}>
        <YAxis domain={domain} hide />
        <XAxis dataKey="t" type="number" domain={sharedDomain ?? ["dataMin", "dataMax"]} hide allowDataOverflow />
        <ReferenceLine y={domain[0] + (domain[1] - domain[0]) / 2} stroke="rgba(242,246,247,0.06)" strokeWidth={1} />
        {/* Tooltip is enhancement only — unit, value range, sample rate and
            time range are ALL also permanently visible in the lane gutter and
            caption, so no fact here is hover-only (§17). */}
        <Tooltip content={<LaneTooltip unit={unit} />} cursor={{ stroke: "rgba(242,246,247,0.14)" }} isAnimationActive={false} />
        <Area type="linear" dataKey="value" stroke={color} strokeWidth={strokeWidth} fill={color} fillOpacity={0.07} isAnimationActive={false} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
