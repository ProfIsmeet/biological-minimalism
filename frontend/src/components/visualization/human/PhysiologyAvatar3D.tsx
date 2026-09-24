"use client";

import { useEffect, useRef, useState } from "react";
import { useThree } from "@react-three/fiber";
import type * as THREE from "three";
import clsx from "clsx";

import { HolographicHumanFigure } from "@/components/visualization/human/HolographicHumanFigure";
import { HolographicStageAtmosphere } from "@/components/visualization/human/HolographicStageAtmosphere";
import { HumanScanRings } from "@/components/visualization/human/HumanScanRings";
import { HumanSensorContacts } from "@/components/visualization/human/HumanSensorContacts";
import { OperationalAvatarOverlay } from "@/components/visualization/human/OperationalAvatarOverlay";
import { StaticAvatarFallback } from "@/components/visualization/human/StaticAvatarFallback";
import { WebglStage } from "@/components/visualization/human/WebglStage";
import { ORTHO_VIEW, computeOrthographicFit, orthoCameraPosition } from "@/components/visualization/human/humanLayout";
import { H_FIGURE_CENTER_Y, H_FIGURE_HALF_WIDTH, H_FIGURE_TOTAL_HEIGHT } from "@/components/visualization/human/holographicGeometry";
import type { PhysiologyAvatarPresentationModel } from "@/components/visualization/human/types";

// Container width below which the overlay switches from a right rail to a
// stacked grid (§5.3). Tuned to the actual operational-avatar cell width: at
// 1440 the cell is ~395px, at tablet ~590px (both rail); a phone stacks the
// stage full width to ~330px (grid). The nominal 480px in §5.2 is the
// intended semantics ("wide enough for a side-by-side"); 340 is the value
// that realises it for this app's actual avatar-cell widths.
const COMPACT_BREAKPOINT_PX = 340;
const DESKTOP_HEIGHT_FRACTION = 0.78;
const COMPACT_HEIGHT_FRACTION = 0.64;
// The operational avatar is a fixed three-quarter view (never front-on), so
// its worst-case projected half-width is narrower than the 360°-rotation
// default; a small horizontal margin keeps the figure large in the narrow
// desktop canvas while still fitting the contact markers.
const OPERATIONAL_FIT = { halfWidth: H_FIGURE_HALF_WIDTH, marginFraction: 0.06, totalHeight: H_FIGURE_TOTAL_HEIGHT };
const HOLO_TARGET: [number, number, number] = [0, H_FIGURE_CENTER_Y, 0];

/**
 * Prompt 3A.2 §6 — the single place that configures the deterministic
 * orthographic frustum + three-quarter position. Re-runs whenever the canvas
 * aspect or the target height fraction changes (e.g. a live viewport
 * emulation during QA). Orthographic bounds are set explicitly in world units
 * (`camera.manual` disables R3F's pixel-based auto-fit), so the figure's
 * on-screen height is exactly `heightFraction` of the canvas regardless of DPR
 * or canvas pixel size.
 */
function OrthoFitRig({ aspect, heightFraction }: { aspect: number; heightFraction: number }) {
  const camera = useThree((state) => state.camera) as THREE.OrthographicCamera;
  useEffect(() => {
    const fit = computeOrthographicFit(aspect, heightFraction, OPERATIONAL_FIT);
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

/**
 * Top-level volumetric physiology avatar (master prompt 3A §3–§7, deterministic
 * screen-space overlay + orthographic framing in Prompt 3A.2 §5/§6). Loaded via
 * `next/dynamic(..., { ssr:false })`. The Three.js `<Canvas>` renders ONLY the
 * mannequin, region orbits, and small contact-marker spheres; every interactive
 * sensor button and text label lives in the sibling DOM overlay
 * (OperationalAvatarOverlay), so nothing collides. Falls back to
 * `StaticAvatarFallback` when WebGL is unavailable.
 */
export function PhysiologyAvatar3D({ anchors, reducedMotion, onSelectModality }: PhysiologyAvatarPresentationModel) {
  const [inView, setInView] = useState(true);
  const [compact, setCompact] = useState(false);
  const [canvasAspect, setCanvasAspect] = useState(0.7);
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasWrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new IntersectionObserver((entries) => setInView(entries[0]?.isIntersecting ?? true), { threshold: 0.02 });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Container width decides rail-vs-grid overlay layout (§5.2/§5.3).
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const apply = (width: number) => {
      if (width > 0) setCompact(width < COMPACT_BREAKPOINT_PX);
    };
    apply(el.getBoundingClientRect().width);
    const observer = new ResizeObserver((entries) => apply(entries[0]?.contentRect.width ?? 0));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Canvas-region aspect drives the orthographic fit (§6). Measured from the
  // canvas wrapper, not the whole container, since the canvas is only ~58% of
  // the container width on desktop.
  useEffect(() => {
    const el = canvasWrapRef.current;
    if (!el) return;
    const apply = (width: number, height: number) => {
      if (width > 0 && height > 0) setCanvasAspect(width / height);
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

  const handleSelect = (modality: Parameters<NonNullable<typeof onSelectModality>>[0]) => onSelectModality?.(modality);

  const heightFraction = compact ? COMPACT_HEIGHT_FRACTION : DESKTOP_HEIGHT_FRACTION;

  return (
    <div
      ref={containerRef}
      className={clsx("relative w-full", compact ? "flex h-[540px] flex-col" : "flex h-full min-h-[340px] flex-row")}
    >
      <div ref={canvasWrapRef} className={clsx("relative", compact ? "h-[56%] w-full" : "h-full w-[62%]")}>
        {/* Stage 2 A4 — WebglStage covers all three failure paths (unsupported
            WebGL, a render-time error anywhere in the scene tree, and a lost
            WebGL context at runtime) with one shared mechanism instead of
            only the up-front unsupported check this component used to have.
            The OperationalAvatarOverlay column stays mounted regardless, so
            the operator never loses the interactive sensor panel — only the
            volumetric rendering itself is ever replaced. */}
        <WebglStage
          canvasProps={{
            dpr: [1, 2],
            orthographic: true,
            frameloop: inView ? "always" : "never",
            camera: { manual: true, position: orthoCameraPosition(), near: 0.1, far: ORTHO_VIEW.distance + 12 },
            gl: { antialias: true, alpha: false },
          }}
          renderLoading={() => <div className="absolute inset-0 z-10 flex items-center justify-center text-xs text-ink-muted">Loading physiology stage…</div>}
          renderFallback={(retry) => <StaticAvatarFallback anchors={anchors} onSelect={handleSelect} onRetry={retry ?? undefined} />}
        >
          {/* Prompt 3B §6 — holographic human system: deep-navy atmosphere +
              spatial scan rings + translucent/wireframe figure + on-body
              sensor contacts. Interactive buttons/labels stay in the DOM
              overlay (collision-free). */}
          <OrthoFitRig aspect={canvasAspect} heightFraction={heightFraction} />
          <HolographicStageAtmosphere />
          <HumanScanRings reducedMotion={reducedMotion} />
          <HolographicHumanFigure />
          <HumanSensorContacts anchors={anchors} />
        </WebglStage>
      </div>

      <div className={clsx("relative", compact ? "w-full flex-1" : "h-full w-[38%]")}>
        <OperationalAvatarOverlay anchors={anchors} onSelect={handleSelect} compact={compact} />
      </div>
    </div>
  );
}
