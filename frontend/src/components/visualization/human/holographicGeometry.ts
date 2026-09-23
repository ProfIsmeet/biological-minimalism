import type { Vec3Tuple } from "@/components/visualization/human/humanGeometry";

/**
 * Prompt 3B §6.1 — improved human proportions. The 3A capsule mannequin read
 * as a "construction robot": spherical shoulders, a rectangular torso, an
 * oversized capsule belly. This geometry uses tapered segments (cylinders
 * with distinct end radii) plus a smaller head, a real neck, a sloped
 * shoulder line, a tapered torso narrowing at the waist, a clear pelvis,
 * tapered arms/legs, and small hand/foot forms, so the silhouette reads
 * immediately as a human body rather than a toy.
 *
 * Local space, y-up, feet near y=0, head top near y≈1.79 (≈ a 1.79m figure).
 */
export const H_JOINTS = {
  headTop: { x: 0, y: 1.79, z: 0 },
  headCenter: { x: 0, y: 1.68, z: 0.01 },
  neckTop: { x: 0, y: 1.585, z: 0 },
  neckBase: { x: 0, y: 1.5, z: 0 },
  shoulderCenter: { x: 0, y: 1.5, z: 0 },
  shoulderL: { x: -0.185, y: 1.49, z: 0 },
  shoulderR: { x: 0.185, y: 1.49, z: 0 },
  chest: { x: 0, y: 1.35, z: 0 },
  waist: { x: 0, y: 1.06, z: 0 },
  pelvisTop: { x: 0, y: 0.98, z: 0 },
  pelvis: { x: 0, y: 0.9, z: 0 },
  hipL: { x: -0.1, y: 0.9, z: 0 },
  hipR: { x: 0.1, y: 0.9, z: 0 },
  elbowL: { x: -0.235, y: 1.18, z: 0.02 },
  elbowR: { x: 0.235, y: 1.18, z: 0.02 },
  wristL: { x: -0.255, y: 0.9, z: 0.05 },
  wristR: { x: 0.255, y: 0.9, z: 0.05 },
  handL: { x: -0.262, y: 0.79, z: 0.06 },
  handR: { x: 0.262, y: 0.79, z: 0.06 },
  kneeL: { x: -0.105, y: 0.5, z: 0.02 },
  kneeR: { x: 0.105, y: 0.5, z: 0.02 },
  ankleL: { x: -0.1, y: 0.07, z: -0.01 },
  ankleR: { x: 0.1, y: 0.07, z: -0.01 },
  footL: { x: -0.1, y: 0.03, z: 0.11 },
  footR: { x: 0.1, y: 0.03, z: 0.11 },
} as const satisfies Record<string, Vec3Tuple>;

export const H_HEAD_RADIUS = 0.098;

export interface TaperedSegment {
  id: string;
  from: Vec3Tuple;
  to: Vec3Tuple;
  /** radius at `from` end. */
  rFrom: number;
  /** radius at `to` end. */
  rTo: number;
  /** non-uniform [x, z] scale for elliptical cross-sections (torso is wider than deep). */
  scale?: readonly [number, number];
}

// Tapered body segments. Torso pieces use an elliptical (wider-than-deep)
// cross-section; limbs taper from proximal to distal.
export const H_SEGMENTS: TaperedSegment[] = [
  { id: "neck", from: H_JOINTS.neckBase, to: H_JOINTS.neckTop, rFrom: 0.045, rTo: 0.04 },
  // Sloped shoulder yoke.
  { id: "yokeL", from: H_JOINTS.shoulderCenter, to: H_JOINTS.shoulderL, rFrom: 0.075, rTo: 0.055, scale: [1, 0.8] },
  { id: "yokeR", from: H_JOINTS.shoulderCenter, to: H_JOINTS.shoulderR, rFrom: 0.075, rTo: 0.055, scale: [1, 0.8] },
  // Torso: chest (broad) tapering to waist (narrow), then a distinct pelvis.
  { id: "upperTorso", from: H_JOINTS.shoulderCenter, to: H_JOINTS.chest, rFrom: 0.15, rTo: 0.145, scale: [1.32, 0.66] },
  { id: "midTorso", from: H_JOINTS.chest, to: H_JOINTS.waist, rFrom: 0.145, rTo: 0.108, scale: [1.24, 0.64] },
  { id: "pelvis", from: H_JOINTS.waist, to: H_JOINTS.pelvis, rFrom: 0.11, rTo: 0.135, scale: [1.28, 0.66] },
  // Arms.
  { id: "upperArmL", from: H_JOINTS.shoulderL, to: H_JOINTS.elbowL, rFrom: 0.052, rTo: 0.04 },
  { id: "upperArmR", from: H_JOINTS.shoulderR, to: H_JOINTS.elbowR, rFrom: 0.052, rTo: 0.04 },
  { id: "forearmL", from: H_JOINTS.elbowL, to: H_JOINTS.wristL, rFrom: 0.04, rTo: 0.028 },
  { id: "forearmR", from: H_JOINTS.elbowR, to: H_JOINTS.wristR, rFrom: 0.04, rTo: 0.028 },
  { id: "handL", from: H_JOINTS.wristL, to: H_JOINTS.handL, rFrom: 0.03, rTo: 0.018, scale: [1, 0.55] },
  { id: "handR", from: H_JOINTS.wristR, to: H_JOINTS.handR, rFrom: 0.03, rTo: 0.018, scale: [1, 0.55] },
  // Legs.
  { id: "thighL", from: H_JOINTS.hipL, to: H_JOINTS.kneeL, rFrom: 0.088, rTo: 0.058 },
  { id: "thighR", from: H_JOINTS.hipR, to: H_JOINTS.kneeR, rFrom: 0.088, rTo: 0.058 },
  { id: "shinL", from: H_JOINTS.kneeL, to: H_JOINTS.ankleL, rFrom: 0.056, rTo: 0.036 },
  { id: "shinR", from: H_JOINTS.kneeR, to: H_JOINTS.ankleR, rFrom: 0.056, rTo: 0.036 },
  { id: "footL", from: H_JOINTS.ankleL, to: H_JOINTS.footL, rFrom: 0.045, rTo: 0.03, scale: [1, 1.4] },
  { id: "footR", from: H_JOINTS.ankleR, to: H_JOINTS.footR, rFrom: 0.045, rTo: 0.03, scale: [1, 1.4] },
];

