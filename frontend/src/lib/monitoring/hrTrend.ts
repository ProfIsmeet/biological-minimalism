/**
 * Prompt 3C §10 — pure derivation for the Recent HR Estimate Trend. Consumes
 * only real confirmed-session snapshots (via `useConfirmedHistory()` at the
 * call site — never raw `missionStore.history`) and never fabricates a
 * historical value: a snapshot with no `heart_rate_prediction` contributes no
 * point, and a hole wider than the source's own typical sampling interval is
 * rendered as an explicit line break rather than connected across.
 */
const DEFAULT_WINDOW_SECONDS = 90;
const GAP_MULTIPLIER = 2.5;
const MIN_GAP_SECONDS = 4;

export interface HrTrendSample {
  timestampSeconds: number;
  heartRateBpm: number | null;
}

export interface HrTrendPoint {
  /** seconds relative to "now" — 0 is now, negative is in the past */
  tSeconds: number;
  /** null marks an explicit gap/line-break, never an interpolated value */
  value: number | null;
}

export interface HrTrendResult {
  points: HrTrendPoint[];
  currentValue: number | null;
  domain: [number, number] | null;
  windowSeconds: number;
  hasData: boolean;
}

export function deriveHrTrend(
  snapshots: HrTrendSample[],
  nowSeconds: number,
  windowSeconds: number = DEFAULT_WINDOW_SECONDS,
): HrTrendResult {
  const windowStart = nowSeconds - windowSeconds;
  const real = snapshots
    .filter(
      (s) =>
        s.heartRateBpm !== null &&
        Number.isFinite(s.heartRateBpm) &&
        s.timestampSeconds >= windowStart &&
        s.timestampSeconds <= nowSeconds,
    )
    .sort((a, b) => a.timestampSeconds - b.timestampSeconds);

  if (real.length === 0) {
    return { points: [], currentValue: null, domain: null, windowSeconds, hasData: false };
  }

  const diffs: number[] = [];
  for (let i = 1; i < real.length; i++) diffs.push(real[i]!.timestampSeconds - real[i - 1]!.timestampSeconds);
  diffs.sort((a, b) => a - b);
  const medianDiff = diffs.length ? diffs[Math.floor(diffs.length / 2)]! : 1;
  const gapThreshold = Math.max(MIN_GAP_SECONDS, medianDiff * GAP_MULTIPLIER);

  const points: HrTrendPoint[] = [];
  for (let i = 0; i < real.length; i++) {
    const sample = real[i]!;
    if (i > 0) {
      const prev = real[i - 1]!;
      if (sample.timestampSeconds - prev.timestampSeconds > gapThreshold) {
        // Explicit break: a null point just after the last real sample so the
        // chart never draws a straight line across an unavailable interval.
        points.push({ tSeconds: prev.timestampSeconds - nowSeconds + 0.01, value: null });
      }
    }
    points.push({ tSeconds: sample.timestampSeconds - nowSeconds, value: sample.heartRateBpm });
  }

  const values = real.map((s) => s.heartRateBpm!);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const pad = Math.max(2, (max - min) * 0.15);
  const domain: [number, number] = [Math.floor(min - pad), Math.ceil(max + pad)];

  return {
    points,
    currentValue: real[real.length - 1]!.heartRateBpm,
    domain,
    windowSeconds,
    hasData: true,
  };
}
