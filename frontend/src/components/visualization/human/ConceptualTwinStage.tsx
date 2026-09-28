"use client";

import { useEffect, useMemo, useRef, useState, type KeyboardEvent as ReactKeyboardEvent } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { ArrowDownToLine, CirclePause, CirclePlay, RotateCcw } from "lucide-react";
import type * as THREE from "three";

import { ArchitectureSensorContacts } from "@/components/visualization/human/ArchitectureSensorContacts";
import { ConceptualTwinFallback } from "@/components/visualization/human/ConceptualTwinFallback";
import { HolographicHumanFigure } from "@/components/visualization/human/HolographicHumanFigure";
import { HolographicStageAtmosphere } from "@/components/visualization/human/HolographicStageAtmosphere";
import { HumanScanRings } from "@/components/visualization/human/HumanScanRings";
import { WebglStage } from "@/components/visualization/human/WebglStage";
import { computeOrthographicFit, ORTHO_VIEW, orthoCameraPosition } from "@/components/visualization/human/humanLayout";
import { H_FIGURE_HALF_WIDTH, H_FIGURE_TOTAL_HEIGHT } from "@/components/visualization/human/holographicGeometry";
import { FINAL_MODULES, FINAL_SENSOR_INVENTORY, MODALITY_COLOR, type FinalRegion } from "@/lib/architecture";
import { useReducedMotionPreference } from "@/lib/runtime/reduceMotion";
import {
  DIGITAL_TWIN_VIEW_PRESETS,
  computeDigitalTwinFrustum,
  digitalTwinViewForKey,
  resolveDigitalTwinView,
  type DigitalTwinViewId,
  type DigitalTwinViewPreset,
} from "@/lib/visualization/digitalTwinPresentation";

const ROTATION_RADIANS_PER_SECOND = (Math.PI * 2) / 36;
const COMPACT_BREAKPOINT_PX = 480;
const FULL_BODY_FIT = { halfWidth: H_FIGURE_HALF_WIDTH, marginFraction: 0.08, totalHeight: H_FIGURE_TOTAL_HEIGHT };

function ViewRig({ aspect, compact, view }: { aspect: number; compact: boolean; view: DigitalTwinViewPreset }) {
  const camera = useThree((state) => state.camera) as THREE.OrthographicCamera;
  useEffect(() => {
    const fit = computeOrthographicFit(aspect, compact ? 0.72 : 0.82, FULL_BODY_FIT);
    const fullBodyViewHeight = fit.top - fit.bottom;
    const frustum = computeDigitalTwinFrustum(aspect, view, fullBodyViewHeight);
    camera.left = frustum.left;
    camera.right = frustum.right;
    camera.top = frustum.top;
    camera.bottom = frustum.bottom;
    camera.zoom = 1;
    const [x, y, z] = orthoCameraPosition({
      azimuthDeg: view.azimuthDeg,
      elevationDeg: view.elevationDeg,
      distance: ORTHO_VIEW.distance,
    });
    camera.position.set(x + view.target[0], y - 0.895 + view.target[1], z + view.target[2]);
    camera.near = 0.1;
    camera.far = ORTHO_VIEW.distance + 12;
    camera.up.set(0, 1, 0);
    camera.lookAt(...view.target);
    camera.updateProjectionMatrix();
  }, [aspect, camera, compact, view]);
  return null;
}

function AnatomicalFigure({
  playing,
  reducedMotion,
  angleRef,
  activeRegion,
}: {
  playing: boolean;
  reducedMotion: boolean;
  angleRef: React.MutableRefObject<number>;
  activeRegion: FinalRegion | null;
}) {
  const groupRef = useRef<THREE.Group>(null);
  useFrame((_, delta) => {
    if (playing && !reducedMotion) angleRef.current += ROTATION_RADIANS_PER_SECOND * Math.min(delta, 0.05);
    if (groupRef.current) groupRef.current.rotation.y = angleRef.current;
  });
  return (
    <group ref={groupRef}>
      <HolographicHumanFigure />
      <ArchitectureSensorContacts activeRegion={activeRegion} />
    </group>
  );
}

const VIEW_ORDER: DigitalTwinViewId[] = ["default", "front", "back", "chest", "wrist"];

