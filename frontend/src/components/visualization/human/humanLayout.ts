import { FIGURE_CENTER_Y, FIGURE_HALF_WIDTH, FIGURE_TOTAL_HEIGHT, HEAD_RADIUS, JOINTS } from "@/components/visualization/human/humanGeometry";
import type { SensorAnchorModel } from "@/components/visualization/human/types";
import { FINAL_SENSOR_INVENTORY, MODALITY_COLOR, type FinalModality, type FinalRegion } from "@/lib/architecture";
import type { ModalityNodeState, OperationalStateWord } from "@/lib/monitoring/modalityNodeState";

/**
 * On-body sensor contact-marker positions (master prompt 3A §6/§7, Prompt 3A.2
 * §5.1). As of Prompt 3A.2 these drive only the small 3D contact-marker
 * spheres — the interactive sensor buttons and text now live in a DOM overlay
 * (OperationalAvatarOverlay), so these positions no longer need the manual
 * anti-collision offsets the earlier passes fought with; they are simply the
 * honest anatomical points on the body. PPG and IMU sit on the same wrist
 * (two sensors on one wristband), so their markers are legitimately close.
 * Positions are in the same local mannequin space as humanGeometry.ts.
 */
export const MODALITY_ANCHOR_POSITION: Record<FinalModality, readonly [number, number, number]> = {
  EEG: [-0.05, JOINTS.head.y + 0.02, HEAD_RADIUS * 0.9],
  EOG: [0.05, JOINTS.head.y - 0.035, HEAD_RADIUS * 0.95],
  ECG: [0, JOINTS.chest.y, 0.16],
  PPG: [JOINTS.wristR.x + 0.01, JOINTS.wristR.y + 0.02, JOINTS.wristR.z + 0.03],
  IMU: [JOINTS.wristR.x - 0.02, JOINTS.wristR.y - 0.03, JOINTS.wristR.z + 0.02],
};

export interface RegionOrbitDef {
  id: "frontal" | "chest" | "wrist";
  label: string;
  center: readonly [number, number, number];
  radiusX: number;
  radiusY: number;
}

export const REGION_ORBITS: RegionOrbitDef[] = [
  { id: "frontal", label: "FRONTAL MODULE", center: [0, JOINTS.head.y, 0], radiusX: HEAD_RADIUS * 1.9, radiusY: HEAD_RADIUS * 1.6 },
  { id: "chest", label: "CHEST MODULE", center: [0, JOINTS.chest.y, 0], radiusX: 0.34, radiusY: 0.26 },
  { id: "wrist", label: "WRIST MODULE", center: [JOINTS.wristR.x, JOINTS.wristR.y, JOINTS.wristR.z], radiusX: 0.16, radiusY: 0.13 },
];

/**
 * Prompt 3A.2 §6 — orthographic technical-view camera. Orthographic (parallel)
 * projection gives *deterministic* framing: the figure's on-screen size is set
 * purely by the frustum bounds, independent of camera distance, and there is
 * no perspective parallax to make extremities clip unpredictably as the figure
 * rotates. This replaces the 3A.1 perspective `resolveResponsiveDistance`
 * approach, which solved clipping by zooming out so far the figure became
 * visually insignificant.
 *
 * Fixed three-quarter angle (azimuth/elevation); `distance` only affects
 * near/far clipping under orthographic projection, not scale.
 */
export const ORTHO_VIEW = { azimuthDeg: 24, elevationDeg: 6, distance: 8 } as const;

export const ORTHO_TARGET: [number, number, number] = [0, FIGURE_CENTER_Y, 0];

