"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import * as THREE from "three";

import { H_FIGURE_MAX_Y, H_FIGURE_MIN_Y, H_SCAN_RINGS } from "@/components/visualization/human/holographicGeometry";
import { HOLO } from "@/components/visualization/human/holographicMaterials";

const SEGMENTS = 56;
const SCAN_PERIOD_SECONDS = 12;
const RING_DRIFT_RAD_PER_SEC = (Math.PI * 2) / 120; // extremely slow

function ellipse(radiusX: number, radiusZ: number): [number, number, number][] {
  const points: [number, number, number][] = [];
  for (let i = 0; i <= SEGMENTS; i++) {
    const t = (i / SEGMENTS) * Math.PI * 2;
    points.push([Math.cos(t) * radiusX, 0, Math.sin(t) * radiusZ]);
  }
  return points;
}

/**
 * Prompt 3B §6.3/§6.4 — the "Illustrative spatial scan field": ~7 thin
 * horizontal cyan rings at meaningful body levels, plus one very subtle
 * scan plane drifting head→feet. Purely a spatial visualization scaffold —
 * no ring/plane encodes any number, health, confidence, or reading. Under
 * reduced motion everything is static. Being a pure Three.js element it never
 * enters the accessibility tree (§18: scan rings are aria-hidden by nature).
 */
export function HumanScanRings({ reducedMotion }: { reducedMotion: boolean }) {
  const driftRef = useRef<THREE.Group>(null);
  const planeRef = useRef<THREE.Group>(null);
  const elapsedRef = useRef(0);

  const rings = useMemo(
    () => H_SCAN_RINGS.map((r) => ({ ...r, pts: ellipse(r.radiusX, r.radiusZ) })),
    [],
  );
  const planePts = useMemo(() => ellipse(0.32, 0.22), []);

  useFrame((_, delta) => {
    if (reducedMotion) return;
    if (driftRef.current) driftRef.current.rotation.y += RING_DRIFT_RAD_PER_SEC * delta;
    elapsedRef.current = (elapsedRef.current + delta) % SCAN_PERIOD_SECONDS;
    if (planeRef.current) {
      const phase = elapsedRef.current / SCAN_PERIOD_SECONDS;
      planeRef.current.position.y = H_FIGURE_MAX_Y - phase * (H_FIGURE_MAX_Y - H_FIGURE_MIN_Y);
    }
  });

  return (
    <group>
      <group ref={driftRef}>
        {rings.map((r) => (
          <group key={r.id} position={[0, r.y, 0]}>
            <Line points={r.pts} color={HOLO.cyan} transparent opacity={r.opacity} lineWidth={1} />
          </group>
        ))}
      </group>
      {/* Subtle horizontal scan plane drifting head→feet; static under reduced motion. */}
      <group ref={planeRef} position={[0, reducedMotion ? (H_FIGURE_MAX_Y + H_FIGURE_MIN_Y) / 2 : H_FIGURE_MAX_Y, 0]}>
        <Line points={planePts} color={HOLO.teal} transparent opacity={0.24} lineWidth={1.4} />
      </group>
    </group>
  );
}
