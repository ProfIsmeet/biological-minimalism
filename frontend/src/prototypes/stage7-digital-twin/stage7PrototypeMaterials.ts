import * as THREE from "three";

/**
 * Stage 7 prototype — module-level singleton materials, created once, never
 * recreated per frame or per render (mirrors the existing, proven pattern in
 * humanMaterials.ts). This is the ONE thing this prototype deliberately
 * changes relative to the audited current system (CURRENT_SYSTEM_AUDIT.md
 * F1): the body surface is a real, mostly-opaque matte material as the
 * PRIMARY read, with the wireframe lattice reduced to a barely-visible,
 * strictly subordinate accent — not the other way around.
 */

export const STAGE7_STAGE_BACKGROUND = "#0A1114";

// Self-review finding (PROTOTYPE_DESIGN_SPEC.md / MASTER_HANDOFF_REPORT.md
// §18): the first render pass used these same tones ~30% darker
// (`#3A5560`/`#2C444D`, emissiveIntensity 0.12) and the figure was legible
// only when the screenshot was zoomed in — at normal viewing scale it
// collapsed into the dark stage background, i.e. the exact silhouette
// problem this prototype exists to fix (CURRENT_SYSTEM_AUDIT F1),
// reproduced by accident in the prototype's own first draft. Brightened
// here, verified by a full, non-zoomed screenshot afterward.
export const stage7BodyMaterial = new THREE.MeshStandardMaterial({
  color: new THREE.Color("#5C7F89"),
  roughness: 0.58,
  metalness: 0.05,
  emissive: new THREE.Color("#16262b"),
  emissiveIntensity: 0.22,
});

export const stage7JointMaterial = new THREE.MeshStandardMaterial({
  color: new THREE.Color("#4A6971"),
  roughness: 0.6,
  metalness: 0.05,
  emissive: new THREE.Color("#16262b"),
  emissiveIntensity: 0.22,
});

/** Strictly subordinate — low opacity, never the dominant visual (CURRENT_SYSTEM_AUDIT F1). */
export const stage7LatticeMaterial = new THREE.MeshBasicMaterial({
  color: new THREE.Color("#6FA6A0"),
  wireframe: true,
  transparent: true,
  opacity: 0.07,
});

export const STAGE7_KEY_LIGHT_COLOR = "#E7F3F1";
export const STAGE7_RIM_LIGHT_COLOR = "#6FC9BE";

/** One reusable anchor-marker material per modality color, keyed so it is created once, not per anchor per render. */
const anchorMaterialCache = new Map<string, THREE.MeshStandardMaterial>();
export function stage7AnchorMaterial(hex: string): THREE.MeshStandardMaterial {
  const cached = anchorMaterialCache.get(hex);
  if (cached) return cached;
  const material = new THREE.MeshStandardMaterial({
    color: new THREE.Color(hex),
    roughness: 0.35,
    metalness: 0.1,
    emissive: new THREE.Color(hex),
    emissiveIntensity: 0.35,
  });
  anchorMaterialCache.set(hex, material);
  return material;
}

/** Region-focus outline — a single reusable material, color-neutral (focus is a UI state, never a modality-colored claim). */
export const stage7RegionFocusMaterial = new THREE.MeshBasicMaterial({
  color: new THREE.Color("#F2C265"),
  wireframe: true,
  transparent: true,
  opacity: 0.55,
});
