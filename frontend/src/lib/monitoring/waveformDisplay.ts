/**
 * Pure, JSX-free scientific-visualization helpers for WaveformChart (master
 * prompt 3 §8.6). Kept separate from the chart component itself so the
 * deterministic verification script can import and exercise them directly
 * (same convention as lib/monitoring/plotSeries.ts) without pulling in
 * recharts.
 */

export interface DownsampledPoint {
  index: number;
  value: number;
}

export interface DownsampleResult {
  points: DownsampledPoint[];
  downsampled: boolean;
}

/**
 * Dynamic Y-domain per master prompt §8.6: computed only from finite
 * displayed values, 8% padding on the observed range, or a small
 * value-relative pad when every finite value is identical (flatline).
 * Returns null when there is nothing finite to plot — callers must render
 * an explicit unavailable state rather than defaulting to an arbitrary
 * range.
 */
export function computeDynamicDomain(values: number[]): [number, number] | null {
  const finite = values.filter((value) => Number.isFinite(value));
  if (finite.length === 0) return null;

  let min = finite[0]!;
  let max = finite[0]!;
  for (const value of finite) {
    if (value < min) min = value;
    if (value > max) max = value;
  }

  if (min !== max) {
    const padding = (max - min) * 0.08;
    return [min - padding, max + padding];
  }

  const padding = Math.max(Math.abs(max) * 0.05, 1e-6);
  return [max - padding, max + padding];
}

/**
 * Deterministic extrema-preserving bucket downsampling per master prompt
 * §8.6. Always keeps the first and last sample, then divides the remaining
 * interior samples into equal buckets and keeps each bucket's min and max
 * (in original temporal order), so a narrow spike or trough between two
 * flat regions is never discarded the way naive stride decimation would
 * discard it. Never mutates the input array; never used for anything but
 * display.
 */
export function downsampleExtremaPreserving(values: number[], maxPoints: number): DownsampleResult {
  const n = values.length;
  const budget = Math.max(2, maxPoints);

  if (n <= budget) {
    return { points: values.map((value, index) => ({ index, value })), downsampled: false };
  }

  const result: DownsampledPoint[] = [{ index: 0, value: values[0]! }];

  const middleStart = 1;
  const middleEnd = n - 2; // inclusive
  const middleLength = Math.max(0, middleEnd - middleStart + 1);
  const remainingBudget = Math.max(0, budget - 2);
  const bucketCount = Math.max(1, Math.floor(remainingBudget / 2));

  if (middleLength > 0 && bucketCount > 0) {
    const bucketSize = Math.max(1, Math.ceil(middleLength / bucketCount));
    for (let start = middleStart; start <= middleEnd; start += bucketSize) {
      const end = Math.min(start + bucketSize - 1, middleEnd);
      let minIndex = start;
      let maxIndex = start;
      for (let i = start; i <= end; i++) {
        if (values[i]! < values[minIndex]!) minIndex = i;
        if (values[i]! > values[maxIndex]!) maxIndex = i;
      }
      if (minIndex === maxIndex) {
        result.push({ index: minIndex, value: values[minIndex]! });
      } else if (minIndex < maxIndex) {
        result.push({ index: minIndex, value: values[minIndex]! });
        result.push({ index: maxIndex, value: values[maxIndex]! });
      } else {
        result.push({ index: maxIndex, value: values[maxIndex]! });
        result.push({ index: minIndex, value: values[minIndex]! });
      }
    }
  }

  result.push({ index: n - 1, value: values[n - 1]! });

  if (result.length > budget) {
    const first = result[0]!;
    const last = result[result.length - 1]!;
    const middle = result.slice(1, -1);
    const keep = Math.max(0, budget - 2);
    const stride = middle.length / Math.max(1, keep);
    const trimmed: DownsampledPoint[] = [];
    for (let i = 0; i < keep; i++) {
      trimmed.push(middle[Math.min(middle.length - 1, Math.floor(i * stride))]!);
    }
    return { points: [first, ...trimmed, last], downsampled: true };
  }

  return { points: result, downsampled: true };
}
