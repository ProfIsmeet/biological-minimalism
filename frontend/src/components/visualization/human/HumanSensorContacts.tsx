"use client";

import { useMemo } from "react";
import { Line } from "@react-three/drei";
import * as THREE from "three";

import { H_CONTACT_POSITION } from "@/components/visualization/human/holographicGeometry";
import { HOLO } from "@/components/visualization/human/holographicMaterials";
import type { SensorAnchorModel } from "@/components/visualization/human/types";

function contactColor(anchor: SensorAnchorModel): string {
  if (anchor.state === "fault") return "#D46F70";
  if (anchor.state === "disconnected" || anchor.state === "source_error" || anchor.state === "unavailable") return HOLO.unavailable;
  if (anchor.state === "awaiting_confirmation" || anchor.state === "warmup") return "#D5A45E";
  return anchor.color;
}

function ringPoints(radius: number): [number, number, number][] {
  const pts: [number, number, number][] = [];
  for (let i = 0; i <= 28; i++) {
    const t = (i / 28) * Math.PI * 2;
    pts.push([Math.cos(t) * radius, Math.sin(t) * radius, 0]);
  }
  return pts;
}

/**
 * Prompt 3B §6.2 Layer C — on-body sensor contacts for the operational
 * holographic figure. Small state-colored spheres at anatomical positions,
 * with a selection halo, a coral fault ring, and desaturation when the
 * source cannot currently be trusted. Interactive buttons/labels are NOT
 * here — they remain in the collision-free DOM overlay (OperationalAvatarOverlay).
 */
export function HumanSensorContacts({ anchors }: { anchors: SensorAnchorModel[] }) {
  const ring = useMemo(() => ringPoints(0.03), []);
  return (
    <group>
      {anchors.map((anchor) => {
        const pos = (H_CONTACT_POSITION[anchor.modality] ?? [0, 1, 0]) as [number, number, number];
        const color = contactColor(anchor);
        const dimmed = anchor.state === "disconnected" || anchor.state === "source_error";
        return (
          <group key={anchor.modality} position={pos}>
            {anchor.selected ? (
              <mesh>
                <sphereGeometry args={[0.03, 16, 12]} />
                <meshBasicMaterial color={color} transparent opacity={0.3} />
              </mesh>
            ) : null}
            <mesh>
              <sphereGeometry args={[0.017, 14, 12]} />
              <meshStandardMaterial
                color={color}
                emissive={new THREE.Color(color)}
                emissiveIntensity={dimmed ? 0.15 : anchor.selected ? 0.95 : 0.6}
                roughness={0.35}
                transparent
                opacity={dimmed ? 0.45 : 1}
              />
            </mesh>
            {anchor.state === "fault" ? <Line points={ring} color="#D46F70" transparent opacity={0.9} lineWidth={1.4} dashed dashSize={0.012} gapSize={0.008} /> : null}
          </group>
        );
      })}
    </group>
  );
}
