/**
 * Pure Y-axis rotation + perspective projection math for
 * components/visualization/RotatingTwinFigure.tsx, split out so
 * scripts/verify-monitoring-state.ts can assert the geometry stays finite
 * even for a zero-size container (same pure/JSX-free convention as
 * lib/monitoring/waveformDisplay.ts).
 */

export interface Point3 {
  x: number;
  y: number;
  z: number;
}

export function rotateY(point: Point3, angle: number): Point3 {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  return { x: point.x * cos + point.z * sin, y: point.y, z: -point.x * sin + point.z * cos };
}

export function projectPoint(point: Point3, width: number, height: number, scale: number): { x: number; y: number; depthFactor: number } {
  const perspective = 4.2;
  const factor = perspective / (perspective + point.z);
  return {
    x: width / 2 + point.x * scale * factor,
    y: height / 2 - (point.y - 0.86) * scale * factor,
    depthFactor: factor,
  };
}
