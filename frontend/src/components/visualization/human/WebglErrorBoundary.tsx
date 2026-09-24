"use client";

import { Component, type ReactNode } from "react";

interface WebglErrorBoundaryProps {
  children: ReactNode;
  /** Called with a retry function; return the fallback UI to render while errored. */
  fallback: (retry: () => void) => ReactNode;
}

interface WebglErrorBoundaryState {
  hasError: boolean;
}

/**
 * Stage 2 A4 — a proper React error boundary for the Three.js/`react-three-
 * fiber` scene tree. Neither `PhysiologyAvatar3D.tsx` nor
 * `ConceptualTwinStage.tsx` previously caught a render-time throw inside
 * their `<Canvas>` tree (a bad geometry, a WebGL driver quirk, an R3F
 * internal error) — React would unmount the whole surrounding tree up to the
 * nearest boundary (none existed), leaving a blank panel or crashing the
 * page. This is a class component because `getDerivedStateFromError`/
 * `componentDidCatch` have no hook equivalent.
 *
 * Only catches render-time throws — WebGL *context loss* fires a DOM event
 * on the canvas rather than throwing, so `WebglStage.tsx` (which wraps this
 * boundary together with the `<Canvas>`) listens for that separately and
 * treats it as an equivalent failure.
 */
export class WebglErrorBoundary extends Component<WebglErrorBoundaryProps, WebglErrorBoundaryState> {
  override state: WebglErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): WebglErrorBoundaryState {
    return { hasError: true };
  }

  override componentDidCatch(error: unknown, info: { componentStack: string }) {
    console.error("WebGL scene render error", error, info.componentStack);
  }

  retry = () => {
    this.setState({ hasError: false });
  };

  override render() {
    if (this.state.hasError) {
      return this.props.fallback(this.retry);
    }
    return this.props.children;
  }
}
