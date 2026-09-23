"use client";

import { useEffect, useMemo } from "react";
import * as THREE from "three";

import { buildAnatomicalHuman, type MeshArrays } from "@/components/visualization/human/anatomicalHumanGeometry";
import { holoLatticeMaterial, holoRimMaterial, holoShellMaterial } from "@/components/visualization/human/holographicMaterials";

/**
 * Prompt 3C/3C.1/3C.2 §8 — the anatomical holographic human. Replaces the 3B
 * figure that was assembled from ~18 separate `cylinderGeometry` segments
 * (visible pipe seams at every joint) with an ORIGINAL merged multi-part
 * procedural mesh built from elliptical cross-section rings
 * (anatomicalHumanGeometry.ts): the torso is one lofted volume, each limb is
 * one lofted tube whose shoulder/elbow/hip/knee bends are blended by
 * parallel-transport frames rather than butted-together tubes, and the head
 * is a separate lofted skull. All six parts are concatenated into one draw
 * buffer by `mergeMeshArrays()` for a single draw call per layer — this is a
 * merged multi-part display mesh, not a single watertight or boolean-unioned
 * surface (§3C.1 §3.1); the parts overlap in space at the joints rather than
 * sharing welded vertices.
 *
 * §3C.2 §3.6 — volume-first three-layer system (replaces 3C.1's edge-only
 * treatment, which read as a black hollow torso with bright hook/belt
 * artifacts at the — then-open — limb roots; see holographicMaterials.ts for
 * the full root-cause explanation):
 *   Layer A — bright translucent teal/cyan body shell (the primary visual —
 *     the figure must read as a filled volume with this layer ALONE);
 *   Layer B — faint full wireframe lattice, subordinate to the shell, giving
 *     surface-following texture without dominating it;
 *   Layer C — backside-rendered, slightly expanded rim mesh (classic
 *     inverted-hull outline) that reads as a thin light rim at the
 *     silhouette edge only, separating the body from the dark stage.
 * Sensor contacts are a separate component. No text, no state, and no data
 * live here. Geometry is memoised once — nothing is rebuilt per frame (§25)
 * — and disposed on unmount.
 */
function toBufferGeometry(mesh: MeshArrays): THREE.BufferGeometry {
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(mesh.positions, 3));
  g.setAttribute("normal", new THREE.BufferAttribute(mesh.normals, 3));
  g.setIndex(new THREE.BufferAttribute(mesh.indices, 1));
  g.computeBoundingSphere();
  return g;
}

export function HolographicHumanFigure({ showWireframe = true }: { showWireframe?: boolean }) {
  const geometry = useMemo(() => toBufferGeometry(buildAnatomicalHuman().body), []);

  useEffect(() => () => geometry.dispose(), [geometry]);

  return (
    <group>
      {/* Layer C — rim, drawn first/furthest out so the shell draws over its front-facing gap and only the silhouette edge peeks through (§3C.3 §11: scale reduced 1.03→1.015 so it stops enlarging angular shoulder geometry). */}
      <mesh geometry={geometry} material={holoRimMaterial} scale={1.015} renderOrder={0} />
      {/* Layer A — the body shell. This layer alone must read as a filled human volume. */}
      <mesh geometry={geometry} material={holoShellMaterial} renderOrder={1} />
      {/* Layer B — faint surface lattice, subordinate to the shell (§3C.3 §11: scale 1.006→1.004). */}
      {showWireframe ? <mesh geometry={geometry} material={holoLatticeMaterial} scale={1.004} renderOrder={2} /> : null}
    </group>
  );
}
