import type { FinalRegion } from "@/lib/architecture";

export type DigitalTwinViewId = "default" | "front" | "back" | "chest" | "wrist" | "frontal";

export interface DigitalTwinViewPreset {
  id: DigitalTwinViewId;
  label: string;
  description: string;
  azimuthDeg: number;
  elevationDeg: number;
  target: readonly [number, number, number];
  viewHeight: number | null;
  activeRegion: FinalRegion | null;
}

export const DIGITAL_TWIN_VIEW_PRESETS: Record<DigitalTwinViewId, DigitalTwinViewPreset> = {
  default: {
    id: "default",
    label: "Default",
    description: "Full-body three-quarter architecture view",
    azimuthDeg: 24,
    elevationDeg: 6,
    target: [0, 0.895, 0],
    viewHeight: null,
    activeRegion: null,
  },
  front: {
    id: "front",
    label: "Front",
    description: "Full-body frontal orientation",
    azimuthDeg: 0,
    elevationDeg: 3,
    target: [0, 0.895, 0],
    viewHeight: null,
    activeRegion: null,
  },
  back: {
    id: "back",
    label: "Back",
    description: "Full-body posterior orientation",
    azimuthDeg: 180,
    elevationDeg: 3,
    target: [0, 0.895, 0],
    viewHeight: null,
    activeRegion: null,
  },
  chest: {
    id: "chest",
    label: "Chest focus",
    description: "Chest module and ECG landmark in anatomical context",
    azimuthDeg: 0,
    elevationDeg: 2,
    target: [0, 1.31, 0],
    viewHeight: 0.74,
    activeRegion: "Chest",
  },
  wrist: {
    id: "wrist",
    label: "Wrist focus",
    description: "Wrist module with colocated PPG and IMU landmarks",
    azimuthDeg: -8,
    elevationDeg: 1,
    target: [0.285, 0.93, 0],
    viewHeight: 0.58,
    activeRegion: "Wrist",
  },
  // Independent-audit correction (S7-AUDIT-01): the semantic architecture
  // summary's "Frontal module" card already offered the identical
  // Focus-region/Selected-region affordance chest and wrist expose, but no
  // view preset ever set `activeRegion: "Frontal"` — the card was reachable
  // and clickable but could never actually reach a "Selected region" state,
  // and EEG/EOG (2 of 5 canonical modalities) had no dedicated close-up
  // framing at all. Target/viewHeight follow the same convention as chest/
  // wrist: centred on H_JOINTS.headCenter.y (1.68, holographicGeometry.ts,
  // imported unmodified), tight enough to read the EEG/EOG landmarks without
  // losing head/neck/shoulder context.
  frontal: {
    id: "frontal",
    label: "Frontal focus",
    description: "Frontal module with EEG and EOG landmarks in anatomical context",
    azimuthDeg: 4,
    elevationDeg: 4,
    target: [0, 1.68, 0],
    viewHeight: 0.42,
    activeRegion: "Frontal",
  },
};

export function resolveDigitalTwinView(id: string | null | undefined): DigitalTwinViewPreset {
  return DIGITAL_TWIN_VIEW_PRESETS[id as DigitalTwinViewId] ?? DIGITAL_TWIN_VIEW_PRESETS.default;
}

export function digitalTwinViewForKey(key: string): DigitalTwinViewId | null {
  switch (key) {
    case "Escape":
    case "Home":
    case "0":
      return "default";
    case "1":
      return "front";
    case "2":
      return "back";
    case "3":
      return "chest";
    case "4":
      return "wrist";
    default:
      return null;
  }
}

export function computeDigitalTwinFrustum(
  aspect: number,
  preset: DigitalTwinViewPreset,
  fullBodyViewHeight: number,
): { left: number; right: number; top: number; bottom: number } {
  const safeAspect = Number.isFinite(aspect) && aspect > 0 ? aspect : 1;
  const viewHeight = preset.viewHeight ?? fullBodyViewHeight;
  const viewWidth = viewHeight * safeAspect;
  return {
    left: -viewWidth / 2,
    right: viewWidth / 2,
    top: viewHeight / 2,
    bottom: -viewHeight / 2,
  };
}
