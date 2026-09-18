"use client";

import type { ReactNode } from "react";

import { TrendLineChart } from "@/components/charts/TrendLineChart";
import { Panel } from "@/components/ui/Panel";
import { useConfirmedHistory } from "@/lib/monitoring/useConfirmedSnapshot";
import { toTrend } from "@/lib/trend";
import type { LiveMetricsSnapshot } from "@/lib/types";

/**
 * Trend metrics are looked up by key (rather than accepting a selector
 * function prop) so `TrendPanel` can be used from server-component pages
 * without crossing the server/client boundary with a function value.
 */
export type TrendMetric =
  | "heart_rate_bpm"
  | "hrv_rmssd_ms"
  | "cognitive_load"
  | "fatigue"
  | "circadian_stability"
  | "ai_confidence";

const SELECTORS: Record<TrendMetric, (snapshot: LiveMetricsSnapshot) => number | null> = {
  heart_rate_bpm: (s) => s.heart_rate_prediction?.value ?? s.vitals?.heart_rate_bpm ?? null,
  hrv_rmssd_ms: (s) => s.vitals?.hrv_rmssd_ms ?? null,
  cognitive_load: (s) => s.cognitive?.cognitive_load ?? null,
  fatigue: (s) => s.cognitive?.fatigue ?? null,
  circadian_stability: (s) => s.cognitive?.circadian_stability ?? null,
  ai_confidence: (s) => s.ai_confidence?.overall_confidence ?? null,
};

interface TrendPanelProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  color: string;
  unit?: string;
  domain?: [number, number];
  metric: TrendMetric;
}

export function TrendPanel({ title, subtitle, icon, color, unit, domain, metric }: TrendPanelProps) {
  const history = useConfirmedHistory();
  const selector = SELECTORS[metric];
  const latest = history.reduce<number | null>((value, snapshot) => selector(snapshot) ?? value, null);

  return (
    <Panel
      title={title}
      subtitle={subtitle}
      icon={icon}
      actions={
        latest !== null ? (
          <span className="tabular-nums-mono text-sm font-semibold text-slate-200">
            {latest.toFixed(1)}
            {unit ? <span className="ml-1 text-xs font-normal text-slate-500">{unit}</span> : null}
          </span>
        ) : undefined
      }
    >
      <TrendLineChart data={toTrend(history, selector)} color={color} domain={domain} unit={unit} />
    </Panel>
  );
}
