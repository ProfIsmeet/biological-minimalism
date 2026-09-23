"use client";

import { useMemo } from "react";
import { Area, ComposedChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { computeDynamicDomain, downsampleExtremaPreserving, type DownsampledPoint } from "@/lib/monitoring/waveformDisplay";

const DISPLAY_POINT_BUDGET = 400;

interface WaveformChartProps {
  values: number[];
  color: string;
  height?: number;
  unit?: string | null;
  transform?: string | null;
  sampleRateHz?: number | null;
  startTimestampSeconds?: number | null;
}

interface WaveformPoint extends DownsampledPoint {
  t: number;
}

function buildPoints(
  sampled: DownsampledPoint[],
  hasTiming: boolean,
  sampleRateHz: number | null,
  startTimestampSeconds: number | null,
): WaveformPoint[] {
  return sampled.map((point) => ({
    ...point,
    t: hasTiming ? startTimestampSeconds! + point.index / sampleRateHz! : point.index,
  }));
}

function WaveformTooltip({
  active,
  payload,
  hasTiming,
  unit,
}: {
  active?: boolean;
  payload?: { payload: WaveformPoint }[];
  hasTiming: boolean;
  unit: string | null;
}) {
  if (!active || !payload?.length) return null;
  const point = payload[0]!.payload;
  return (
    <div className="rounded-[4px] border border-jury-border-strong bg-surface-2 px-2.5 py-1.5 font-mono text-[11px] leading-relaxed text-ink-primary shadow-sm">
      <div>{hasTiming ? `t = ${point.t.toFixed(3)} s` : `sample ${point.index}`}</div>
      <div>
        value = {point.value.toFixed(3)}
        {unit ? ` ${unit}` : " device units"}
      </div>
    </div>
  );
}

/**
 * Restrained scientific line chart (master prompt 3 §8.6). Replaces the
 * previous fixed [-1.2, 1.6] normalized domain — inappropriate across PPG,
 * acceleration magnitude, and ECG — with a domain computed only from the
 * values actually being displayed, and replaces naive stride decimation
 * with the deterministic extrema-preserving bucket algorithm in
 * lib/monitoring/waveformDisplay.ts so narrow peaks/troughs survive
 * downsampling. No smoothing, no animation, no synthetic extrema.
 */
export function WaveformChart({
  values,
  color,
  height = 110,
  unit = null,
  transform = null,
  sampleRateHz = null,
  startTimestampSeconds = null,
}: WaveformChartProps) {
  const hasTiming = sampleRateHz != null && sampleRateHz > 0 && startTimestampSeconds != null;

  const { points, domain, isDownsampled } = useMemo(() => {
    if (!values.length) {
      return { points: [] as WaveformPoint[], domain: null as [number, number] | null, isDownsampled: false };
    }
    const { points: sampled, downsampled } = downsampleExtremaPreserving(values, DISPLAY_POINT_BUDGET);
    return {
      points: buildPoints(sampled, hasTiming, sampleRateHz, startTimestampSeconds),
      domain: computeDynamicDomain(values),
      isDownsampled: downsampled,
    };
  }, [values, hasTiming, sampleRateHz, startTimestampSeconds]);

  if (!points.length || !domain) {
    return (
      <div style={{ height }} className="flex items-center justify-center text-xs text-ink-muted">
        No plottable samples in the current window.
      </div>
    );
  }

  const crossesZero = domain[0] <= 0 && domain[1] >= 0;
  const guideLow = domain[0] + (domain[1] - domain[0]) / 3;
  const guideHigh = domain[0] + ((domain[1] - domain[0]) * 2) / 3;
  const firstPoint = points[0]!;
  const lastPoint = points[points.length - 1]!;
  const startLabel = hasTiming ? `t=${firstPoint.t.toFixed(2)}s` : `sample ${firstPoint.index}`;
  const endLabel = hasTiming ? `t=${lastPoint.t.toFixed(2)}s` : `sample ${lastPoint.index}`;

  return (
    <div className="flex flex-col gap-1">
      {/* §11.2 — the min/max range is a real gutter column, not text
          absolutely overlaid on top of the plotted trace (which could
          collide with the line or with nearby labels). */}
      <div className="flex w-full items-stretch gap-1.5">
        <div style={{ height }} className="min-w-0 flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={points} margin={{ top: 4, right: 4, bottom: 2, left: 4 }}>
            <YAxis domain={domain} hide />
            <XAxis dataKey="t" hide type="number" domain={["dataMin", "dataMax"]} />
            <ReferenceLine y={guideLow} stroke="rgba(242,246,247,0.06)" strokeWidth={1} />
            <ReferenceLine y={guideHigh} stroke="rgba(242,246,247,0.06)" strokeWidth={1} />
            {crossesZero ? <ReferenceLine y={0} stroke="#30464F" strokeWidth={1} /> : null}
            <Tooltip
              content={<WaveformTooltip hasTiming={hasTiming} unit={unit} />}
              cursor={{ stroke: "rgba(242,246,247,0.14)" }}
              isAnimationActive={false}
            />
            <Area
              type="linear"
              dataKey="value"
              stroke={color}
              strokeWidth={1.6}
              fill={color}
              fillOpacity={0.04}
              isAnimationActive={false}
              dot={false}
            />
          </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="flex w-11 shrink-0 flex-col justify-between py-0.5 text-right font-mono text-[10px] text-ink-muted">
          <span>{domain[1].toFixed(2)}</span>
          <span>{domain[0].toFixed(2)}</span>
        </div>
      </div>
      <div className="flex justify-between font-mono text-[10px] text-ink-disabled">
        <span>{startLabel}</span>
        <span>{endLabel}</span>
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-0.5 font-mono text-[10px] text-ink-muted">
        <span>{unit ? `Unit: ${unit}` : "Unit not provided by current source"}</span>
        <span>{values.length} raw samples</span>
        <span>{points.length} pts displayed</span>
        {sampleRateHz != null ? <span>{sampleRateHz} Hz source</span> : null}
        {transform ? <span>{transform}</span> : null}
        {isDownsampled ? <span className="text-ink-disabled">Display downsampled</span> : null}
      </div>
    </div>
  );
}
