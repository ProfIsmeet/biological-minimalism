import * as THREE from "three";

/**
 * Module-level singleton materials (master prompt 3A §5/§20, restated
 * Prompt 3A.1 §7.1 with an exact palette after the original Prompt 3A
 * figure was judged too dark — "collapses into a nearly black silhouette").
 * Created once, shared by every body-segment mesh, never recreated per
 * frame or per render.
 *
 * `bodyMaterial` (main torso/limb/head surface) and `jointMaterial`
 * (secondary — joint spheres only, a visibly distinct but still dark tone)
 * are deliberately NOT the same object: Prompt 3A.1 §7.1 specifies two
 * different base tones ("Main body material" vs "Secondary body/joint
 * material"), and reusing one material for both would either wash out the
 * joint definition or require per-mesh color overrides that break the
 * "created once, shared" invariant this module exists to enforce. The
 * previous pass's heavy dark emissive (`#0a1416` @ 0.4) is gone — it was
 * actively suppressing lit detail rather than adding it; visibility now
 * comes from `roughness`/`metalness` tuned for a matte-but-lit surface plus
 * the lighting rig in PhysiologyAvatar3D.tsx, not from self-illumination.
 */
// Prompt 3A.2 §7 — brightened one step further from the 3A.1 values, using
// the exact palette in §7. The 3A.1 body (`#1B3038`) still rendered as a
// near-black silhouette in the actual browser render (verified from the
// failed screenshots, not from the hex value); `#28444D` with a slightly
// lower roughness and a faint sky-tone emissive lift reads as clearly
// volumetric under the neutral key + cool rim.
export const bodyMaterial = new THREE.MeshStandardMaterial({
  color: new THREE.Color("#28444D"),
  roughness: 0.55,
  metalness: 0.08,
  emissive: new THREE.Color("#12242a"),
  emissiveIntensity: 0.18,
});

export const jointMaterial = new THREE.MeshStandardMaterial({
  color: new THREE.Color("#203840"),
  roughness: 0.58,
  metalness: 0.08,
  emissive: new THREE.Color("#12242a"),
  emissiveIntensity: 0.18,
});

export const wireframeOverlayMaterial = new THREE.MeshBasicMaterial({
  color: new THREE.Color("#486872"),
  wireframe: true,
  transparent: true,
  opacity: 0.14,
});

/** Prompt 3A.1 §7.1 / 3A.2 §7 — canvas/stage base, set as the Canvas's explicit WebGL background. */
export const STAGE_BACKGROUND_COLOR = "#0B1519";

/** Prompt 3A.2 §7 — the exact key/rim light colours, shared by both the operational avatar and the conceptual twin stage so their lighting stays identical. */
export const KEY_LIGHT_COLOR = "#E2F1EF";
export const RIM_LIGHT_COLOR = "#75C7BD";

export function anchorRingColor(hex: string): THREE.Color {
  return new THREE.Color(hex);
}
