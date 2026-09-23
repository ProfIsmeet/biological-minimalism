"use client";

import { useEffect, useMemo, useState } from "react";
import { Area, ComposedChart, ResponsiveContainer, XAxis, YAxis } from "recharts";

import { deriveHrTrend } from "@/lib/monitoring/hrTrend";
import { useConfirmedHistory } from "@/lib/monitoring/useConfirmedSnapshot";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";

/** Mirrors MissionStatusBar's clock hook: starts null so SSR/first-client markup match, ticks after mount. */
function useNowSeconds(intervalMs: number): number | null {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now() / 1000);
    const id = setInterval(() => setNow(Date.now() / 1000), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
}

/**
 * Prompt 3C §10 — Recent HR Estimate Trend. Reads confirmed session history
 * ONLY through `useConfirmedHistory()` (the canonical hook — never raw
 * `missionStore.history`), derives the plotted series through the pure
 * `deriveHrTrend` module, and never draws a reference HR line or an
 * accuracy/error comparison: there is no reference HR channel in this
 * runtime, which is why the scope label says so explicitly.
 */
export function RecentHrEstimateTrend() {
  const view = useOperationalViewModel();
  const history = useConfirmedHistory();
  const nowSeconds = useNowSeconds(2000);

  const samples = useMemo(
    () => history.map((snapshot) => ({ timestampSeconds: snapshot.timestamp, heartRateBpm: snapshot.heart_rate_prediction?.value ?? null })),
    [history],
  );

  const trend = useMemo(() => {
    if (nowSeconds === null) return null;
    return deriveHrTrend(samples, nowSeconds);
  }, [samples, nowSeconds]);

  const notApplicable = !view.isReplay;

  return (
    <section aria-labelledby="hr-trend-heading" className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-3">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="hr-trend-heading" className="text-sm font-semibold text-ink-primary">
          Recent HR estimate trend
        </h2>
        {trend?.currentValue != null ? (
          <span className="font-mono text-xs font-semibold text-final-accent">{trend.currentValue.toFixed(1)} bpm</span>
        ) : null}
      </div>

      <div className="h-[92px] w-full">
        {notApplicable ? (
          <div className="flex h-full items-center justify-center text-center text-[11px] leading-snug text-ink-muted">
            Not applicable — synthetic demo carries no HR prediction stream.
          </div>
        ) : !trend || !trend.hasData || !trend.domain ? (
          <div className="flex h-full items-center justify-center text-center text-[11px] leading-snug text-ink-muted">
            No HR estimate in the last {trend?.windowSeconds ?? 90}s.{view.faultActive ? " Simulated fault is withholding the output." : ""}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={trend.points} margin={{ top: 4, right: 6, bottom: 2, left: 6 }}>
              <YAxis domain={trend.domain} hide />
              <XAxis dataKey="tSeconds" type="number" domain={[-trend.windowSeconds, 0]} hide />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#69B7AD"
                strokeWidth={1.8}
                fill="#69B7AD"
                fillOpacity={0.08}
                isAnimationActive={false}
                connectNulls={false}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>

      <p className="font-mono text-[10px] text-ink-muted">Replay HR estimate · no reference HR channel in the current runtime</p>
      {/* §3C.1 §5 — an unexplained break in the line can read as a rendering
          defect; this stays visible regardless of whether the current window
          happens to contain a gap, and stays visually subordinate (smaller,
          dimmer) to the scope label above it. */}
      <p className="text-[9.5px] leading-snug text-ink-disabled">Gaps indicate intervals where the HR output was unavailable or withheld.</p>
    </section>
  );
}
