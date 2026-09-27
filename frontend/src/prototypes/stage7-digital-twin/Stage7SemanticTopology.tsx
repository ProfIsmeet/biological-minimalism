"use client";

import type { FinalModality } from "@/lib/architecture";
import { STAGE7_MODULES, STAGE7_SENSOR_ANCHORS } from "@/prototypes/stage7-digital-twin/stage7PrototypeModel";
import type { Stage7RegionId, Stage7Selection } from "@/prototypes/stage7-digital-twin/types";

/**
 * Fully keyboard-operable, canvas-independent module/modality list (design
 * spec "Accessibility model"). This is the actual textual equivalent for
 * everything the 3D scene shows — usable with the canvas never focused,
 * never touched, and never rendered at all (the static fallback reuses the
 * exact same anchor descriptions).
 */
export function Stage7SemanticTopology({
  selection,
  onSelectRegion,
  onSelectModality,
}: {
  selection: Stage7Selection | null;
  onSelectRegion: (regionId: Stage7RegionId) => void;
  onSelectModality: (modality: FinalModality) => void;
}) {
  return (
    <div className="stage7-topology-list">
      <p className="stage7-topology-list__heading">Sensor topology — CORE_PLUS_CONTEXT · 5 modalities</p>
      {STAGE7_MODULES.map((module) => {
        const isRegionSelected = selection?.kind === "region" && selection.regionId === module.id;
        return (
          <div key={module.id} className="stage7-topology-list__module">
            <button
              type="button"
              aria-pressed={isRegionSelected}
              className={isRegionSelected ? "stage7-topology-list__module-button stage7-topology-list__module-button--active" : "stage7-topology-list__module-button"}
              onClick={() => onSelectRegion(module.id)}
            >
              {module.label}
            </button>
            <ul className="stage7-topology-list__modalities">
              {module.modalities.map((modality) => {
                const anchor = STAGE7_SENSOR_ANCHORS.find((a) => a.modality === modality)!;
                const isModalitySelected = selection?.kind === "modality" && selection.modality === modality;
                return (
                  <li key={modality}>
                    <button
                      type="button"
                      aria-pressed={isModalitySelected}
                      className={isModalitySelected ? "stage7-topology-list__modality-button stage7-topology-list__modality-button--active" : "stage7-topology-list__modality-button"}
                      style={{ borderColor: anchor.color }}
                      onClick={() => onSelectModality(modality)}
                    >
                      <span className="stage7-topology-list__modality-swatch" style={{ backgroundColor: anchor.color }} aria-hidden="true" />
                      <span>
                        <strong>{modality}</strong> — {anchor.description}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}
      <p className="stage7-topology-list__note" aria-live="polite">
        {selection
          ? selection.kind === "modality"
            ? `PROTOTYPE SELECTION: ${selection.modality} sensor. This is a UI interaction state, not a telemetry reading.`
            : `PROTOTYPE SELECTION: ${selection.regionId} module. This is a UI interaction state, not a telemetry reading.`
          : "No selection. Choose a module or modality to focus it in the stage above."}
      </p>
    </div>
  );
}
