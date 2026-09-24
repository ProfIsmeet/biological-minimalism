"use client";

import { MotionConfig } from "framer-motion";

import { useReducedMotionPreference } from "@/lib/runtime/reduceMotion";

/**
 * Stage 2 A2 — Framer Motion's `animate`/`transition` props are driven by its
 * own JS animation engine (WAAPI/rAF motion values), not CSS `animation`/
 * `transition` properties, so the global `prefers-reduced-motion`/
 * `html.reduce-motion` override in globals.css (which only zeroes CSS
 * animation/transition durations) never touches them. Left alone, every
 * Framer Motion surface (DigitalTwinPanel's orbiting rings and pulsing glow,
 * RadialGauge/LinearMeter springs, ExplanationPanel bar animations) keeps
 * animating at full speed regardless of either reduced-motion source.
 *
 * `<MotionConfig reducedMotion="always">` makes every Framer Motion animation
 * in its subtree resolve instantly (equivalent to `transition={{ duration: 0
 * }}` everywhere) without editing each animated component individually. Using
 * the shared `useReducedMotionPreference()` hook (persisted setting OR OS
 * query, propagating live) instead of Framer Motion's own `"user"` mode (OS
 * query only) is what makes the persisted `/settings` toggle actually reach
 * Framer Motion surfaces.
 */
export function MotionConfigProvider({ children }: { children: React.ReactNode }) {
  const reducedMotion = useReducedMotionPreference();
  return <MotionConfig reducedMotion={reducedMotion ? "always" : "never"}>{children}</MotionConfig>;
}
