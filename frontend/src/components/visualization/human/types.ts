import type { FinalModality, FinalRegion } from "@/lib/architecture";
import type { ModalityNodeState, OperationalStateWord } from "@/lib/monitoring/modalityNodeState";

/**
 * Master prompt 3A §4 — shared volumetric human visualization system. This
 * module (and every other file directly under components/visualization/human)
 * is pure presentation: it receives a typed model through props and never
 * reads missionStore/useOperationalViewModel itself. The page-level
 * component (OperationalPhysiologyStage) is the only place that derives this
 * model from the shared operational view model.
 */
export type PhysiologyAvatarMode = "operational" | "architecture" | "digital-twin";

export interface SensorAnchorModel {
  modality: FinalModality;
  region: FinalRegion;
  /** Local mannequin-space position, meters, y-up. */
  position: readonly [number, number, number];
  state: ModalityNodeState;
  stateLabel: OperationalStateWord;
  selected: boolean;
  color: string;
  detail: string;
}

export interface PhysiologyAvatarPresentationModel {
  mode: PhysiologyAvatarMode;
  anchors: SensorAnchorModel[];
  reducedMotion: boolean;
  onSelectModality?: (modality: FinalModality) => void;
}
