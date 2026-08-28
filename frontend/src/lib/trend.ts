import type { TrendPoint } from "@/components/charts/TrendLineChart";
import type { LiveMetricsSnapshot } from "@/lib/types";

export function toTrend(history: LiveMetricsSnapshot[], selector: (snapshot: LiveMetricsSnapshot) => number): TrendPoint[] {
  return history.map((snapshot) => ({ timestamp: snapshot.timestamp, value: selector(snapshot) }));
}
