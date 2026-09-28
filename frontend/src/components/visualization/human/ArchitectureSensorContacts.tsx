"use client";

import { Line } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";

import { H_CONTACT_POSITION } from "@/components/visualization/human/holographicGeometry";
import { REGION_ORBITS } from "@/components/visualization/human/humanLayout";
import { FINAL_SENSOR_INVENTORY, MODALITY_COLOR, type FinalRegion } from "@/lib/architecture";

function ellipsePoints(radiusX: number, radiusY: number): [number, number, number][] {
  return Array.from({ length: 49 }, (_, index) => {
    const angle = (index / 48) * Math.PI * 2;
    return [Math.cos(angle) * radiusX, Math.sin(angle) * radiusY, 0];
  });
}

/**
 * Static architecture landmarks for the Digital Twin reference. These marks
 * encode placement only: they do not read telemetry, availability, fault,
 * confidence, or model output. The DOM topology list beside the canvas is the
 * accessible source of the same information.
 */
export function ArchitectureSensorContacts({ activeRegion }: { activeRegion: FinalRegion | null }) {
  const halo = useMemo(() => ellipsePoints(0.031, 0.031), []);
  const selectedOrbit = REGION_ORBITS.find((orbit) => orbit.id === activeRegion?.toLowerCase());

  return (
    <group>
      {selectedOrbit ? (
        <group position={selectedOrbit.center}>
          <Line
            points={ellipsePoints(selectedOrbit.radiusX, selectedOrbit.radiusY).map(([x, y]) => [x, y, 0])}
            color="#A1D2CC"
            transparent
            opacity={0.78}
            lineWidth={1.5}
          />
        </group>
      ) : null}

      {FINAL_SENSOR_INVENTORY.map((sensor) => {
        const position = H_CONTACT_POSITION[sensor.modality] as [number, number, number];
        const color = MODALITY_COLOR[sensor.modality];
        const selected = sensor.region === activeRegion;
        return (
          <group key={sensor.modality} position={position}>
            {selected ? <Line points={halo} color="#F4F7F8" transparent opacity={0.92} lineWidth={1.4} /> : null}
            <mesh>
              <sphereGeometry args={[selected ? 0.021 : 0.016, 18, 14]} />
              <meshStandardMaterial
                color={color}
                emissive={new THREE.Color(color)}
                emissiveIntensity={selected ? 1.05 : 0.55}
                roughness={0.42}
              />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}
