"use client";

import { useCallback, useMemo, useState } from "react";
import dynamic from "next/dynamic";

import type { FinalModality } from "@/lib/architecture";
import { STAGE7_DEFAULT_VIEW_ID } from "@/prototypes/stage7-digital-twin/stage7PrototypeModel";
import { Stage7SemanticTopology } from "@/prototypes/stage7-digital-twin/Stage7SemanticTopology";
import { Stage7ViewControls } from "@/prototypes/stage7-digital-twin/Stage7ViewControls";
import type { Stage7RegionId, Stage7Selection, Stage7ViewId } from "@/prototypes/stage7-digital-twin/types";

import "@/prototypes/stage7-digital-twin/stage7Prototype.css";

// Loaded client-only, same convention the product's own PhysiologyAvatar3D /
// ConceptualTwinStage use for their next/dynamic(..., { ssr:false }) — R3F's
// <Canvas> cannot render during SSR.
const Stage7PrototypeCanvas = dynamic(
  () => import("@/prototypes/stage7-digital-twin/Stage7PrototypeCanvas").then((m) => m.Stage7PrototypeCanvas),
  { ssr: false, loading: () => <div className="stage7-canvas-loading">Loading Stage 7 prototype stage…</div> },
);

const MODALITY_TO_REGION: Record<FinalModality, Stage7RegionId> = {
  PPG: "wrist",
  IMU: "wrist",
  ECG: "chest",
  EEG: "frontal",
  EOG: "frontal",
};

/**
 * Top-level Stage 7 prototype composition. Owns only local UI state
 * (current view, current selection) — no store, no backend, no
 * localStorage, no shared subscriptions, per the master prompt's isolation
 * requirements. Renders the mandatory watermark and architecture-only
 * disclosure directly in the visible UI, not only in documentation.
 */
export function Stage7DigitalTwinPrototype() {
  const [viewId, setViewId] = useState<Stage7ViewId>(STAGE7_DEFAULT_VIEW_ID);
  const [selection, setSelection] = useState<Stage7Selection | null>(null);

  const handleSelectRegion = useCallback((regionId: Stage7RegionId) => {
    setSelection({ kind: "region", regionId, modality: null });
  }, []);

  const handleSelectModality = useCallback((modality: FinalModality) => {
    setSelection({ kind: "modality", regionId: MODALITY_TO_REGION[modality], modality });
  }, []);

  const regionFocusId = useMemo(() => (selection ? selection.regionId : null), [selection]);

  return (
    <div className="stage7-prototype-root">
      <div className="stage7-watermark" role="note">
        ISOLATED STAGE 7 PROTOTYPE — NOT PRODUCT INTEGRATION
      </div>

      <header className="stage7-header">
        <h1 className="stage7-header__title">Stage 7 Digital Twin — human visualization prototype</h1>
        <p className="stage7-header__disclaimer">
          Conceptual, architecture-only illustration. Untrained. Unvalidated. Not personalized. Not a patient model.
          Not a clinical tool. Not evidence of live astronaut monitoring. Every value shown below is a static fact
          from the accepted CORE_PLUS_CONTEXT architecture — nothing on this page is a measured or inferred
          physiological reading.
        </p>
      </header>

      <div className="stage7-layout">
        <div className="stage7-layout__stage">
          <Stage7ViewControls viewId={viewId} onChange={setViewId} />
          <Stage7PrototypeCanvas viewId={viewId} selection={selection} regionFocusId={regionFocusId} />
        </div>
        <div className="stage7-layout__topology">
          <Stage7SemanticTopology selection={selection} onSelectRegion={handleSelectRegion} onSelectModality={handleSelectModality} />
        </div>
      </div>
    </div>
  );
}
