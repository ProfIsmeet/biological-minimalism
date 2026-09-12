import type { TrendPoint } from "@/components/charts/TrendLineChart";
import type { LiveMetricsSnapshot } from "@/lib/types";

export function toTrend(history: LiveMetricsSnapshot[], selector: (snapshot: LiveMetricsSnapshot) => number | null): TrendPoint[] {
  return history.flatMap((snapshot) => {
    const value = selector(snapshot);
    return value === null ? [] : [{ timestamp: snapshot.timestamp, value }];
  });
}
