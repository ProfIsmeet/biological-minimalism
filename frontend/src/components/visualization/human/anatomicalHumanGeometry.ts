/**
 * Prompt 3C/3C.1 §8 — anatomical holographic human.
 *
 * The 3A/3B figure was assembled from separate tapered `cylinderGeometry`
 * segments: the torso read as three stacked pipes and every joint showed a
 * seam. This module replaces that with an ORIGINAL merged multi-part
 * procedural anatomical display mesh: the torso itself is one lofted volume
 * (§8.1, a single ordered run of elliptical cross-section rings), each limb is
 * one lofted tube that bends smoothly via parallel-transport frames (§8.3),
 * and the head is an elongated low-poly skull rather than a perfect sphere
 * (§8.2) — but the torso, head, and four limbs are six independently-lofted
 * parts concatenated into one draw buffer by `mergeMeshArrays()`, not a single
 * watertight or boolean-unioned surface. A shared draw call is not the same
 * claim as topological continuity; §3C.1 removed the limb-root end caps that
 * used to sit embedded inside the torso volume (visible through the
 * translucent shell as bright internal discs) precisely because those parts
 * are genuinely separate volumes overlapping in space, not welded together.
 *
 * Pure geometry only — NO `three` import, no DOM, no React — so
 * scripts/verify-monitoring-state.ts can exercise it in plain node and assert
 * finite, NaN-free position/normal/index buffers (§30). A thin React helper
 * (`buildBufferGeometry`) turns these arrays into THREE.BufferGeometry.
 *
 * Local space: y-up, feet sole at y≈0, crown at y≈1.79 (a ~1.79 m figure),
 * front is +z. This matches holographicGeometry.ts joints/contacts/scan rings.
 */

export type Vec3 = readonly [number, number, number];

export interface MeshArrays {
  /** flat xyz triples */
  positions: Float32Array;
  /** flat xyz triples, per-vertex smooth normals */
  normals: Float32Array;
  /** triangle indices */
  indices: Uint32Array;
}

/** A single lofted cross-section: an ellipse in the plane spanned by `right`/`up`. */
export interface LoftRing {
  center: Vec3;
  /** unit vector, ellipse extends ±radiusA along here */
  right: Vec3;
  /** unit vector, ellipse extends ±radiusB along here */
  up: Vec3;
  radiusA: number;
  radiusB: number;
}

// ---------- tiny pure vector helpers (no three dependency) ----------
const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const scale = (a: Vec3, s: number): Vec3 => [a[0] * s, a[1] * s, a[2] * s];
const dot = (a: Vec3, b: Vec3): number => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: Vec3, b: Vec3): Vec3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
function norm(a: Vec3): Vec3 {
  const l = Math.hypot(a[0], a[1], a[2]);
  if (l < 1e-9) return [0, 0, 0];
  return [a[0] / l, a[1] / l, a[2] / l];
}

/**
 * Loft a smooth tube through an ordered list of elliptical rings and return an
 * indexed triangle mesh with smooth per-vertex normals. Optional flat caps
 * close the first/last ring so the body volume reads as solid from any angle.
 */
