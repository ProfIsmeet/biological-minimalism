"use client";

import { useMemo } from "react";

import { BODY_SEGMENTS, HEAD_RADIUS, JOINTS, SHOULDER_JOINT_RADIUS, computeSegmentTransform } from "@/components/visualization/human/humanGeometry";
import { bodyMaterial, jointMaterial, wireframeOverlayMaterial } from "@/components/visualization/human/humanMaterials";

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
 * Volumetric mannequin body (master prompt 3A §5). Every limb/torso element
 * is a shaded capsule or sphere mesh — never a line. Geometry/transforms are
 * memoized once (they are static; the mannequin does not animate per limb),
 * so no mesh is recreated on re-render, only sensor-anchor overlays update.
 */
export function HumanMannequin({ showWireframeOverlay = true }: { showWireframeOverlay?: boolean }) {
  const segmentTransforms = useMemo(
    () => BODY_SEGMENTS.map((segment) => ({ segment, transform: computeSegmentTransform(segment.from, segment.to) })),
    [],
  );

  return (
    <group>
      <mesh position={[JOINTS.head.x, JOINTS.head.y, JOINTS.head.z]} material={bodyMaterial}>
        <sphereGeometry args={[HEAD_RADIUS, 24, 18]} />
      </mesh>
      {showWireframeOverlay ? (
        <mesh position={[JOINTS.head.x, JOINTS.head.y, JOINTS.head.z]} material={wireframeOverlayMaterial}>
          <sphereGeometry args={[HEAD_RADIUS * 1.01, 12, 9]} />
        </mesh>
      ) : null}

      {segmentTransforms.map(({ segment, transform }) => (
        <group key={segment.id} position={transform.position} quaternion={transform.quaternion} scale={[segment.scale?.[0] ?? 1, 1, segment.scale?.[1] ?? 1]}>
          <mesh material={bodyMaterial}>
            <capsuleGeometry args={[segment.radius, Math.max(0.01, transform.length - segment.radius), 6, 12]} />
          </mesh>
        </group>
      ))}

      {JOINT_SPHERES.map((joint, index) => (
        <mesh key={index} position={joint.position} material={jointMaterial}>
          <sphereGeometry args={[joint.radius, 14, 10]} />
        </mesh>
      ))}
    </group>
  );
}
