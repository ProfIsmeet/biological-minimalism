"use client";

import clsx from "clsx";

import type { SensorAnchorModel } from "@/components/visualization/human/types";
import type { FinalModality } from "@/lib/architecture";
import type { ModalityNodeState, OperationalStateWord } from "@/lib/monitoring/modalityNodeState";

/**
 * Prompt 3A.2 §5 — the deterministic DOM sensor overlay. Every previous pass
 * treated the five sensor pills and three module names as independent
 * world-space `<Html>` elements and fought their overlaps with manual 3D
 * offsets; that approach failed repeatedly (EEG/EOG obscuring one another,
 * WRIST MODULE colliding with the PPG/IMU pills). This component instead lays
 * the labels and interactive buttons out as ordinary DOM in a predictable
 * screen-space rail (desktop) / grid (mobile), so their geometry is fully
 * controlled by CSS and cannot collide. The 3D scene keeps only the small
 * contact-marker spheres; colour links each marker to its button.
 */

interface ModuleGroupDef {
  id: "frontal" | "chest" | "wrist";
  label: string;
  modalities: FinalModality[];
  /** Desktop vertical anchor (top %), roughly aligned with the body region height (§5.2). */
  desktopTop: string;
}

const MODULE_GROUPS: ModuleGroupDef[] = [
  { id: "frontal", label: "FRONTAL MODULE", modalities: ["EEG", "EOG"], desktopTop: "14%" },
  { id: "chest", label: "CHEST MODULE", modalities: ["ECG"], desktopTop: "43%" },
  { id: "wrist", label: "WRIST MODULE", modalities: ["PPG", "IMU"], desktopTop: "70%" },
];

/** Short, single-line state wording shown under each sensor button (§5.1/§5.4). */
function shortStateWord(state: OperationalStateWord): string {
  switch (state) {
    case "Confirmed":
      return "Confirmed";
    case "Simulated fault":
      return "Sim fault";
    case "No channel in current source":
      return "No channel";
    case "Disconnected":
      return "Disconnected";
    case "Replay warm-up":
      return "Warm-up";
    case "Connected — awaiting confirmed frame":
      return "Awaiting";
    case "Source error":
      return "Source error";
    case "Recovered":
      return "Recovered";
    case "Unavailable":
      return "Unavailable";
    default:
      return state;
  }
}

function isDimmed(state: ModalityNodeState): boolean {
  return state === "disconnected" || state === "source_error" || state === "awaiting_confirmation" || state === "unavailable";
}

function isDashed(state: ModalityNodeState): boolean {
  return state === "fault" || state === "warmup" || state === "awaiting_confirmation" || state === "unavailable" || state === "source_error";
}

function borderColor(anchor: SensorAnchorModel): string {
  if (anchor.state === "fault") return "#D46F70";
  if (anchor.state === "warmup" || anchor.state === "awaiting_confirmation") return "#D5A45E";
  if (isDimmed(anchor.state)) return "#516269";
  return anchor.color;
}

function SensorButton({ anchor, onSelect }: { anchor: SensorAnchorModel; onSelect: (modality: FinalModality) => void }) {
  const dimmed = isDimmed(anchor.state);
  const bColor = borderColor(anchor);
  return (
    <button
      type="button"
      onClick={() => onSelect(anchor.modality)}
      aria-pressed={anchor.selected}
      aria-label={`${anchor.modality} — ${anchor.region} — ${anchor.stateLabel}`}
      title={`${anchor.modality} — ${anchor.stateLabel}`}
      className="pointer-events-auto flex min-h-[28px] flex-col items-start justify-center rounded-[7px] px-2 py-1 text-left outline-none transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
      style={{
        border: `1.5px ${isDashed(anchor.state) ? "dashed" : "solid"} ${bColor}`,
        background: anchor.selected ? "rgba(105,183,173,0.16)" : "rgba(8,16,19,0.72)",
        boxShadow: anchor.selected ? "0 0 0 2px rgba(105,183,173,0.55)" : "none",
      }}
    >
      <span className="flex items-center gap-1.5">
        <span aria-hidden="true" className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: dimmed ? "#516269" : anchor.color }} />
        <span className="text-[11px] font-bold leading-none tracking-wide" style={{ color: dimmed ? "#9DB0B6" : "#F2F6F7" }}>
          {anchor.modality}
        </span>
        {anchor.state === "fault" ? (
          <span aria-hidden="true" className="rounded-[3px] bg-jury-fault/25 px-1 text-[8px] font-bold leading-tight text-jury-fault">
            SIM
          </span>
        ) : null}
      </span>
      <span className="mt-0.5 text-[9px] leading-none text-ink-muted">{shortStateWord(anchor.stateLabel)}</span>
    </button>
  );
}

function ModuleGroup({
  def,
  anchors,
  onSelect,
  className,
  style,
}: {
  def: ModuleGroupDef;
  anchors: SensorAnchorModel[];
  onSelect: (modality: FinalModality) => void;
  className?: string;
  style?: React.CSSProperties;
}) {
  const groupAnchors = def.modalities
    .map((modality) => anchors.find((a) => a.modality === modality))
    .filter((a): a is SensorAnchorModel => Boolean(a));
  return (
    <div className={clsx("flex flex-col gap-1.5", className)} style={style}>
      <span className="text-[10px] font-bold uppercase leading-none tracking-[0.08em] text-ink-secondary">{def.label}</span>
      <div className="flex flex-wrap gap-2">
        {groupAnchors.map((anchor) => (
          <SensorButton key={anchor.modality} anchor={anchor} onSelect={onSelect} />
        ))}
      </div>
    </div>
  );
}

/**
 * `compact` (mobile, container < ~480px): a two-column grid below the figure,
 * frontal spanning both columns. Otherwise (desktop): module groups pinned to
 * the right rail at region-aligned vertical positions.
 */
export function OperationalAvatarOverlay({
  anchors,
  onSelect,
  compact,
}: {
  anchors: SensorAnchorModel[];
  onSelect: (modality: FinalModality) => void;
  compact: boolean;
}) {
  if (compact) {
    return (
      <div className="grid w-full grid-cols-2 gap-x-3 gap-y-2.5 px-1 pt-1">
        <ModuleGroup def={MODULE_GROUPS[0]!} anchors={anchors} onSelect={onSelect} className="col-span-2" />
        <ModuleGroup def={MODULE_GROUPS[1]!} anchors={anchors} onSelect={onSelect} />
        <ModuleGroup def={MODULE_GROUPS[2]!} anchors={anchors} onSelect={onSelect} />
      </div>
    );
  }

  return (
    <div className="pointer-events-none absolute inset-0">
      {MODULE_GROUPS.map((def) => (
        <ModuleGroup
          key={def.id}
          def={def}
          anchors={anchors}
          onSelect={onSelect}
          className="absolute left-2 right-2"
          style={{ top: def.desktopTop }}
        />
      ))}
    </div>
  );
}