export function loftRings(rings: LoftRing[], radialSegments: number, opts?: { capStart?: boolean; capEnd?: boolean }): MeshArrays {
  const seg = Math.max(3, Math.floor(radialSegments));
  const ringCount = rings.length;
  const ringVerts = seg; // ring is closed: vertex `seg` wraps to vertex 0
  const capStart = opts?.capStart ?? false;
  const capEnd = opts?.capEnd ?? false;

  const positions: number[] = [];

  // Ring vertices.
  for (let r = 0; r < ringCount; r++) {
    const ring = rings[r]!;
    for (let i = 0; i < ringVerts; i++) {
      const theta = (i / ringVerts) * Math.PI * 2;
      const ca = Math.cos(theta) * ring.radiusA;
      const cb = Math.sin(theta) * ring.radiusB;
      const px = ring.center[0] + ring.right[0] * ca + ring.up[0] * cb;
      const py = ring.center[1] + ring.right[1] * ca + ring.up[1] * cb;
      const pz = ring.center[2] + ring.right[2] * ca + ring.up[2] * cb;
      positions.push(px, py, pz);
    }
  }

  const indices: number[] = [];
  // Side quads between consecutive rings.
  for (let r = 0; r < ringCount - 1; r++) {
    const base = r * ringVerts;
    const next = (r + 1) * ringVerts;
    for (let i = 0; i < ringVerts; i++) {
      const i2 = (i + 1) % ringVerts;
      const a = base + i;
      const b = base + i2;
      const c = next + i2;
      const d = next + i;
      // outward winding (CCW seen from outside)
      indices.push(a, d, c);
      indices.push(a, c, b);
    }
  }

  // Caps (center-fan). Added after ring verts so ring indices stay stable.
  if (capStart && ringCount > 0) {
    const c = rings[0]!.center;
    const centerIdx = positions.length / 3;
    positions.push(c[0], c[1], c[2]);
    for (let i = 0; i < ringVerts; i++) {
      const i2 = (i + 1) % ringVerts;
      indices.push(centerIdx, i, i2);
    }
  }
  if (capEnd && ringCount > 0) {
    const c = rings[ringCount - 1]!.center;
    const base = (ringCount - 1) * ringVerts;
    const centerIdx = positions.length / 3;
    positions.push(c[0], c[1], c[2]);
    for (let i = 0; i < ringVerts; i++) {
      const i2 = (i + 1) % ringVerts;
      indices.push(centerIdx, base + i2, base + i);
    }
  }

  const posArr = new Float32Array(positions);
  const idxArr = new Uint32Array(indices);
  const normals = computeSmoothNormals(posArr, idxArr);
  return { positions: posArr, normals, indices: idxArr };
}

/** Angle-free smooth normals: accumulate face normals per vertex, then normalize. */
export function computeSmoothNormals(positions: Float32Array, indices: Uint32Array): Float32Array {
  const normals = new Float32Array(positions.length);
  for (let t = 0; t < indices.length; t += 3) {
    const ia = indices[t]! * 3;
    const ib = indices[t + 1]! * 3;
    const ic = indices[t + 2]! * 3;
    const ax = positions[ia]!, ay = positions[ia + 1]!, az = positions[ia + 2]!;
    const bx = positions[ib]!, by = positions[ib + 1]!, bz = positions[ib + 2]!;
    const cx = positions[ic]!, cy = positions[ic + 1]!, cz = positions[ic + 2]!;
    const e1x = bx - ax, e1y = by - ay, e1z = bz - az;
    const e2x = cx - ax, e2y = cy - ay, e2z = cz - az;
    const nx = e1y * e2z - e1z * e2y;
    const ny = e1z * e2x - e1x * e2z;
    const nz = e1x * e2y - e1y * e2x;
    normals[ia]! += nx; normals[ia + 1]! += ny; normals[ia + 2]! += nz;
    normals[ib]! += nx; normals[ib + 1]! += ny; normals[ib + 2]! += nz;
    normals[ic]! += nx; normals[ic + 1]! += ny; normals[ic + 2]! += nz;
  }
  for (let i = 0; i < normals.length; i += 3) {
    const l = Math.hypot(normals[i]!, normals[i + 1]!, normals[i + 2]!);
    if (l > 1e-9) {
      normals[i]! /= l; normals[i + 1]! /= l; normals[i + 2]! /= l;
    } else {
      normals[i] = 0; normals[i + 1] = 1; normals[i + 2] = 0;
    }
  }
  return normals;
}

// ---------- limb lofting with parallel-transport frames (§8.3) ----------

export interface LimbNode {
  point: Vec3;
  radius: number;
  /** flatten factor applied to the depth (up) axis: 1 = round, <1 = flattened (hands/feet). */
  flatten?: number;
}

/**
 * Loft a limb (arm/leg/hand/foot) as ONE continuous tube through a bent
 * polyline, using parallel-transport frames so consecutive rings do not twist
 * and elbow/knee bends stay smooth (no disconnected-pipe seam, §8.3).
 */
