"use client";

import { useEffect, useMemo, useState } from "react";
import { Area, ComposedChart, ResponsiveContainer, XAxis, YAxis } from "recharts";

import { deriveHrTrend } from "@/lib/monitoring/hrTrend";
import { visibleTrendCurrentValue } from "@/lib/monitoring/hrOperationalPresentation";
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
  const visibleCurrentValue = visibleTrendCurrentValue(view.predictionAvailability, trend?.currentValue ?? null);

  return (
    <section aria-labelledby="hr-trend-heading" className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-3">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="hr-trend-heading" className="text-sm font-semibold text-ink-primary">
          Recent HR estimate trend
        </h2>
        {visibleCurrentValue != null ? (
          <span className="font-mono text-base font-semibold text-final-accent">{visibleCurrentValue.toFixed(1)} bpm</span>
        ) : null}
      </div>

      {view.isReplay && view.predictionAvailability !== "available" && trend?.hasData ? (
        <p className="rounded-[5px] border border-jury-warning/30 bg-jury-warning-soft px-2 py-1.5 text-xs leading-snug text-jury-warning">
          Current HR unavailable · plot retains confirmed historical estimates only
        </p>
      ) : null}

      {/* Stage 6 (master prompt §14) — enlarged from the prior 120-140px
          sparkline-scale container so the axes/gap legibility this chart
          already computed correctly (see hrTrend.ts) is actually readable as
          a primary quantitative plot, not compressed decoration. */}
      <div className="h-[220px] w-full sm:h-[240px] 2xl:h-[260px]">
        {notApplicable ? (
          <div className="flex h-full items-center justify-center text-center text-[13px] leading-snug text-ink-muted">
            Not applicable — synthetic demo carries no HR prediction stream.
          </div>
        ) : !trend || !trend.hasData || !trend.domain ? (
          <div className="flex h-full items-center justify-center text-center text-[13px] leading-snug text-ink-muted">
            No HR estimate in the last {trend?.windowSeconds ?? 90}s.{view.faultActive ? " Simulated fault is withholding the output." : ""}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={trend.points} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
              {/* Real, visible tick labels instead of `hide` — a reviewer must
                  be able to read the bpm range and time direction without
                  guessing. Two ticks each (min/max, window-start/now) keep
                  this legible without turning a 140px sparkline into a full
                  scientific chart (that redesign is Stage 6 scope). */}
              <YAxis
                domain={trend.domain}
                tickCount={4}
                width={40}
                tick={{ fontSize: 12, fill: "#8CA0A6" }}
                axisLine={false}
                tickLine={false}
                label={{ value: "bpm", angle: -90, position: "insideLeft", fontSize: 12, fill: "#8CA0A6" }}
              />
              <XAxis
                dataKey="tSeconds"
                type="number"
                domain={[-trend.windowSeconds, 0]}
                ticks={[-trend.windowSeconds, 0]}
                tickFormatter={(value: number) => (value === 0 ? "now" : `-${Math.round(-value)}s`)}
                tick={{ fontSize: 12, fill: "#8CA0A6" }}
                axisLine={false}
                tickLine={false}
                height={16}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#69B7AD"
                strokeWidth={2}
                fill="#69B7AD"
                fillOpacity={0.1}
                isAnimationActive={false}
                connectNulls={false}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>

      <p className="font-mono text-xs text-ink-muted">Replay HR estimate · no reference HR channel in the current runtime</p>
      {/* §3C.1 §5 — an unexplained break in the line can read as a rendering
          defect; this stays visible regardless of whether the current window
          happens to contain a gap, and stays visually subordinate (smaller,
          dimmer) to the scope label above it. Kept at/above the 12px floor
          rather than the previous 9.5px. */}
      <p className="text-xs leading-snug text-ink-disabled">Gaps indicate intervals where the HR output was unavailable or withheld.</p>
    </section>
  );
}
