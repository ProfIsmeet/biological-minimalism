import type { FinalModality, FinalRegion } from "@/lib/architecture";

/**
 * Stage 7 prototype — deliberately decoupled from the operational monitoring
 * types (`ModalityNodeState`, `OperationalStateWord`) that the product's
 * `SensorAnchorModel` (components/visualization/human/types.ts) carries.
 * This prototype has no telemetry, no store, no backend — every anchor here
 * is a static architecture fact, never a live/derived operational state, so
 * it has no business importing operational state types it would never
 * legitimately populate.
 */
export interface Stage7SensorAnchor {
  modality: FinalModality;
  region: FinalRegion;
  /** Local mannequin-space position, meters, y-up — sourced verbatim from humanLayout.ts's MODALITY_ANCHOR_POSITION. */
  position: readonly [number, number, number];
  color: string;
  /** Static conceptual-role sentence, sourced verbatim from lib/architecture.ts's FINAL_SENSOR_INVENTORY description. */
  description: string;
}

export type Stage7RegionId = "frontal" | "chest" | "wrist";

export interface Stage7ModuleDef {
  id: Stage7RegionId;
  label: string;
  modalities: FinalModality[];
}

export type Stage7ViewId = "front" | "three-quarter" | "left" | "right" | "back";

export interface Stage7ViewDef {
  id: Stage7ViewId;
  label: string;
  azimuthDeg: number;
  elevationDeg: number;
}

/** Local UI selection state only — never telemetry, never a shared-store write. Explicitly labelled PROTOTYPE SELECTION wherever rendered. */
export interface Stage7Selection {
  kind: "region" | "modality";
  regionId: Stage7RegionId;
  modality: FinalModality | null;
}
