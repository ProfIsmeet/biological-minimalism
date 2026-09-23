"use client";

import { useMemo } from "react";
import { Line } from "@react-three/drei";

import { HOLO } from "@/components/visualization/human/holographicMaterials";

function ellipse(radiusX: number, radiusZ: number, segments = 64): [number, number, number][] {
  const pts: [number, number, number][] = [];
  for (let i = 0; i <= segments; i++) {
    const t = (i / segments) * Math.PI * 2;
    pts.push([Math.cos(t) * radiusX, 0, Math.sin(t) * radiusZ]);
  }
  return pts;
}

/**
 * Prompt 3B §6.5 — deep navy/cyan spatial stage. Explicit dark navy WebGL
 * background, a restrained key + cyan rim light, faint ambient, and a subtle
 * floor ellipse at the feet. Deliberately NO star field, particles, purple
 * gradients, glow clouds, or lens flares.
 */
export function HolographicStageAtmosphere() {
  const floorOuter = useMemo(() => ellipse(0.55, 0.34), []);
  const floorInner = useMemo(() => ellipse(0.34, 0.21), []);
  return (
    <group>
      <color attach="background" args={[HOLO.stageDeepNavy]} />
      <ambientLight intensity={0.72} />
      {/* Neutral key. */}
      <directionalLight position={[1.6, 2.6, 2.2]} intensity={1.15} color="#E4F3F2" />
      {/* Cyan rim. */}
      <directionalLight position={[-1.8, 1.0, -1.4]} intensity={0.6} color={HOLO.cyan} />
      {/* Faint floor ellipses at the feet. */}
      <group position={[0, 0.01, 0]}>
        <Line points={floorOuter} color={HOLO.cyan} transparent opacity={0.16} lineWidth={1} />
        <Line points={floorInner} color={HOLO.teal} transparent opacity={0.12} lineWidth={1} />
      </group>
    </group>
  );
}
