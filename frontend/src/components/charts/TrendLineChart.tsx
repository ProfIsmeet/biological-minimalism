"use client";

import { Area, AreaChart, ResponsiveContainer, Tooltip, YAxis } from "recharts";

export interface TrendPoint {
  timestamp: number;
  value: number;
}

interface TrendLineChartProps {
  data: TrendPoint[];
  color: string;
  domain?: [number, number];
  height?: number;
  unit?: string;
}

function TrendTooltip({ active, payload, unit }: { active?: boolean; payload?: { value: number }[]; unit?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-white/10 bg-space-900/95 px-2.5 py-1.5 text-xs text-slate-200 shadow-lg">
      {payload[0]!.value.toFixed(1)}
      {unit ? ` ${unit}` : ""}
    </div>
  );
}

export function TrendLineChart({ data, color, domain, height = 110, unit }: TrendLineChartProps) {
  const points = data.length > 0 ? data : [{ timestamp: 0, value: 0 }];

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 6, right: 4, bottom: 0, left: 4 }}>
          <defs>
            <linearGradient id={`trend-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <YAxis domain={domain ?? ["auto", "auto"]} hide />
          <Tooltip content={<TrendTooltip unit={unit} />} cursor={{ stroke: "rgba(255,255,255,0.15)" }} />
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill={`url(#trend-${color.replace("#", "")})`}
            isAnimationActive={false}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