export function buildLimb(nodes: LimbNode[], radialSegments: number, opts?: { capStart?: boolean; capEnd?: boolean }): MeshArrays {
  const n = nodes.length;
  const tangents: Vec3[] = [];
  for (let i = 0; i < n; i++) {
    let t: Vec3;
    if (i === 0) t = sub(nodes[1]!.point, nodes[0]!.point);
    else if (i === n - 1) t = sub(nodes[n - 1]!.point, nodes[n - 2]!.point);
    else t = sub(nodes[i + 1]!.point, nodes[i - 1]!.point);
    const nt = norm(t);
    tangents.push(nt[0] === 0 && nt[1] === 0 && nt[2] === 0 ? [0, 1, 0] : nt);
  }

  // Initial frame: pick a reference not parallel to t0.
  const t0 = tangents[0]!;
  const refUp: Vec3 = Math.abs(t0[1]) > 0.9 ? [0, 0, 1] : [0, 1, 0];
  let right = norm(cross(refUp, t0));
  if (right[0] === 0 && right[1] === 0 && right[2] === 0) right = [1, 0, 0];
  let up = norm(cross(t0, right));

  const rings: LoftRing[] = [];
  for (let i = 0; i < n; i++) {
    const t = tangents[i]!;
    if (i > 0) {
      // parallel-transport `right` onto the plane perpendicular to the new tangent
      const projected = sub(right, scale(t, dot(t, right)));
      const rp = norm(projected);
      right = rp[0] === 0 && rp[1] === 0 && rp[2] === 0 ? right : rp;
      up = norm(cross(t, right));
    }
    const flat = nodes[i]!.flatten ?? 1;
    rings.push({ center: nodes[i]!.point, right, up, radiusA: nodes[i]!.radius, radiusB: nodes[i]!.radius * flat });
  }
  return loftRings(rings, radialSegments, opts);
}

/** Merge several meshes into one buffer set (single draw call for shell + wire). */
export function mergeMeshArrays(parts: MeshArrays[]): MeshArrays {
  let vCount = 0;
  let iCount = 0;
  for (const p of parts) {
    vCount += p.positions.length;
    iCount += p.indices.length;
  }
  const positions = new Float32Array(vCount);
  const normals = new Float32Array(vCount);
  const indices = new Uint32Array(iCount);
  let vOff = 0;
  let iOff = 0;
  let baseVert = 0;
  for (const p of parts) {
    positions.set(p.positions, vOff);
    normals.set(p.normals, vOff);
    for (let i = 0; i < p.indices.length; i++) indices[iOff + i] = p.indices[i]! + baseVert;
    baseVert += p.positions.length / 3;
    vOff += p.positions.length;
    iOff += p.indices.length;
  }
  return { positions, normals, indices };
}

// ================= anatomical profile =================

const TORSO_RADIAL = 22; // §8.1 "at least 18–24 radial segments"
const LIMB_RADIAL = 14;
const HEAD_RADIAL = 18;

const RIGHT: Vec3 = [1, 0, 0];
const DEPTH: Vec3 = [0, 0, 1];

/** Vertical elliptical cross-sections lofted into the torso's own single volume (§8.1). */
interface TorsoSection {
  y: number;
  z: number;
  rx: number; // half-width (x)
  rz: number; // half-depth (z)
}

// §3C.3 §6/§10 — gradual neck→clavicle→shoulder transition and an S-curve
// front/back (z) profile for real side-view depth. The 3C.2 torso jumped from
// neck rx=0.062 to shoulder rx=0.185 across 0.05 world units — a triangular
// "wing shelf". Three transitional clavicle rings now spread that expansion
// over 0.04 units. The z offsets push the chest slightly forward and the
// waist/pelvis slightly back so the side silhouette reads as a human S-curve
// (chest projection, lumbar/gluteal depth) rather than a flat column; the
// chest cross-section (rz 0.110) is visibly deeper than the waist (rz 0.087).
const TORSO_SECTIONS: TorsoSection[] = [
  { y: 1.525, z: 0.004, rx: 0.06, rz: 0.055 }, // neck base (top cap seat)
  { y: 1.505, z: 0.004, rx: 0.104, rz: 0.07 }, // inner clavicle
  { y: 1.485, z: 0.004, rx: 0.145, rz: 0.083 }, // mid clavicle
  { y: 1.46, z: 0.002, rx: 0.18, rz: 0.096 }, // outer shoulder line
  { y: 1.405, z: 0.012, rx: 0.17, rz: 0.11 }, // upper chest (projects forward)
  { y: 1.335, z: 0.012, rx: 0.156, rz: 0.11 }, // mid chest
  { y: 1.24, z: 0.006, rx: 0.14, rz: 0.102 }, // lower rib cage
  { y: 1.155, z: 0.0, rx: 0.124, rz: 0.093 }, // upper waist
  { y: 1.075, z: -0.004, rx: 0.112, rz: 0.087 }, // waist (narrowest, slight lumbar set-back)
  { y: 1.0, z: -0.006, rx: 0.136, rz: 0.1 }, // iliac expansion
  { y: 0.92, z: -0.01, rx: 0.15, rz: 0.114 }, // pelvis (deepest, gluteal rear volume)
  { y: 0.865, z: -0.006, rx: 0.138, rz: 0.106 }, // lower pelvis (narrows before thigh roots)
];

