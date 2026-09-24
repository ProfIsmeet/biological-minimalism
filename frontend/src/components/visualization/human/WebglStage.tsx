"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Canvas, type RootState } from "@react-three/fiber";

import { detectWebgl } from "@/components/visualization/human/detectWebgl";
import { WebglErrorBoundary } from "@/components/visualization/human/WebglErrorBoundary";

type CanvasProps = Omit<React.ComponentProps<typeof Canvas>, "children">;

interface WebglStageProps {
  canvasProps: CanvasProps;
  children: ReactNode;
  /**
   * `retry` is `null` when recovery genuinely cannot help (WebGL is
   * unsupported on this device/browser) — A4 requires a recovery action
   * "only when technically possible", so callers must not render a retry
   * control in that case. For a runtime render error or a lost WebGL
   * context, `retry` is a function that remounts the Canvas with a fresh
   * context.
   */
  renderFallback: (retry: (() => void) | null) => ReactNode;
  /** Optional loading placeholder for the brief window before the initial
   * WebGL support check resolves (unavoidable — it must run client-side). */
  renderLoading?: () => ReactNode;
}

/**
 * Stage 2 A4 — shared fallback wrapper for every 3D physiology/Digital Twin
 * surface, covering all of the required failure paths in one place instead
 * of leaving each `<Canvas>` caller to handle them ad hoc:
 *   - WebGL unsupported on this device/browser (detected up front).
 *   - Renderer init failure or a render-time error thrown anywhere inside
 *     the scene tree (caught by `WebglErrorBoundary`).
 *   - WebGL context loss at runtime (a DOM event on the canvas, not a
 *     thrown error — listened for via `onCreated`, since R3F does not
 *     surface it as a React error).
 *
 * On any of these, the Canvas is unmounted and `renderFallback` is shown
 * instead — the caller supplies fallback content that preserves whatever
 * important textual/operational information the 3D view would have shown
 * (e.g. `StaticAvatarFallback`'s sensor buttons), never a blank panel and
 * never an invented measurement. Retry remounts the Canvas (a fresh
 * `key` forces a fresh WebGL context), which is the only defined recovery
 * for a lost context or a transient render error.
 */
export function WebglStage({ canvasProps, children, renderFallback, renderLoading }: WebglStageProps) {
  const [webglAvailable, setWebglAvailable] = useState<boolean | null>(null);
  const [contextLost, setContextLost] = useState(false);
  const [remountKey, setRemountKey] = useState(0);
  const contextLossCleanupRef = useRef<() => void>(() => {});

  useEffect(() => {
    setWebglAvailable(detectWebgl());
  }, []);

  useEffect(() => () => contextLossCleanupRef.current(), []);

  const retry = useCallback(() => {
    setContextLost(false);
    setRemountKey((key) => key + 1);
  }, []);

  const handleCreated = useCallback(
    (state: RootState) => {
      canvasProps.onCreated?.(state);
      const canvas = state.gl.domElement;
      const onContextLost = (event: Event) => {
        event.preventDefault();
        setContextLost(true);
      };
      canvas.addEventListener("webglcontextlost", onContextLost);
      contextLossCleanupRef.current = () => canvas.removeEventListener("webglcontextlost", onContextLost);
    },
    [canvasProps],
  );

  if (webglAvailable === null) {
    return renderLoading ? <>{renderLoading()}</> : null;
  }

  if (webglAvailable === false) {
    // Hard-unsupported: no retry can help, so A4's "recovery action only
    // when technically possible" rule means none is offered.
    return <>{renderFallback(null)}</>;
  }

  if (contextLost) {
    return <>{renderFallback(retry)}</>;
  }

  return (
    <WebglErrorBoundary key={remountKey} fallback={() => renderFallback(retry)}>
      <Canvas key={remountKey} {...canvasProps} onCreated={handleCreated}>
        {children}
      </Canvas>
    </WebglErrorBoundary>
  );
}