/** Figure vertical bounds for the orthographic fit. */
export const H_FIGURE_MIN_Y = 0.0;
export const H_FIGURE_MAX_Y = H_JOINTS.headTop.y;
export const H_FIGURE_TOTAL_HEIGHT = H_FIGURE_MAX_Y - H_FIGURE_MIN_Y;
export const H_FIGURE_CENTER_Y = (H_FIGURE_MAX_Y + H_FIGURE_MIN_Y) / 2;
export const H_FIGURE_HALF_WIDTH = 0.42;

export interface ScanRingLevel {
  id: string;
  /** vertical world position. */
  y: number;
  /** ellipse radii (x horizontal, z depth). */
  radiusX: number;
  radiusZ: number;
  opacity: number;
}

/**
 * Prompt 3B §6.3 — 7 horizontal scan rings at meaningful body levels. Purely a
 * spatial visualization scaffold: no ring encodes any number, health, or
 * confidence value.
 */
// §3C.2 §3.7 — the previous "head" ring (y=1.66, radiusX=0.17, opacity=0.34)
// sat at head-CENTER height at ~1.7x the head's own radius (H_HEAD_RADIUS =
// 0.098) and near-maximum opacity — a wide, bright, opaque ellipse straddling
// the skull reads exactly as a hat brim. The previous "pelvis" ring
// (y=0.86) sat almost exactly on the anatomical hip line, reading as a belt.
// Rings are now: repositioned so none coincides with a prominent body-mesh
// loft ring (crown, shoulder, hip lines), sized closer to the body's own
// radius at that height rather than far wider, and reduced to the requested
// 0.10-0.22 opacity band throughout so the shell stays visually primary.
export const H_SCAN_RINGS: ScanRingLevel[] = [
  { id: "crownHalo", y: 1.85, radiusX: 0.12, radiusZ: 0.1, opacity: 0.16 },
  { id: "upperChest", y: 1.44, radiusX: 0.22, radiusZ: 0.16, opacity: 0.14 },
  { id: "lowerChest", y: 1.2, radiusX: 0.21, radiusZ: 0.15, opacity: 0.13 },
  { id: "abdomen", y: 1.0, radiusX: 0.19, radiusZ: 0.14, opacity: 0.12 },
  { id: "thigh", y: 0.72, radiusX: 0.17, radiusZ: 0.13, opacity: 0.13 },
  { id: "knees", y: 0.44, radiusX: 0.16, radiusZ: 0.12, opacity: 0.13 },
  { id: "feet", y: 0.04, radiusX: 0.19, radiusZ: 0.16, opacity: 0.17 },
];

/** Sensor contact positions on the holographic figure (operational stage only). */
export const H_CONTACT_POSITION: Record<string, readonly [number, number, number]> = {
  EEG: [-0.045, H_JOINTS.headCenter.y + 0.02, H_HEAD_RADIUS * 0.92],
  EOG: [0.05, H_JOINTS.headCenter.y - 0.03, H_HEAD_RADIUS * 0.94],
  ECG: [0, H_JOINTS.chest.y - 0.03, 0.14],
  // §3C.3 §7 — the anatomical wrist was abducted to x≈0.305 (anatomicalHumanGeometry.ts);
  // these wrist contacts are pinned to the new wrist so PPG/IMU stay on the body,
  // not floating at the old x≈0.258 position. (H_JOINTS is legacy scaffolding for
  // the retired segment mesh and no longer matches the rendered wrist.)
  PPG: [0.315, 0.925, 0.072],
  IMU: [0.298, 0.895, 0.06],
};
