"use client";

import clsx from "clsx";

import type { SensorAnchorModel } from "@/components/visualization/human/types";

/** Percent-of-viewBox positions matching the 3D anchor layout's relative placement. */
const FALLBACK_POSITION: Record<string, { left: number; top: number }> = {
  EEG: { left: 41, top: 10 },
  EOG: { left: 59, top: 10 },
  ECG: { left: 50, top: 38 },
  PPG: { left: 62, top: 60 },
  IMU: { left: 70, top: 66 },
};

/**
 * Usable 2D static fallback for when WebGL is unavailable (master prompt 3A
 * §3/§20). Same body outline/anchor-button language as the 3D scene's
 * accessible layer, so the operator loses only the volumetric rendering,
 * never the operational information.
 */
export function StaticAvatarFallback({ anchors, onSelect }: { anchors: SensorAnchorModel[]; onSelect: (modality: SensorAnchorModel["modality"]) => void }) {
  return (
    <div className="relative mx-auto aspect-[3/4] w-full max-w-[320px]">
      <svg viewBox="0 0 300 400" className="absolute inset-0 h-full w-full" aria-hidden="true">
        <g fill="none" stroke="#30464F" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
          <circle cx={150} cy={55} r={34} />
          <line x1={150} y1={89} x2={150} y2={112} />
          <path d="M100,150 L90,112 L210,112 L200,150 L200,270 L100,270 Z" />
          <path d="M100,120 L55,190 L48,250" />
          <path d="M200,120 L245,190 L252,250" />
          <path d="M120,270 L112,380" />
          <path d="M180,270 L188,380" />
        </g>
      </svg>
      {anchors.map((anchor) => {
        const position = FALLBACK_POSITION[anchor.modality] ?? { left: 50, top: 50 };
        return (
          <button
            key={anchor.modality}
            type="button"
            onClick={() => onSelect(anchor.modality)}
            aria-pressed={anchor.selected}
            aria-label={`${anchor.modality} — ${anchor.region} — ${anchor.stateLabel}`}
            title={`${anchor.modality} — ${anchor.stateLabel}`}
            className={clsx(
              "absolute flex -translate-x-1/2 -translate-y-1/2 items-center gap-1 rounded-full border px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide outline-none focus-visible:ring-2 focus-visible:ring-final-accent",
              anchor.selected ? "bg-final-accent-soft" : "bg-surface-1/80",
            )}
            style={{ left: `${position.left}%`, top: `${position.top}%`, borderColor: anchor.color, color: anchor.state === "disconnected" ? "#758990" : "#f2f6f7" }}
          >
            <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: anchor.color }} />
            {anchor.modality}
            {anchor.state === "fault" ? " SIM" : ""}
          </button>
        );
      })}
      <p className="absolute bottom-1 left-1/2 -translate-x-1/2 text-[10px] text-ink-muted">3D rendering unavailable — static sensor map</p>
    </div>
  );
}
