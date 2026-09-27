"use client";

import { useEffect, useRef, useState } from "react";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";

import { WebglStage } from "@/components/visualization/human/WebglStage";
import { STAGE7_SENSOR_ANCHORS, STAGE7_VIEWS, STAGE7_DEFAULT_VIEW_ID } from "@/prototypes/stage7-digital-twin/stage7PrototypeModel";
import { STAGE7_STAGE_BACKGROUND } from "@/prototypes/stage7-digital-twin/stage7PrototypeMaterials";
import { STAGE7_CAMERA_DISTANCE, stage7CameraPosition, stage7ComputeFrustum } from "@/prototypes/stage7-digital-twin/stage7PrototypeCamera";
import { Stage7HumanModel } from "@/prototypes/stage7-digital-twin/Stage7HumanModel";
import { Stage7Lighting } from "@/prototypes/stage7-digital-twin/Stage7Lighting";
import { Stage7RegionFocus } from "@/prototypes/stage7-digital-twin/Stage7RegionFocus";
import { Stage7SensorAnchors } from "@/prototypes/stage7-digital-twin/Stage7SensorAnchors";
import { Stage7StaticFallback } from "@/prototypes/stage7-digital-twin/Stage7StaticFallback";
import type { Stage7Selection, Stage7ViewId } from "@/prototypes/stage7-digital-twin/types";

const HEIGHT_FRACTION = 0.8;

function Stage7CameraRig({ aspect, viewId }: { aspect: number; viewId: Stage7ViewId }) {
  const camera = useThree((state) => state.camera) as THREE.OrthographicCamera;
  const scene = useThree((state) => state.scene);
  const invalidate = useThree((state) => state.invalidate);

  useEffect(() => {
    scene.background = new THREE.Color(STAGE7_STAGE_BACKGROUND);
    invalidate();
  }, [scene, invalidate]);

  useEffect(() => {
    const view = STAGE7_VIEWS.find((candidate) => candidate.id === viewId) ?? STAGE7_VIEWS[0]!;
    const fit = stage7ComputeFrustum(aspect, HEIGHT_FRACTION);
    camera.left = fit.left;
    camera.right = fit.right;
    camera.top = fit.top;
    camera.bottom = fit.bottom;
    camera.zoom = 1;
    const [x, y, z] = stage7CameraPosition(view, STAGE7_CAMERA_DISTANCE);
    camera.position.set(x, y, z);
    camera.near = 0.1;
    camera.far = STAGE7_CAMERA_DISTANCE + 12;
    camera.up.set(0, 1, 0);
    camera.lookAt(0, 0.82, 0);
    camera.updateProjectionMatrix();
    // "demand" frameloop only re-renders in response to R3F-tracked prop
    // changes or an explicit invalidate() — camera.position/lookAt here are
    // imperative mutations React/R3F cannot see on their own, so without this
    // call a view/selection change would update the camera object but never
    // actually redraw the canvas.
    invalidate();
  }, [camera, aspect, viewId, invalidate]);

  return null;
}

/**
 * Stage 7 prototype canvas. Reuses the existing, imported, unmodified
 * WebglStage wrapper (unsupported / render-error / context-loss coverage —
 * Stage 2 A4) exactly as the product's own PhysiologyAvatar3D.tsx and
 * ConceptualTwinStage.tsx already do — this prototype does not reimplement
 * fallback handling, only supplies its own fallback content
 * (Stage7StaticFallback) and its own scene content.
 *
 * No autonomous animation of any kind runs here by default (design spec
 * "Reduced-motion model") — frameloop is "demand" (render only on state
 * change / R3F invalidation), which also means this component draws zero
 * frames when nothing has changed, satisfying the performance budget's
 * "no per-frame work when nothing changed" goal without needing a visibility
 * observer for this specific concern (there is no continuous animation to
 * gate in the first place).
 */
export function Stage7PrototypeCanvas({
  viewId,
  selection,
  regionFocusId,
}: {
  viewId: Stage7ViewId;
  selection: Stage7Selection | null;
  regionFocusId: Stage7Selection["regionId"] | null;
}) {
  const [aspect, setAspect] = useState(1);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const apply = (width: number, height: number) => {
      if (width > 0 && height > 0) setAspect(width / height);
    };
    const rect = el.getBoundingClientRect();
    apply(rect.width, rect.height);
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) apply(entry.contentRect.width, entry.contentRect.height);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const currentView = STAGE7_VIEWS.find((v) => v.id === viewId)?.label ?? STAGE7_DEFAULT_VIEW_ID;
  const selectionLabel = selection
    ? selection.kind === "modality"
      ? `${selection.modality} sensor selected (prototype selection, not telemetry)`
      : `${selection.regionId} module focused (prototype selection, not telemetry)`
    : "no selection";

  return (
    <div
      ref={containerRef}
      className="stage7-canvas-frame"
      role="img"
      aria-label={`Stage 7 prototype human sensing topology, ${currentView} view, ${selectionLabel}. Architecture-only, untrained, unvalidated illustrative reference figure.`}
    >
      <WebglStage
        canvasProps={{
          dpr: [1, 2],
          orthographic: true,
          frameloop: "demand",
          camera: { manual: true, position: [0, 1, 8], near: 0.1, far: 20 },
          gl: { antialias: true, alpha: false },
        }}
        renderLoading={() => <div className="stage7-canvas-loading">Loading Stage 7 prototype stage…</div>}
        renderFallback={(retry) => (
          <Stage7StaticFallback selection={selection} onRetry={retry ?? undefined} unsupported={retry === null} />
        )}
      >
        <Stage7CameraRig aspect={aspect} viewId={viewId} />
        <Stage7Lighting />
        <Stage7HumanModel />
        <Stage7SensorAnchors anchors={STAGE7_SENSOR_ANCHORS} selection={selection} />
        <Stage7RegionFocus regionId={regionFocusId} />
      </WebglStage>
    </div>
  );
}