function torso(): MeshArrays {
  const rings: LoftRing[] = TORSO_SECTIONS.map((s) => ({
    center: [0, s.y, s.z] as Vec3,
    right: RIGHT,
    up: DEPTH,
    radiusA: s.rx,
    radiusB: s.rz,
  }));
  return loftRings(rings, TORSO_RADIAL, { capStart: true, capEnd: true });
}

/**
 * Elongated low-poly head (§8.2): cranial volume, narrower jaw/chin, subtle
 * front/back orientation (front bulge on +z), and a short neck transition.
 * Lofted from horizontal rings chin→crown.
 */
function head(): MeshArrays {
  const cy = 1.66; // head center
  // {dy from center, rx, rz, dz forward offset}
  const profile: Array<[number, number, number, number]> = [
    [-0.115, 0.03, 0.032, 0.012], // chin
    [-0.09, 0.052, 0.058, 0.016], // jaw
    [-0.055, 0.07, 0.079, 0.012], // cheek / mid face (front bulge)
    [-0.015, 0.079, 0.086, 0.004], // brow line
    [0.03, 0.082, 0.088, -0.004], // upper cranium
    [0.075, 0.066, 0.07, -0.006], // crown taper
    [0.108, 0.03, 0.03, -0.004], // top
  ];
  const rings: LoftRing[] = profile.map(([dy, rx, rz, dz]) => ({
    center: [0, cy + dy, dz] as Vec3,
    right: RIGHT,
    up: DEPTH,
    radiusA: rx,
    radiusB: rz,
  }));
  const skull = loftRings(rings, HEAD_RADIAL, { capStart: true, capEnd: true });
  // Neck transition (short lofted tube, blends head to shoulders).
  const neck = loftRings(
    [
      { center: [0, 1.5, 0.004], right: RIGHT, up: DEPTH, radiusA: 0.05, radiusB: 0.046 },
      { center: [0, 1.555, 0.006], right: RIGHT, up: DEPTH, radiusA: 0.046, radiusB: 0.044 },
      { center: [0, 1.6, 0.006], right: RIGHT, up: DEPTH, radiusA: 0.05, radiusB: 0.05 },
    ],
    HEAD_RADIAL,
  );
  return mergeMeshArrays([skull, neck]);
}

// §3C.3 §7 — neutral scan pose with ~14° abduction so the wrist reaches
// x≈0.305 (was 0.258), opening clear negative space between the upper arm and
// the rib cage and between the forearm/hand and the thigh. Deltoid bulges at
// the outer shoulder, the upper arm is fuller than the forearm, the elbow
// narrows, and the wrist is narrower than the hand palm below it.
function arm(side: -1 | 1): MeshArrays {
  const sx = side;
  const nodes: LimbNode[] = [
    { point: [sx * 0.158, 1.47, -0.002], radius: 0.056 }, // deltoid root (embeds into shoulder)
    { point: [sx * 0.198, 1.435, 0.0], radius: 0.052 }, // deltoid bulge / outer shoulder
    { point: [sx * 0.235, 1.3, 0.006], radius: 0.044 }, // upper arm (fuller)
    { point: [sx * 0.264, 1.165, 0.012], radius: 0.036 }, // elbow (narrower)
    { point: [sx * 0.29, 1.01, 0.026], radius: 0.032 }, // forearm
    { point: [sx * 0.305, 0.905, 0.042], radius: 0.026 }, // wrist (narrowest)
  ];
  // §3C.2 §3.5 — capped start: the deltoid root is embedded inside the
  // shoulder volume, and an open boundary there would be drawn as a bright
  // ring by any edge pass; the cap keeps the silhouette clean.
  const armMesh = buildLimb(nodes, LIMB_RADIAL, { capStart: true, capEnd: false });
  // §3C.3 §8 — hand as a flattened multi-ring palm, not a needle taper: wrist
  // → palm expansion (wider than wrist) → palm body → distal taper → rounded
  // terminal. Depth is flatter than the arm (flatten < arm) and it stays well
  // clear of the thigh (hand x≈0.31 vs thigh outer edge ≈0.18).
  const hand = buildLimb(
    [
      { point: [sx * 0.306, 0.892, 0.046], radius: 0.025, flatten: 0.5 }, // wrist edge
      { point: [sx * 0.309, 0.862, 0.055], radius: 0.038, flatten: 0.42 }, // palm expansion (wider than wrist)
      { point: [sx * 0.31, 0.828, 0.06], radius: 0.038, flatten: 0.4 }, // palm body
      { point: [sx * 0.31, 0.8, 0.062], radius: 0.026, flatten: 0.42 }, // distal taper
      { point: [sx * 0.309, 0.782, 0.063], radius: 0.013, flatten: 0.5 }, // rounded terminal
    ],
    LIMB_RADIAL,
    { capStart: false, capEnd: true },
  );
  return mergeMeshArrays([armMesh, hand]);
}

