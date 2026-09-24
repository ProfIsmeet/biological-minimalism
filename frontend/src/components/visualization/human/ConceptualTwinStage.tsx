"use client";

import { useEffect, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Pause, Play, RotateCcw, RotateCw } from "lucide-react";
import type * as THREE from "three";

import { HolographicHumanFigure } from "@/components/visualization/human/HolographicHumanFigure";
import { HolographicStageAtmosphere } from "@/components/visualization/human/HolographicStageAtmosphere";
import { HumanScanRings } from "@/components/visualization/human/HumanScanRings";
import { ORTHO_VIEW, computeOrthographicFit, orthoCameraPosition } from "@/components/visualization/human/humanLayout";
import { H_FIGURE_CENTER_Y, H_FIGURE_HALF_WIDTH, H_FIGURE_TOTAL_HEIGHT } from "@/components/visualization/human/holographicGeometry";

const ROTATION_RADIANS_PER_SECOND = (Math.PI * 2) / 32;
const REDUCED_MOTION_ANGLE = (Math.PI / 180) * 24;
const COMPACT_BREAKPOINT_PX = 480;
const DESKTOP_HEIGHT_FRACTION = 0.8;
const COMPACT_HEIGHT_FRACTION = 0.72;
const HOLO_TARGET: [number, number, number] = [0, H_FIGURE_CENTER_Y, 0];
const TWIN_FIT = { halfWidth: H_FIGURE_HALF_WIDTH, marginFraction: 0.08, totalHeight: H_FIGURE_TOTAL_HEIGHT };

/** Prompt 3B §6/§14 — deterministic orthographic fit, guaranteeing full head-to-feet framing at every rotation angle. */
function OrthoFitRig({ aspect, heightFraction }: { aspect: number; heightFraction: number }) {
  const camera = useThree((state) => state.camera) as THREE.OrthographicCamera;
  useEffect(() => {
    const fit = computeOrthographicFit(aspect, heightFraction, TWIN_FIT);
    camera.left = fit.left;
    camera.right = fit.right;
    camera.top = fit.top;
    camera.bottom = fit.bottom;
    camera.zoom = 1;
    const [x, y, z] = orthoCameraPosition();
    camera.position.set(x, y, z);
    camera.near = 0.1;
    camera.far = ORTHO_VIEW.distance + 12;
    camera.up.set(0, 1, 0);
    camera.lookAt(...HOLO_TARGET);
    camera.updateProjectionMatrix();
  }, [camera, aspect, heightFraction]);
  return null;
}

function RotatingFigure({
  playing,
  reducedMotion,
  angleRef,
  onAngleChange,
}: {
  playing: boolean;
  reducedMotion: boolean;
  angleRef: React.MutableRefObject<number>;
  onAngleChange: (deg: number) => void;
}) {
  const groupRef = useRef<THREE.Group>(null);
  const sinceRef = useRef(0);
  useFrame((_, delta) => {
    if (playing && !reducedMotion) angleRef.current += ROTATION_RADIANS_PER_SECOND * delta;
    if (groupRef.current) groupRef.current.rotation.y = angleRef.current;
    sinceRef.current += delta;
    if (sinceRef.current > 0.5) {
      sinceRef.current = 0;
      onAngleChange((angleRef.current * 180) / Math.PI);
    }
  });
  return (
    <group ref={groupRef}>
      <HolographicHumanFigure />
    </group>
  );
}

/**
 * Prompt 3B §14 — Digital Twin holographic reference figure. Uses the same
 * holographic human system as the operational stage but with NO sensor state,
 * NO data-bearing colour, and NO text on the body. The scan rings are stated
 * to be a decorative/spatial scaffold. Slow rotation, reduced-motion→paused.
 */
