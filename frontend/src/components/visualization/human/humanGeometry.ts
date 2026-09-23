/**
 * Pure joint/segment geometry for the volumetric mannequin (master prompt 3A
 * §5). Internal joints exist only to position volumetric capsule/sphere
 * meshes — the body is never rendered as lines connecting these points.
 * Proportions: head ≈ 1/7.5 of total height (~1.78m modeled height, head
 * sphere diameter ≈ 0.24), shoulder width ≈ 2.7 head widths, elbows near
 * waist height, wrists near upper-thigh height, symmetric neutral stance,
 * arms offset from torso so wrist sensors stay visible.
 */

export interface Vec3Tuple {
  x: number;
  y: number;
  z: number;
}

export const JOINTS = {
  head: { x: 0, y: 1.64, z: 0 },
  neckBase: { x: 0, y: 1.49, z: 0 },
  chest: { x: 0, y: 1.37, z: 0 },
  shoulderL: { x: -0.21, y: 1.45, z: 0 },
  shoulderR: { x: 0.21, y: 1.45, z: 0 },
  elbowL: { x: -0.31, y: 1.1, z: 0.03 },
  elbowR: { x: 0.31, y: 1.1, z: 0.03 },
  wristL: { x: -0.34, y: 0.84, z: 0.07 },
  wristR: { x: 0.34, y: 0.84, z: 0.07 },
  handEndL: { x: -0.35, y: 0.73, z: 0.09 },
  handEndR: { x: 0.35, y: 0.73, z: 0.09 },
  waist: { x: 0, y: 1.02, z: 0 },
  pelvis: { x: 0, y: 0.87, z: 0 },
  hipL: { x: -0.11, y: 0.84, z: 0 },
  hipR: { x: 0.11, y: 0.84, z: 0 },
  kneeL: { x: -0.12, y: 0.44, z: 0.01 },
  kneeR: { x: 0.12, y: 0.44, z: 0.01 },
  ankleL: { x: -0.12, y: 0.08, z: 0 },
  ankleR: { x: 0.12, y: 0.08, z: 0 },
  footTipL: { x: -0.12, y: 0.02, z: 0.13 },
  footTipR: { x: 0.12, y: 0.02, z: 0.13 },
} as const satisfies Record<string, Vec3Tuple>;

export type JointName = keyof typeof JOINTS;

export interface CapsuleSegment {
  id: string;
  from: Vec3Tuple;
  to: Vec3Tuple;
  radius: number;
  /** Non-uniform width/depth scale applied around the segment's own axis, for torso/pelvis flattening. */
  scale?: readonly [number, number];
}

export const HEAD_RADIUS = 0.115;

export const BODY_SEGMENTS: CapsuleSegment[] = [
  { id: "neck", from: JOINTS.neckBase, to: { ...JOINTS.head, y: JOINTS.head.y - HEAD_RADIUS * 0.7 }, radius: 0.05 },
  { id: "torsoUpper", from: JOINTS.chest, to: JOINTS.waist, radius: 0.165, scale: [1.18, 0.72] },
  { id: "torsoLower", from: JOINTS.waist, to: JOINTS.pelvis, radius: 0.14, scale: [1.15, 0.75] },
  { id: "pelvis", from: JOINTS.hipL, to: JOINTS.hipR, radius: 0.1, scale: [1, 1.35] },
  { id: "upperArmL", from: JOINTS.shoulderL, to: JOINTS.elbowL, radius: 0.055 },
  { id: "upperArmR", from: JOINTS.shoulderR, to: JOINTS.elbowR, radius: 0.055 },
  { id: "forearmL", from: JOINTS.elbowL, to: JOINTS.wristL, radius: 0.045 },
  { id: "forearmR", from: JOINTS.elbowR, to: JOINTS.wristR, radius: 0.045 },
  { id: "handL", from: JOINTS.wristL, to: JOINTS.handEndL, radius: 0.032 },
  { id: "handR", from: JOINTS.wristR, to: JOINTS.handEndR, radius: 0.032 },
  { id: "thighL", from: JOINTS.hipL, to: JOINTS.kneeL, radius: 0.08 },
  { id: "thighR", from: JOINTS.hipR, to: JOINTS.kneeR, radius: 0.08 },
  { id: "shinL", from: JOINTS.kneeL, to: JOINTS.ankleL, radius: 0.06 },
  { id: "shinR", from: JOINTS.kneeR, to: JOINTS.ankleR, radius: 0.06 },
  { id: "footL", from: JOINTS.ankleL, to: JOINTS.footTipL, radius: 0.045 },
  { id: "footR", from: JOINTS.ankleR, to: JOINTS.footTipR, radius: 0.045 },
];

