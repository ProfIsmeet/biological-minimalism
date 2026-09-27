"use client";

import { STAGE7_SENSOR_ANCHORS } from "@/prototypes/stage7-digital-twin/stage7PrototypeModel";
import type { Stage7Selection } from "@/prototypes/stage7-digital-twin/types";

/** Percent-of-viewBox positions matching the 3D anchor layout's relative placement (same convention as the product's own StaticAvatarFallback.tsx). */
const FALLBACK_POSITION: Record<string, { left: number; top: number }> = {
  EEG: { left: 41, top: 10 },
  EOG: { left: 59, top: 10 },
  ECG: { left: 50, top: 38 },
  PPG: { left: 62, top: 60 },
  IMU: { left: 70, top: 66 },
};

/**
 * Stage 7 prototype's static/2D-equivalent view (design spec "Fallback
 * model" / CURRENT_SYSTEM_AUDIT F7). Shown for unsupported WebGL, a
 * render-time error, or a lost context (via the existing, imported,
 * unmodified WebglStage). Preserves the same 5-anchor topology and the same
 * selection state as the 3D mode — never a lesser, disconnected experience.
 * `unsupported` distinguishes the hard-unsupported case (no retry offered,
 * matching WebglStage's "recovery only when technically possible" contract)
 * from a recoverable error/context-loss case.
 */
export function Stage7StaticFallback({
  selection,
  onRetry,
  unsupported,
}: {
  selection: Stage7Selection | null;
  onRetry?: () => void;
  unsupported: boolean;
}) {
  return (
    <div className="stage7-static-fallback">
      <p className="stage7-static-fallback__title">
        {unsupported ? "3D rendering unavailable on this device or browser" : "3D rendering temporarily unavailable"}
      </p>
      <div className="stage7-static-fallback__figure">
        <svg viewBox="0 0 300 400" className="stage7-static-fallback__svg" aria-hidden="true">
          <g fill="none" stroke="#4A6A72" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
            <circle cx={150} cy={55} r={34} />
            <line x1={150} y1={89} x2={150} y2={112} />
            <path d="M100,150 L90,112 L210,112 L200,150 L200,270 L100,270 Z" />
            <path d="M100,120 L55,190 L48,250" />
            <path d="M200,120 L245,190 L252,250" />
            <path d="M120,270 L112,380" />
            <path d="M180,270 L188,380" />
          </g>
        </svg>
        {STAGE7_SENSOR_ANCHORS.map((anchor) => {
          const position = FALLBACK_POSITION[anchor.modality] ?? { left: 50, top: 50 };
          const isSelected = selection !== null && selection.kind === "modality" && selection.modality === anchor.modality;
          return (
            <span
              key={anchor.modality}
              className={isSelected ? "stage7-static-fallback__marker stage7-static-fallback__marker--selected" : "stage7-static-fallback__marker"}
              style={{ left: `${position.left}%`, top: `${position.top}%`, borderColor: anchor.color }}
              aria-hidden="true"
            >
              {anchor.modality}
            </span>
          );
        })}
      </div>
      <p className="stage7-static-fallback__caption">
        Architecture-only, untrained, unvalidated illustrative reference. Sensor topology below remains available as
        text.
      </p>
      {onRetry ? (
        <button type="button" onClick={onRetry} className="stage7-static-fallback__retry">
          Try 3D view again
        </button>
      ) : null}
    </div>
  );
}
