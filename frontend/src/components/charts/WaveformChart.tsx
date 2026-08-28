"use client";

import { Area, AreaChart, ResponsiveContainer, YAxis } from "recharts";

interface WaveformChartProps {
  data: number[];
  color: string;
  height?: number;
  flatline?: boolean;
}

export function WaveformChart({ data, color, height = 96, flatline = false }: WaveformChartProps) {
  const points = data.length > 0 ? data.map((value, index) => ({ index, value })) : [{ index: 0, value: 0 }];

  return (
    <div style={{ height }} className="relative w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={`waveform-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.45} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <YAxis domain={[-1.2, 1.6]} hide />
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.75}
            fill={`url(#waveform-${color.replace("#", "")})`}
            isAnimationActive={false}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
      {flatline ? (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="rounded-full bg-space-900/80 px-2.5 py-1 text-[10px] uppercase tracking-wider text-signal-offline">
            No Signal
          </span>
        </div>
      ) : null}
    </div>
  );
}
