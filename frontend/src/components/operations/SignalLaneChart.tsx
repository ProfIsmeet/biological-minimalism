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
}: {
  points: SignalLanePoint[];
  domain: [number, number];
  sharedDomain: [number, number] | null;
  color: string;
  unit: string | null;
  syncId: string;
}) {
  return (
    <ResponsiveContainer>
      <ComposedChart syncId={syncId} syncMethod="value" data={points} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
        <YAxis domain={domain} hide />
        <XAxis dataKey="t" type="number" domain={sharedDomain ?? ["dataMin", "dataMax"]} hide allowDataOverflow />
        <ReferenceLine y={domain[0] + (domain[1] - domain[0]) / 2} stroke="rgba(242,246,247,0.05)" strokeWidth={1} />
        <Tooltip content={<LaneTooltip unit={unit} />} cursor={{ stroke: "rgba(242,246,247,0.14)" }} isAnimationActive={false} />
        <Area type="linear" dataKey="value" stroke={color} strokeWidth={1.5} fill={color} fillOpacity={0.05} isAnimationActive={false} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
