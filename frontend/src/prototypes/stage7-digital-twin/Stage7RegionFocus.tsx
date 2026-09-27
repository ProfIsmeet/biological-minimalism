"use client";

import { REGION_ORBITS } from "@/components/visualization/human/humanLayout";
import { stage7RegionFocusMaterial } from "@/prototypes/stage7-digital-twin/stage7PrototypeMaterials";
import type { Stage7RegionId } from "@/prototypes/stage7-digital-twin/types";

/**
 * Region focus outline (design spec §"Region focus") — a single subtle
 * outline ellipse at the selected region's existing, imported, unmodified
 * REGION_ORBITS bounds (humanLayout.ts). Replaces the audited "excessive
 * ambient scan rings" pattern (CURRENT_SYSTEM_AUDIT F3): this outline is
 * shown ONLY for the currently-focused region, never all three at once and
 * never as always-on decoration.
 */
export function Stage7RegionFocus({ regionId }: { regionId: Stage7RegionId | null }) {
  if (!regionId) return null;
  const orbit = REGION_ORBITS.find((candidate) => candidate.id === regionId);
  if (!orbit) return null;

  return (
    <group>
      <mesh position={orbit.center} rotation={[-Math.PI / 2, 0, 0]} scale={[1, orbit.radiusY / orbit.radiusX, 1]}>
        <torusGeometry args={[orbit.radiusX, 0.003, 8, 48]} />
        <primitive object={stage7RegionFocusMaterial} attach="material" />
      </mesh>
    </group>
  );
}
