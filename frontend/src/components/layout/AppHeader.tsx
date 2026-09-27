"use client";

import { usePathname } from "next/navigation";

import { PresentationHeader } from "@/components/layout/PresentationHeader";
import { TopBar } from "@/components/layout/TopBar";

// Stage 4 route-cohesion pass — every route now renders the same minimal
// PresentationHeader shell. The legacy Mission-Control TopBar (invented
// "Mission Control / Earth Orbit / Mission Day" language found nowhere else
// in the product, plus an AI-confidence badge duplicating the AI Insights
// page's own content) previously rendered on /ai-insights, /mission-timeline,
// and /settings — the last three routes not yet migrated. TopBar.tsx is left
// in place (it is one of verify-monitoring-consumers.mjs's protected files)
// but is no longer mounted anywhere. /research (which immediately redirects
// to /research/experimental) is included in the experimental prefix so
// there is no old-shell flash during the redirect.
export function AppHeader() {
  const pathname = usePathname();

  if (pathname?.startsWith("/mission-overview")) {
    return <PresentationHeader variant="final" />;
  }
  if (pathname?.startsWith("/live-monitoring")) {
    return <PresentationHeader variant="monitoring" />;
  }
  if (pathname?.startsWith("/system-brief")) {
    return <PresentationHeader variant="system" />;
  }
  if (pathname?.startsWith("/research")) {
    return <PresentationHeader variant="experimental" />;
  }
  if (pathname?.startsWith("/digital-twin")) {
    return <PresentationHeader variant="reference" />;
  }
  if (pathname?.startsWith("/ai-insights")) {
    return <PresentationHeader variant="insights" />;
  }
  if (pathname?.startsWith("/mission-timeline")) {
    return <PresentationHeader variant="timeline" />;
  }
  if (pathname?.startsWith("/settings")) {
    return <PresentationHeader variant="settings" />;
  }
  return <TopBar />;
}
