"use client";

import { STAGE7_KEY_LIGHT_COLOR, STAGE7_RIM_LIGHT_COLOR } from "@/prototypes/stage7-digital-twin/stage7PrototypeMaterials";

/**
 * Restrained key + rim + soft ambient fill — no orbiting particles, no
 * pulsing, no more than these three static lights. Colors reuse the
 * existing system's own KEY_LIGHT_COLOR/RIM_LIGHT_COLOR family
 * (humanMaterials.ts) so the prototype's lighting language is a visible
 * refinement, not an unrelated new palette.
 */
export function Stage7Lighting() {
  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[2.2, 3.2, 2.6]} intensity={1.6} color={STAGE7_KEY_LIGHT_COLOR} />
      <directionalLight position={[-2.4, 1.4, -2.2]} intensity={0.75} color={STAGE7_RIM_LIGHT_COLOR} />
    </>
  );
}
