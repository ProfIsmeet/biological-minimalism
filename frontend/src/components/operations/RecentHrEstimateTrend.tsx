"use client";

import { useEffect, useMemo, useState } from "react";
import { Area, CartesianGrid, ComposedChart, ResponsiveContainer, XAxis, YAxis } from "recharts";

import { PLOT_COLOR } from "@/lib/visualization/operationalVisualTokens";
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
    <section aria-labelledby="hr-trend-heading" className="flex h-full flex-col gap-2.5 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-[18px]">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="hr-trend-heading" className="text-[17px] font-semibold leading-tight text-ink-primary">
          Recent HR estimate trend
        </h2>
        {visibleCurrentValue != null ? (
          <span className="font-mono text-[24px] font-semibold tabular-nums leading-none text-final-accent">
            {visibleCurrentValue.toFixed(1)} <span className="text-[13px] font-medium text-ink-secondary">bpm</span>
          </span>
        ) : null}
      </div>

      {view.isReplay && view.predictionAvailability !== "available" && trend?.hasData ? (
        <p className="rounded-[5px] border border-jury-warning/30 bg-jury-warning-soft px-2 py-1.5 text-xs leading-snug text-jury-warning">
          Current HR unavailable · plot retains confirmed historical estimates only
        </p>
      ) : null}

      {/* Mission Overview §10 — materially enlarged to a primary analytical
          plot (300px+ desktop internal plot area, 250px+ mobile) so it can
          hold its own beside the concentric orbit and the human stage
          instead of reading as a sparkline. */}
      <div className="h-[250px] w-full min-[768px]:h-[300px] min-[1366px]:h-[330px]">
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
            <ComposedChart data={trend.points} margin={{ top: 8, right: 14, bottom: 4, left: 0 }}>
              <CartesianGrid stroke={PLOT_COLOR.grid} strokeWidth={1} vertical={false} />
              <YAxis
                domain={trend.domain}
                tickCount={5}
                width={46}
                tick={{ fontSize: 12, fill: PLOT_COLOR.axisText }}
                axisLine={false}
                tickLine={false}
                label={{ value: "HR (bpm)", angle: -90, position: "insideLeft", fontSize: 12, fill: PLOT_COLOR.axisText }}
              />
              <XAxis
                dataKey="tSeconds"
                type="number"
                domain={[-trend.windowSeconds, 0]}
                ticks={[-trend.windowSeconds, -trend.windowSeconds / 2, 0]}
                tickFormatter={(value: number) => (value === 0 ? "now" : `-${Math.round(-value)}s`)}
                tick={{ fontSize: 12, fill: PLOT_COLOR.axisText }}
                axisLine={false}
                tickLine={false}
                height={30}
                label={{ value: "Replay time (s, relative)", position: "insideBottom", offset: -2, fontSize: 12, fill: PLOT_COLOR.axisText }}
              />
              {/* `type="linear"` is deliberate (§10): monotone smoothing would
                  draw curved segments implying intermediate samples that were
                  never observed. connectNulls={false} keeps every withheld
                  interval a real visible break, never an interpolated line. */}
              <Area
                type="linear"
                dataKey="value"
                stroke={PLOT_COLOR.hrLine}
                strokeWidth={2.5}
                fill={PLOT_COLOR.hrLine}
                fillOpacity={0.12}
                isAnimationActive={false}
                connectNulls={false}
                dot={false}
                activeDot={false}
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
