"use client";

import { useMemo } from "react";

import { BODY_SEGMENTS, HEAD_RADIUS, JOINTS, SHOULDER_JOINT_RADIUS, computeSegmentTransform } from "@/components/visualization/human/humanGeometry";
import { stage7BodyMaterial, stage7JointMaterial, stage7LatticeMaterial } from "@/prototypes/stage7-digital-twin/stage7PrototypeMaterials";

const JOINT_SPHERES: { position: readonly [number, number, number]; radius: number }[] = [
  { position: [JOINTS.shoulderL.x, JOINTS.shoulderL.y, JOINTS.shoulderL.z], radius: SHOULDER_JOINT_RADIUS },
  { position: [JOINTS.shoulderR.x, JOINTS.shoulderR.y, JOINTS.shoulderR.z], radius: SHOULDER_JOINT_RADIUS },
  { position: [JOINTS.elbowL.x, JOINTS.elbowL.y, JOINTS.elbowL.z], radius: 0.05 },
  { position: [JOINTS.elbowR.x, JOINTS.elbowR.y, JOINTS.elbowR.z], radius: 0.05 },
  { position: [JOINTS.hipL.x, JOINTS.hipL.y, JOINTS.hipL.z], radius: 0.075 },
  { position: [JOINTS.hipR.x, JOINTS.hipR.y, JOINTS.hipR.z], radius: 0.075 },
  { position: [JOINTS.kneeL.x, JOINTS.kneeL.y, JOINTS.kneeL.z], radius: 0.058 },
  { position: [JOINTS.kneeR.x, JOINTS.kneeR.y, JOINTS.kneeR.z], radius: 0.058 },
];

/**
 * Stage 7 prototype human silhouette. Reuses the existing, imported,
 * unmodified geometry math (JOINTS, BODY_SEGMENTS, computeSegmentTransform
 * from humanGeometry.ts — the same body proportions and segment topology the
 * accepted HumanMannequin.tsx already uses) — this component changes ONLY
 * the material treatment (stage7PrototypeMaterials.ts), per
 * CURRENT_SYSTEM_AUDIT.md finding F1: opaque matte body as the primary read,
 * a barely-visible lattice overlay strictly subordinate to it, never the
 * reverse. `showLattice` is false in the prototype's static/2D-equivalent
 * conceptual mode illustration, matching the design spec's "wireframe
 * completely omitted under the static fallback" rule.
 */
export function Stage7HumanModel({ showLattice = true }: { showLattice?: boolean }) {
  const segmentTransforms = useMemo(
    () => BODY_SEGMENTS.map((segment) => ({ segment, transform: computeSegmentTransform(segment.from, segment.to) })),
    [],
  );

  return (
    <group>
      <mesh position={[JOINTS.head.x, JOINTS.head.y, JOINTS.head.z]} material={stage7BodyMaterial}>
        <sphereGeometry args={[HEAD_RADIUS, 24, 18]} />
      </mesh>
      {showLattice ? (
        <mesh position={[JOINTS.head.x, JOINTS.head.y, JOINTS.head.z]} material={stage7LatticeMaterial}>
          <sphereGeometry args={[HEAD_RADIUS * 1.01, 12, 9]} />
        </mesh>
      ) : null}

      {segmentTransforms.map(({ segment, transform }) => (
        <group key={segment.id} position={transform.position} quaternion={transform.quaternion} scale={[segment.scale?.[0] ?? 1, 1, segment.scale?.[1] ?? 1]}>
          <mesh material={stage7BodyMaterial}>
            <capsuleGeometry args={[segment.radius, Math.max(0.01, transform.length - segment.radius), 6, 12]} />
          </mesh>
        </group>
      ))}

      {JOINT_SPHERES.map((joint, index) => (
        <mesh key={index} position={joint.position} material={stage7JointMaterial}>
          <sphereGeometry args={[joint.radius, 14, 10]} />
        </mesh>
      ))}
    </group>
  );
}