export const SHOULDER_JOINT_RADIUS = 0.062;

/** Overall modeled figure height, head top to foot sole — used for camera framing. */
export const FIGURE_HEIGHT = JOINTS.head.y + HEAD_RADIUS;

// Prompt 3A.2 §6 — exact vertical/horizontal bounds of the rendered figure,
// used by the deterministic orthographic fit (humanLayout.computeOrthographicFit).
/** Lowest rendered point (foot sole). */
export const FIGURE_MIN_Y = JOINTS.footTipR.y;
/** Highest rendered point (top of the head sphere). */
export const FIGURE_MAX_Y = FIGURE_HEIGHT;
/** Visible vertical extent, foot sole to head top. */
export const FIGURE_TOTAL_HEIGHT = FIGURE_MAX_Y - FIGURE_MIN_Y;
/** Vertical centre of the visible figure (camera look-at target height). */
export const FIGURE_CENTER_Y = (FIGURE_MAX_Y + FIGURE_MIN_Y) / 2;
/**
 * Worst-case projected half-width across a full 360° Y rotation. The widest
 * silhouette is front/back-on (shoulders + arms at the sides, wristR.x 0.34 +
 * hand radius); a small margin is added so a three-quarter marker never
 * clips. Used by the orthographic fit's horizontal safety check so the figure
 * is guaranteed fully framed at every rotation angle (Digital Twin §8.4).
 */
export const FIGURE_HALF_WIDTH = 0.44;

export function isFiniteVec3(v: Vec3Tuple): boolean {
  return Number.isFinite(v.x) && Number.isFinite(v.y) && Number.isFinite(v.z);
}

export interface SegmentTransform {
  position: [number, number, number];
  /** [x, y, z, w] */
  quaternion: [number, number, number, number];
  length: number;
}

/**
 * Pure midpoint/orientation/length transform for placing a capsule mesh
 * along a from→to joint pair (master prompt 3A §20 "no NaN transformation").
 * Uses three.js's math-only Vector3/Quaternion (no DOM/WebGL dependency),
 * so this is safe to exercise from the plain node verify script. Degenerate
 * zero-length segments fail closed to a finite identity transform rather
 * than producing NaN from a zero-vector normalize.
 */
export function computeSegmentTransform(from: Vec3Tuple, to: Vec3Tuple): SegmentTransform {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const dz = to.z - from.z;
  const length = Math.sqrt(dx * dx + dy * dy + dz * dz);
  const position: [number, number, number] = [(from.x + to.x) / 2, (from.y + to.y) / 2, (from.z + to.z) / 2];

  if (length < 1e-6) {
    return { position, quaternion: [0, 0, 0, 1], length: 0 };
  }

  const nx = dx / length;
  const ny = dy / length;
  const nz = dz / length;
  // Rotation from (0,1,0) to (nx,ny,nz) via cross/dot, matching
  // THREE.Quaternion.setFromUnitVectors without requiring a THREE import.
  const dot = ny; // (0,1,0) · (nx,ny,nz)
  if (dot > 1 - 1e-9) return { position, quaternion: [0, 0, 0, 1], length };
  if (dot < -1 + 1e-9) return { position, quaternion: [1, 0, 0, 0], length };
  // (0,1,0) × (nx,ny,nz) = (1*nz - 0*ny, 0*nx - 0*nz, 0*ny - 1*nx) = (nz, 0, -nx)
  const cx = nz;
  const cz = -nx;
  const w = 1 + dot;
  const qLen = Math.sqrt(cx * cx + cz * cz + w * w);
  return { position, quaternion: [cx / qLen, 0, cz / qLen, w / qLen], length };
}
