"use client";

import { stage7AnchorMaterial } from "@/prototypes/stage7-digital-twin/stage7PrototypeMaterials";
import type { Stage7SensorAnchor, Stage7Selection } from "@/prototypes/stage7-digital-twin/types";

const ANCHOR_RADIUS = 0.018;
const ANCHOR_RADIUS_SELECTED = 0.026;

/**
 * Small, consistent 3D anchor markers only — no essential text lives inside
 * this canvas (design spec "Sensor anchor presentation"). The adjacent
 * Stage7SemanticTopology DOM list is the actual label/description surface.
 * A selected anchor renders slightly larger AND with a thin outline ring
 * (not color alone) so selection is distinguishable independent of hue.
 */
export function Stage7SensorAnchors({ anchors, selection }: { anchors: Stage7SensorAnchor[]; selection: Stage7Selection | null }) {
  return (
    <group>
      {anchors.map((anchor) => {
        const isSelected =
          selection !== null &&
          (selection.kind === "modality" ? selection.modality === anchor.modality : selection.regionId === anchor.region.toLowerCase());
        const radius = isSelected ? ANCHOR_RADIUS_SELECTED : ANCHOR_RADIUS;
        return (
          <group key={anchor.modality} position={anchor.position}>
            <mesh material={stage7AnchorMaterial(anchor.color)}>
              <sphereGeometry args={[radius, 16, 12]} />
            </mesh>
            {isSelected ? (
              <mesh>
                <sphereGeometry args={[radius * 1.6, 16, 12]} />
                <meshBasicMaterial color="#F2C265" wireframe transparent opacity={0.85} />
              </mesh>
            ) : null}
          </group>
        );
      })}
    </group>
  );
}
