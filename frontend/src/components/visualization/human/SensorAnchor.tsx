"use client";

import * as THREE from "three";

import type { SensorAnchorModel } from "@/components/visualization/human/types";

/**
 * A single on-body sensor contact marker (Prompt 3A.2 §5.1). This renders the
 * Three.js contact point ONLY — a small coloured sphere at the anatomical
 * position, brightened when its modality is selected and desaturated when the
 * source cannot currently be trusted.
 *
 * The interactive, accessible button UI (label, aria, keyboard focus, state
 * text) deliberately no longer lives here. It moved to the DOM overlay
 * (OperationalAvatarOverlay) because five independent world-space `<Html>`
 * pills repeatedly collided with one another and with the region labels no
 * matter how their 3D offsets were tuned — the whole point of Prompt 3A.2 §5
 * is to stop positioning independent text labels inside the 3D world.
 */
export function SensorAnchor({ anchor }: { anchor: SensorAnchorModel }) {
  const dimmed = anchor.state === "disconnected" || anchor.state === "source_error" || anchor.state === "awaiting_confirmation";
  const markerColor = dimmed ? "#516269" : anchor.color;
  const position = anchor.position as unknown as [number, number, number];

  return (
    <group>
      {/* Selection halo — a slightly larger, faint ring sphere behind the marker. */}
      {anchor.selected ? (
        <mesh position={position}>
          <sphereGeometry args={[0.032, 16, 12]} />
          <meshBasicMaterial color={markerColor} transparent opacity={0.28} />
        </mesh>
      ) : null}
      <mesh position={position}>
        <sphereGeometry args={[0.019, 14, 12]} />
        <meshStandardMaterial
          color={markerColor}
          emissive={new THREE.Color(markerColor)}
          emissiveIntensity={dimmed ? 0.15 : anchor.selected ? 0.9 : 0.55}
          roughness={0.4}
          transparent
          opacity={dimmed ? 0.4 : 1}
        />
      </mesh>
    </group>
  );
}