export interface OrthographicFrustum {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

/**
 * Deterministic orthographic frustum that frames the figure as LARGE as
 * possible while keeping it fully inside the canvas, centred, from the actual
 * figure bounds (humanGeometry). It takes the tighter of two constraints:
 *
 *   - a height cap (`maxHeightFraction`): the figure never exceeds this
 *     fraction of the canvas height;
 *   - a width fit: the figure's worst-case projected width (`halfWidth`) plus
 *     side margins always fits the canvas width.
 *
 * `viewH = max(heightConstraint, widthConstraint)` — the larger view box is
 * the one that satisfies both, and it is exactly as large as needed and no
 * larger, so a tall/narrow canvas fills to its width (figure large) and a
 * wide canvas fills to the height cap. This replaces the 3A.1 perspective
 * "zoom out with a hard scale cap" that shrank the figure to insignificance.
 */
export function computeOrthographicFit(
  aspect: number,
  maxHeightFraction: number,
  options?: { halfWidth?: number; marginFraction?: number; totalHeight?: number },
): OrthographicFrustum {
  const safeAspect = Number.isFinite(aspect) && aspect > 0 ? aspect : 1;
  const safeFraction = Number.isFinite(maxHeightFraction) && maxHeightFraction > 0 ? Math.min(0.92, maxHeightFraction) : 0.72;
  const halfWidth = options?.halfWidth ?? FIGURE_HALF_WIDTH;
  const marginFraction = options?.marginFraction ?? 0.08;
  const totalHeight = options?.totalHeight ?? FIGURE_TOTAL_HEIGHT;
  const viewHForHeight = totalHeight / safeFraction;
  const viewWForWidth = (halfWidth * 2) / Math.max(0.02, 1 - 2 * marginFraction);
  const viewHForWidth = viewWForWidth / safeAspect;
  const viewH = Math.max(viewHForHeight, viewHForWidth);
  const viewW = viewH * safeAspect;
  // Bounds are in CAMERA space, centred on the look-at target (which the rig
  // points at FIGURE_CENTER_Y). They must be symmetric about 0 — offsetting
  // top/bottom by FIGURE_CENTER_Y would double-apply the vertical centre and
  // push the figure to the bottom of the frame.
  return {
    left: -viewW / 2,
    right: viewW / 2,
    top: viewH / 2,
    bottom: -viewH / 2,
  };
}

/** Orthographic camera world position for the fixed three-quarter view. */
export function orthoCameraPosition(view: { azimuthDeg: number; elevationDeg: number; distance: number } = ORTHO_VIEW): [number, number, number] {
  const az = (view.azimuthDeg * Math.PI) / 180;
  const el = (view.elevationDeg * Math.PI) / 180;
  const horizontal = view.distance * Math.cos(el);
  return [horizontal * Math.sin(az), FIGURE_CENTER_Y + view.distance * Math.sin(el), horizontal * Math.cos(az)];
}

export interface ModalityStateInput {
  modality: FinalModality;
  region: FinalRegion;
  nodeState: ModalityNodeState;
  stateLabel: OperationalStateWord;
  statusLabel: string;
}

/**
 * Pure presentation-model mapping (master prompt 3A §19) from operational
 * modality state to 3D sensor anchors — split out of
 * OperationalPhysiologyStage.tsx so scripts/verify-monitoring-state.ts can
 * assert exactly 5 anchors, no duplicate modality, and a finite position for
 * every one of them, independent of React/WebGL.
 */
export function buildSensorAnchors(entries: ModalityStateInput[], selectedModality: FinalModality): SensorAnchorModel[] {
  return entries.map((entry) => ({
    modality: entry.modality,
    region: entry.region,
    position: MODALITY_ANCHOR_POSITION[entry.modality],
    state: entry.nodeState,
    stateLabel: entry.stateLabel,
    selected: entry.modality === selectedModality,
    color: MODALITY_COLOR[entry.modality],
    detail: entry.statusLabel,
  }));
}

/** Every final-architecture modality, in canonical ledger order — used to assert anchor-mapping completeness. */
export const ALL_FINAL_MODALITIES: FinalModality[] = FINAL_SENSOR_INVENTORY.map((entry) => entry.modality);
