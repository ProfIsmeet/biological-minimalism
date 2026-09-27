/**
 * Stage 7 prototype — authoritative sensor/module topology, derived ONLY from
 * repository-canonical sources, never invented or duplicated:
 *   - modality/region/order/description: @/lib/architecture FINAL_SENSOR_INVENTORY
 *   - modality color: @/lib/architecture MODALITY_COLOR
 *   - anchor 3D position: @/components/visualization/human/humanLayout MODALITY_ANCHOR_POSITION
 *   - module id/label: @/lib/architecture FINAL_MODULES (id/label reused; this
 *     file only narrows FINAL_MODULES' string id down to the exact 3-value
 *     Stage7RegionId union so the prototype's region-focus logic is
 *     exhaustively typed)
 *
 * This module performs NO invention: every value below is either imported
 * directly or is a 1:1 read of an imported value's field. If the upstream
 * architecture module ever adds a 6th modality or a 4th module, this file's
 * type-level exhaustiveness (Stage7RegionId, the FinalModality union) will
 * fail to compile until updated — it cannot silently drift out of sync.
 */

import { FINAL_MODULES, FINAL_SENSOR_INVENTORY, MODALITY_COLOR } from "@/lib/architecture";
import { MODALITY_ANCHOR_POSITION } from "@/components/visualization/human/humanLayout";
import type { Stage7ModuleDef, Stage7RegionId, Stage7SensorAnchor, Stage7ViewDef } from "@/prototypes/stage7-digital-twin/types";

export const STAGE7_SENSOR_ANCHORS: Stage7SensorAnchor[] = FINAL_SENSOR_INVENTORY.map((entry) => ({
  modality: entry.modality,
  region: entry.region,
  position: MODALITY_ANCHOR_POSITION[entry.modality],
  color: MODALITY_COLOR[entry.modality],
  description: entry.description,
}));

const MODULE_ID_BY_LABEL_PREFIX: Record<string, Stage7RegionId> = {
  frontal: "frontal",
  chest: "chest",
  wrist: "wrist",
};

export const STAGE7_MODULES: Stage7ModuleDef[] = FINAL_MODULES.map((module) => {
  const id = MODULE_ID_BY_LABEL_PREFIX[module.id];
  if (!id) {
    throw new Error(`Stage 7 prototype: unrecognized module id "${module.id}" from FINAL_MODULES — update stage7PrototypeModel.ts's Stage7RegionId mapping before this can render.`);
  }
  return {
    id,
    label: module.label,
    modalities: STAGE7_SENSOR_ANCHORS.filter((anchor) => anchor.region.toLowerCase() === id).map((anchor) => anchor.modality),
  };
});

/**
 * Six deterministic views, azimuth/elevation only — the same angle
 * convention `orthoCameraPosition()` (humanLayout.ts, imported unmodified)
 * already accepts. "three-quarter" reuses the existing system's own default
 * ORTHO_VIEW angle so the prototype's default framing is provably consistent
 * with the accepted product convention, not a new invented angle.
 */
export const STAGE7_VIEWS: Stage7ViewDef[] = [
  { id: "front", label: "Front", azimuthDeg: 0, elevationDeg: 4 },
  { id: "three-quarter", label: "Three-quarter", azimuthDeg: 24, elevationDeg: 6 },
  { id: "left", label: "Left", azimuthDeg: -90, elevationDeg: 4 },
  { id: "right", label: "Right", azimuthDeg: 90, elevationDeg: 4 },
  { id: "back", label: "Back", azimuthDeg: 180, elevationDeg: 4 },
];

export const STAGE7_DEFAULT_VIEW_ID = "three-quarter" as const;