function viewButtonLabel(view: DigitalTwinViewId): string {
  return DIGITAL_TWIN_VIEW_PRESETS[view].label;
}

/**
 * Production Stage 7 architecture viewer. It is deliberately a static-system
 * reference: no operational transport, store, endpoint, or model output is consumed.
 */
export function ConceptualTwinStage() {
  const angleRef = useRef(0);
  const reducedMotion = useReducedMotionPreference();
  const [playing, setPlaying] = useState(true);
  const [viewId, setViewId] = useState<DigitalTwinViewId>("default");
  const [canvasAspect, setCanvasAspect] = useState(1.4);
  const [compact, setCompact] = useState(false);
  const [pageVisible, setPageVisible] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const view = resolveDigitalTwinView(viewId);
  const motionActive = playing && viewId === "default" && pageVisible;

  useEffect(() => {
    const updateVisibility = () => setPageVisible(document.visibilityState === "visible");
    updateVisibility();
    document.addEventListener("visibilitychange", updateVisibility);
    return () => document.removeEventListener("visibilitychange", updateVisibility);
  }, []);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;
    const apply = (width: number, height: number) => {
      if (width <= 0 || height <= 0) return;
      setCanvasAspect(width / height);
      setCompact(width < COMPACT_BREAKPOINT_PX);
    };
    const bounds = element.getBoundingClientRect();
    apply(bounds.width, bounds.height);
    const observer = new ResizeObserver(([entry]) => {
      if (entry) apply(entry.contentRect.width, entry.contentRect.height);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const activeModule = useMemo(
    () => FINAL_MODULES.find((module) => module.id === view.activeRegion?.toLowerCase()) ?? null,
    [view.activeRegion],
  );

  function selectView(next: DigitalTwinViewId) {
    angleRef.current = 0;
    setViewId(next);
  }

  function resetView() {
    angleRef.current = 0;
    setViewId("default");
  }

  function onStageKeyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    const next = digitalTwinViewForKey(event.key);
    if (next) {
      event.preventDefault();
      if (next === "default") resetView();
      else selectView(next);
      return;
    }
    if (event.key === " " || event.key.toLowerCase() === "p") {
      event.preventDefault();
      setPlaying((current) => !current);
    }
  }

  return (
    <section aria-labelledby="digital-twin-viewer-heading" className="flex min-w-0 flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="digital-twin-viewer-heading" className="text-base font-semibold text-ink-primary">Anatomical architecture viewer</h2>
          <p className="mt-1 text-sm text-ink-secondary">{view.description}. Landmarks show placement, not current sensor state.</p>
        </div>
        <span className="rounded-full border border-information/35 bg-information/10 px-3 py-1 text-xs font-semibold text-information">
          {view.label}
        </span>
      </div>

      <div
        ref={containerRef}
        tabIndex={0}
        onKeyDown={onStageKeyDown}
        aria-label="Interactive Digital Twin architecture viewer. Keys 1 through 4 select front, back, chest, and wrist views. Home or Escape resets. Space pauses or resumes rotation."
        className="relative h-[430px] w-full overflow-hidden rounded-[12px] border border-jury-border-strong bg-[#061A26] outline-none focus-visible:ring-2 focus-visible:ring-[#A1D2CC] focus-visible:ring-offset-2 focus-visible:ring-offset-canvas sm:h-[600px]"
      >
        <WebglStage
          canvasProps={{
            dpr: [1, 1.75],
            orthographic: true,
            camera: { manual: true, position: orthoCameraPosition(), near: 0.1, far: ORTHO_VIEW.distance + 12 },
            gl: { antialias: true, alpha: false, powerPreference: "high-performance" },
            frameloop: motionActive && !reducedMotion ? "always" : "demand",
          }}
          renderLoading={() => <div className="flex h-full items-center justify-center text-sm text-ink-secondary">Checking 3D capability…</div>}
          renderFallback={(retry) => <ConceptualTwinFallback onRetry={retry ?? undefined} view={view} activeRegion={view.activeRegion} />}
        >
          <ViewRig aspect={canvasAspect} compact={compact} view={view} />
          <HolographicStageAtmosphere />
          <HumanScanRings reducedMotion={reducedMotion || !motionActive} />
          <AnatomicalFigure playing={motionActive} reducedMotion={reducedMotion} angleRef={angleRef} activeRegion={view.activeRegion} />
        </WebglStage>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5" aria-label="Digital Twin view presets">
        {VIEW_ORDER.map((presetId) => (
          <button
            key={presetId}
            type="button"
            onClick={() => (presetId === "default" ? resetView() : selectView(presetId))}
            aria-pressed={viewId === presetId}
            className="min-h-11 rounded-[7px] border border-jury-border-strong px-3 py-2 text-sm font-medium text-ink-secondary transition-colors hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC] aria-pressed:border-final-accent/70 aria-pressed:bg-final-accent/10 aria-pressed:text-ink-primary"
          >
            {viewButtonLabel(presetId)}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setPlaying((current) => !current)}
          disabled={reducedMotion}
          className="flex min-h-11 items-center gap-2 rounded-[7px] border border-jury-border-strong px-3 py-2 text-sm font-medium text-ink-secondary hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC] disabled:cursor-not-allowed disabled:opacity-45"
        >
          {motionActive && !reducedMotion ? <CirclePause size={16} aria-hidden="true" /> : <CirclePlay size={16} aria-hidden="true" />}
          {reducedMotion ? "Rotation paused" : playing ? "Pause rotation" : "Resume rotation"}
        </button>
        <button
          type="button"
          onClick={resetView}
          className="flex min-h-11 items-center gap-2 rounded-[7px] border border-jury-border-strong px-3 py-2 text-sm font-medium text-ink-secondary hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
        >
          <RotateCcw size={16} aria-hidden="true" /> Reset view
        </button>
        <span className="flex items-center gap-1.5 text-xs text-ink-muted">
          <ArrowDownToLine size={14} aria-hidden="true" /> Focus viewer, then use 1–4 · Home/Esc · Space
        </span>
      </div>

      {reducedMotion ? (
        <p className="rounded-[6px] border border-jury-border-subtle bg-surface-2 px-3 py-2 text-sm text-ink-secondary">
          Reduced motion is active. Automatic rotation and scan movement are paused; every preset remains available.
        </p>
      ) : null}

      <div className="border-t border-jury-border-subtle pt-4" aria-live="polite">
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Semantic architecture summary</p>
        <p className="mt-1 text-sm text-ink-primary">
          Active view: <strong>{view.label}</strong>. {activeModule ? `${activeModule.label}: ${activeModule.modalities}.` : "No region focus is active."}
        </p>
        <ul className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
          {FINAL_MODULES.map((module) => {
            const region = (module.id === "frontal" ? "Frontal" : module.id === "chest" ? "Chest" : "Wrist") as FinalRegion;
            const selected = view.activeRegion === region;
            return (
              <li key={module.id} className="rounded-[7px] border border-jury-border-subtle bg-surface-2 p-3">
                <button
                  type="button"
                  onClick={() => selectView(module.id === "chest" ? "chest" : module.id === "wrist" ? "wrist" : "front")}
                  aria-pressed={selected}
                  className="w-full text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
                >
                  <span className="text-sm font-semibold text-ink-primary">{module.label}</span>
                  <span className="mt-1 block text-xs text-ink-secondary">{module.modalities}</span>
                  <span className="mt-1 block text-xs leading-relaxed text-ink-muted">{module.description}</span>
                  <span className="mt-2 block text-xs font-medium text-information">{selected ? "Selected region" : "Focus region"}</span>
                </button>
              </li>
            );
          })}
        </ul>
        <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-2" aria-label="Sensor landmark legend">
          {FINAL_SENSOR_INVENTORY.map((sensor) => (
            <li key={sensor.modality} className="flex items-center gap-2 text-xs text-ink-secondary">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: MODALITY_COLOR[sensor.modality] }} aria-hidden="true" />
              <strong className="text-ink-primary">{sensor.modality}</strong> · {sensor.region} · {sensor.description}
            </li>
          ))}
        </ul>
      </div>

      <p className="sr-only" role="status">
        Architecture-only, untrained, unvalidated anatomical reference. The canvas reports no adaptation percentage,
        confidence value, diagnosis, or current physiological measurement.
      </p>
      <p className="sr-only">Current illustrative rotation approximately follows the selected view preset.</p>
    </section>
  );
}
