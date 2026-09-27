/**
 * Stage 7 prototype — thin wrapper around the existing, imported, unmodified
 * deterministic orthographic-framing math (humanLayout.ts's
 * computeOrthographicFit / orthoCameraPosition, and humanGeometry.ts's
 * figure-bounds constants). This file adds no new framing math; it only
 * supplies the prototype's own view-angle table (stage7PrototypeModel.ts)
 * to those existing functions.
 */

import { computeOrthographicFit, orthoCameraPosition, type OrthographicFrustum } from "@/components/visualization/human/humanLayout";
import { FIGURE_HALF_WIDTH, FIGURE_TOTAL_HEIGHT } from "@/components/visualization/human/humanGeometry";
import type { Stage7ViewDef } from "@/prototypes/stage7-digital-twin/types";

/** A small extra margin beyond the existing FIGURE_HALF_WIDTH default, since
 * the prototype's left/right/back views are full 90-180 degree rotations
 * (not just the product's fixed three-quarter angle), so the worst-case
 * projected width across all six prototype views must still fit. */
const STAGE7_FIT_OPTIONS = { halfWidth: FIGURE_HALF_WIDTH * 1.05, marginFraction: 0.1, totalHeight: FIGURE_TOTAL_HEIGHT };

export function stage7ComputeFrustum(aspect: number, heightFraction: number): OrthographicFrustum {
  return computeOrthographicFit(aspect, heightFraction, STAGE7_FIT_OPTIONS);
}

export function stage7CameraPosition(view: Stage7ViewDef, distance: number): [number, number, number] {
  return orthoCameraPosition({ azimuthDeg: view.azimuthDeg, elevationDeg: view.elevationDeg, distance });
}

export const STAGE7_CAMERA_DISTANCE = 8;