export function ConceptualTwinStage() {
  const angleRef = useRef(0);
  const [angleDeg, setAngleDeg] = useState(0);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [playing, setPlaying] = useState(true);
  const [canvasAspect, setCanvasAspect] = useState(1.4);
  const [compact, setCompact] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(query.matches);
    if (query.matches) {
      angleRef.current = REDUCED_MOTION_ANGLE;
      setAngleDeg((REDUCED_MOTION_ANGLE * 180) / Math.PI);
      setPlaying(false);
    }
    const listener = (event: MediaQueryListEvent) => setReducedMotion(event.matches);
    query.addEventListener("change", listener);
    return () => query.removeEventListener("change", listener);
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const apply = (width: number, height: number) => {
      if (width > 0 && height > 0) {
        setCanvasAspect(width / height);
        setCompact(width < COMPACT_BREAKPOINT_PX);
      }
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

  function rotateBy(radians: number) {
    angleRef.current += radians;
    setAngleDeg((angleRef.current * 180) / Math.PI);
  }

  return (
    <div className="flex flex-col gap-3">
      <div ref={containerRef} className="relative h-[380px] w-full overflow-hidden rounded-[10px] border border-jury-border-subtle sm:h-[540px]" style={{ background: "#061A26" }}>
        <Canvas
          dpr={[1, 2]}
          orthographic
          camera={{ manual: true, position: orthoCameraPosition(), near: 0.1, far: ORTHO_VIEW.distance + 12 }}
          gl={{ antialias: true, alpha: false }}
        >
          <OrthoFitRig aspect={canvasAspect} heightFraction={compact ? COMPACT_HEIGHT_FRACTION : DESKTOP_HEIGHT_FRACTION} />
          <HolographicStageAtmosphere />
          <HumanScanRings reducedMotion={reducedMotion} />
          <RotatingFigure playing={playing} reducedMotion={reducedMotion} angleRef={angleRef} onAngleChange={setAngleDeg} />
        </Canvas>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setPlaying((value) => !value)}
          disabled={reducedMotion}
          className="flex h-9 items-center gap-1.5 rounded-[6px] border border-jury-border-strong px-3 text-xs font-medium text-ink-secondary transition-colors duration-150 hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC] disabled:opacity-40"
        >
          {playing && !reducedMotion ? <Pause size={13} aria-hidden="true" /> : <Play size={13} aria-hidden="true" />}
          {playing && !reducedMotion ? "Pause rotation" : "Resume rotation"}
        </button>
        <button
          type="button"
          onClick={() => rotateBy(-Math.PI / 8)}
          className="flex h-9 items-center gap-1.5 rounded-[6px] border border-jury-border-strong px-3 text-xs font-medium text-ink-secondary transition-colors duration-150 hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
        >
          <RotateCcw size={13} aria-hidden="true" /> Rotate left
        </button>
        <button
          type="button"
          onClick={() => rotateBy(Math.PI / 8)}
          className="flex h-9 items-center gap-1.5 rounded-[6px] border border-jury-border-strong px-3 text-xs font-medium text-ink-secondary transition-colors duration-150 hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
        >
          Rotate right <RotateCw size={13} aria-hidden="true" />
        </button>
        {reducedMotion ? <span className="text-[11px] text-ink-muted">Reduced motion — automatic rotation starts paused; manual controls remain active.</span> : null}
      </div>

      {/* A11y fix (Stage 2 A1): the rotation angle updates on every animation
          frame (`useFrame`, up to 60/s) while auto-rotating. It previously
          lived inside this same `role="status"` element, so the whole
          sentence — including the fixed scientific-boundary disclaimer —
          was re-announced continuously. The disclaimer (which never changes
          after mount) keeps the live region; the angle is static-per-render
          text with no live role, readable on request but never a trigger
          for automatic re-announcement. */}
      <p className="sr-only" role="status">
        Architecture-only, untrained, unvalidated holographic reference figure with an illustrative spatial scan field.
        This figure reports no adaptation percentage, confidence value, or measured quantity.
      </p>
      <p className="sr-only">
        Current illustrative rotation approximately {((((angleDeg % 360) + 360) % 360)).toFixed(0)} degrees.
      </p>
    </div>
  );
}
