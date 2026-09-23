"use client";

import { usePathname } from "next/navigation";

import { PresentationHeader } from "@/components/layout/PresentationHeader";
import { TopBar } from "@/components/layout/TopBar";

// Master-prompt 3 §6.3 — routes the persistent header render between the
// minimal PresentationHeader (final/monitoring/experimental variants) and
// the legacy Mission-Control TopBar, which is now reserved strictly for the
// preserved reference routes (/digital-twin, /ai-insights,
// /mission-timeline, /settings). /research (which immediately redirects to
// /research/experimental) is included in the experimental prefix so there
// is no old-shell flash during the redirect.
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
  return <TopBar />;
}