// §3C.3 §9 — two anatomically separate legs. The 3C.2 thigh roots (x=±0.088,
// r=0.096) overlapped through the centreline, fusing into a rectangular
// "shorts" block. The roots are now narrower (r=0.080) and set slightly wider
// (x=±0.098), leaving a clear ~0.036 crotch gap below the narrowed lower
// pelvis. The thigh is fuller than the knee, the calf carries a gentle volume
// peak before the narrow ankle, and the foot extends forward.
function leg(side: -1 | 1): MeshArrays {
  const sx = side;
  const nodes: LimbNode[] = [
    { point: [sx * 0.098, 0.865, -0.004], radius: 0.08 }, // hip root (embeds into lower pelvis)
    { point: [sx * 0.1, 0.79, 0.004], radius: 0.084 }, // upper thigh (fullest)
    { point: [sx * 0.104, 0.61, 0.01], radius: 0.066 }, // thigh
    { point: [sx * 0.105, 0.475, 0.014], radius: 0.049 }, // knee (narrower, not pinched)
    { point: [sx * 0.106, 0.36, 0.006], radius: 0.052 }, // calf (gentle volume peak)
    { point: [sx * 0.103, 0.23, -0.002], radius: 0.036 }, // lower shin
    { point: [sx * 0.1, 0.085, -0.01], radius: 0.032 }, // ankle (narrow)
  ];
  const legMesh = buildLimb(nodes, LIMB_RADIAL, { capStart: true, capEnd: false });
  // Foot: extends forward, flattened, individually readable.
  const foot = buildLimb(
    [
      { point: [sx * 0.1, 0.072, -0.028], radius: 0.038, flatten: 0.7 }, // heel
      { point: [sx * 0.1, 0.04, 0.02], radius: 0.05, flatten: 0.5 }, // arch
      { point: [sx * 0.1, 0.028, 0.09], radius: 0.05, flatten: 0.42 }, // forefoot
      { point: [sx * 0.1, 0.022, 0.145], radius: 0.034, flatten: 0.4 }, // toe
      { point: [sx * 0.1, 0.02, 0.175], radius: 0.015, flatten: 0.4 }, // toe end
    ],
    LIMB_RADIAL,
    { capStart: true, capEnd: true },
  );
  return mergeMeshArrays([legMesh, foot]);
}

export interface AnatomicalHuman {
  /** merged body volume (torso + neck + head + limbs) as one indexed mesh */
  body: MeshArrays;
}

/**
 * Build the six-part anatomical human (torso, head, two arms, two legs) and
 * concatenate them into one merged indexed mesh, so the shell and the edge-line
 * overlay share a single geometry (one upload, one draw per layer). This is a
 * merged multi-part display mesh, not a single continuous or watertight
 * surface — see the file header. Memoise the result at the call site — this
 * is deterministic.
 */
export function buildAnatomicalHuman(): AnatomicalHuman {
  const parts = [torso(), head(), arm(-1), arm(1), leg(-1), leg(1)];
  return { body: mergeMeshArrays(parts) };
}

/** Vertical bounds of the rendered figure (for orthographic framing). */
export const ANATOMY_MIN_Y = 0.0;
export const ANATOMY_MAX_Y = 1.79;
export const ANATOMY_CENTER_Y = (ANATOMY_MAX_Y + ANATOMY_MIN_Y) / 2;
export const ANATOMY_HALF_WIDTH = 0.34; // shoulders + arm offset + margin
