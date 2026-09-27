"use client";

import { STAGE7_DEFAULT_VIEW_ID, STAGE7_VIEWS } from "@/prototypes/stage7-digital-twin/stage7PrototypeModel";
import type { Stage7ViewId } from "@/prototypes/stage7-digital-twin/types";

/**
 * Deterministic view buttons (design spec "View model"). Native <button>
 * elements, keyboard-operable by construction, current view indicated via
 * aria-pressed AND a visible filled/outlined style — never color alone.
 * A "Reset" button always returns to STAGE7_DEFAULT_VIEW_ID regardless of
 * current state.
 */
export function Stage7ViewControls({ viewId, onChange }: { viewId: Stage7ViewId; onChange: (id: Stage7ViewId) => void }) {
  return (
    <div className="stage7-view-controls" role="group" aria-label="Deterministic camera views">
      {STAGE7_VIEWS.map((view) => (
        <button
          key={view.id}
          type="button"
          aria-pressed={viewId === view.id}
          className={viewId === view.id ? "stage7-view-controls__button stage7-view-controls__button--active" : "stage7-view-controls__button"}
          onClick={() => onChange(view.id)}
        >
          {view.label}
        </button>
      ))}
      <button
        type="button"
        className="stage7-view-controls__button stage7-view-controls__button--reset"
        onClick={() => onChange(STAGE7_DEFAULT_VIEW_ID)}
      >
        Reset
      </button>
    </div>
  );
}
