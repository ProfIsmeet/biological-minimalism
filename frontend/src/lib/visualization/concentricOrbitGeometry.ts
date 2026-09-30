/** Pure geometry for the four categorical integrity rings. */
export const FIXED_ORBIT_SWEEP_DEGREES = 300;
export const FIXED_ORBIT_GAP_DEGREES = 60;

/**
 * Returns one fixed-sweep arc. No state or value parameter is accepted: ring
 * state can alter only the stroke treatment, never the angular geometry.
 */
export function fixedOrbitArcPath(cx: number, cy: number, radius: number): string {
  const startAngle = 90 + FIXED_ORBIT_GAP_DEGREES / 2;
  const endAngle = startAngle + FIXED_ORBIT_SWEEP_DEGREES;
  const toXY = (degrees: number) => {
    const radians = (degrees * Math.PI) / 180;
    return {
      x: Math.round((cx + radius * Math.cos(radians)) * 100) / 100,
      y: Math.round((cy + radius * Math.sin(radians)) * 100) / 100,
    };
  };
  const start = toXY(startAngle);
  const end = toXY(endAngle);
  const largeArc = FIXED_ORBIT_SWEEP_DEGREES > 180 ? 1 : 0;
  return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArc} 1 ${end.x} ${end.y}`;
}
