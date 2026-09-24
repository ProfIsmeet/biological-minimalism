/**
 * Stage 2 A4 — single shared WebGL-availability check, used by every 3D
 * physiology/Digital Twin surface instead of each one re-implementing its
 * own copy (previously only `PhysiologyAvatar3D.tsx` had this; the
 * conceptual Digital Twin stage had no detection at all and would render a
 * broken/blank `<Canvas>` on a device without WebGL).
 */
export function detectWebgl(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}
