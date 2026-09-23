import * as THREE from "three";

/**
 * Prompt 3B §6.5 — holographic scan palette. Deep navy/cyan spatial stage,
 * translucent body shell, thin luminous cyan wireframe. Deliberately NO
 * purple/pink, NO large glow clouds, NO particle fields.
 */
export const HOLO = {
  pageCanvas: "#071115",
  stageDeepNavy: "#061A26",
  stageSecondary: "#082533",
  cyan: "#45D6E5",
  teal: "#63BFB7",
  bodyBase: "#123846",
  bodyHighlight: "#2D788A",
  unavailable: "#516269",
} as const;

/**
 * Layer A — visible body shell (§3C.2 §3.6). §3C.1 dropped the shell nearly
 * to invisibility (opacity 0.42, emissiveIntensity 0.35, near-black emissive)
 * and then removed the dense wireframe that used to visually fill the
 * silhouette, so the two changes compounded into a torso that reads as a
 * black hollow void with only a faint edge outline. This is brightened back
 * into the readable range: base/emissive lifted toward the reference image's
 * "solid glowing volume" look, opacity raised toward the top of the
 * requested 0.42-0.58 band. `depthWrite: false` is kept (not the spec's
 * default-true suggestion) — three overlapping transparent layers (shell,
 * lattice, rim) sharing near-identical multi-part geometry produced visible
 * self-intersection artifacts with depth writing enabled during testing;
 * this is the narrowly-scoped exception the spec allows.
 */
export const holoShellMaterial = new THREE.MeshStandardMaterial({
  color: new THREE.Color("#1A5B68"),
  roughness: 0.68,
  metalness: 0.05,
  transparent: true,
  opacity: 0.54,
  emissive: new THREE.Color("#0D3640"),
  emissiveIntensity: 0.62,
  depthWrite: false,
  side: THREE.FrontSide,
});

/**
 * Layer B — restrained surface lattice (§3C.2 §3.6). §3C.1 replaced the raw
 * wireframe with `THREE.EdgesGeometry`, which unconditionally draws every
 * open-boundary edge (any edge shared by only one triangle) regardless of
 * its crease-angle threshold. The limb roots were open boundaries at the
 * time (capStart: false), so EdgesGeometry drew a full bright ring exactly
 * around each one — the actual mechanism behind the "shoulder hook" and
 * "mechanical pelvic belt" defects, not a symptom of the geometry itself.
 * Reverting to a faint RAW wireframe (every triangle edge, uniform low
 * opacity, no special emphasis on any one edge) both fixes that and, now
 * that the limb roots are capped again, has no open boundary to highlight.
 */
export const holoLatticeMaterial = new THREE.MeshBasicMaterial({
  color: new THREE.Color(HOLO.cyan),
  wireframe: true,
  transparent: true,
  opacity: 0.09, // §3C.3 §11 — 0.11→0.09 so the lattice stays subordinate to the shell
  depthWrite: false,
});

/**
 * Layer C — silhouette/rim definition (§3C.2 §3.6). Classic inverted-hull
 * outline: the same geometry, scaled slightly outward, rendered back-face-only
 * so it is invisible except at the silhouette edge (where the surface curves
 * away from the camera), reading as a thin rim of light separating the body
 * from the stage without a cartoon stroke or an outline around internal
 * (already-capped) boundaries.
 */
export const holoRimMaterial = new THREE.MeshBasicMaterial({
  color: new THREE.Color(HOLO.cyan),
  transparent: true,
  opacity: 0.2, // §3C.3 §11 — 0.3→0.20 (paired with scale 1.03→1.015) so the rim supports the silhouette without ghosting/enlarging angular shoulders
  depthWrite: false,
  side: THREE.BackSide,
});
