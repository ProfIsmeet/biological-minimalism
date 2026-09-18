"use client";

import { createContext, useContext } from "react";

/**
 * Lets Panel's title render as a different heading level depending on where
 * it's nested, without touching every Panel call site individually.
 *
 * Default "h2" preserves existing behavior on every page outside the
 * Experimental Research archive (live-monitoring, ai-insights, settings,
 * digital-twin, mission-timeline all use Panel titles as their primary
 * sub-headings directly under the page's own h1).
 *
 * AdditionalResearchArchive.tsx provides "h3" around the whole embedded
 * ResearchMode tree, because those Panels are now nested two levels below
 * the Experimental Research page's h1 (h1 → h2 "Additional Research
 * Archive" → h3 for every Panel inside it) — corrective-pass §4/§13.9.
 */
const PanelHeadingContext = createContext<"h2" | "h3">("h2");

export const PanelHeadingProvider = PanelHeadingContext.Provider;

export function usePanelHeadingLevel(): "h2" | "h3" {
  return useContext(PanelHeadingContext);
}
