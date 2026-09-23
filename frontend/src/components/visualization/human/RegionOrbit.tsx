"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import * as THREE from "three";

import type { RegionOrbitDef } from "@/components/visualization/human/humanLayout";

const SEGMENTS = 48;
const DRIFT_RADIANS_PER_SECOND = (Math.PI * 2) / 90; // one very slow revolution per 90s

function ellipsePoints(def: RegionOrbitDef): THREE.Vector3[] {
  const points: THREE.Vector3[] = [];
  for (let i = 0; i <= SEGMENTS; i++) {
    const t = (i / SEGMENTS) * Math.PI * 2;
    points.push(new THREE.Vector3(def.center[0] + Math.cos(t) * def.radiusX, def.center[1] + Math.sin(t) * def.radiusY * 0.3, def.center[2] + Math.sin(t) * def.radiusY));
  }
  return points;
}

/**
 * Physical-module grouping indicator only (master prompt 3A §7) — encodes no
 * health/quality/confidence/burden value. Rotation, when not reduced-motion,
 * is a slow drift (~1 revolution/90s), never a rapid spin.
 */
export function RegionOrbit({ def, reducedMotion }: { def: RegionOrbitDef; reducedMotion: boolean }) {
  const points = useMemo(() => ellipsePoints(def), [def]);
  const groupRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (reducedMotion || !groupRef.current) return;
    groupRef.current.rotation.y += DRIFT_RADIANS_PER_SECOND * delta;
  });

  return (
    <group ref={groupRef} position={def.center}>
      <Line points={points.map((p) => [p.x - def.center[0], p.y - def.center[1], p.z - def.center[2]])} color="#79a7d3" transparent opacity={0.22} lineWidth={1} />
    </group>
  );
}
