"use client";

import { usePathname } from "next/navigation";

import { PresentationHeader } from "@/components/layout/PresentationHeader";
import { TopBar } from "@/components/layout/TopBar";

// Master-prompt corrective pass §2 — routes the persistent header render
// between the minimal jury/experimental PresentationHeader and the legacy
// Mission-Control TopBar. /research (which immediately redirects to
// /research/experimental) is included in the experimental prefix so there
// is no old-shell flash during the redirect.
export function AppHeader() {
  const pathname = usePathname();

  if (pathname?.startsWith("/mission-overview")) {
    return <PresentationHeader variant="final" />;
  }
  if (pathname?.startsWith("/research")) {
    return <PresentationHeader variant="experimental" />;
  }
  return <TopBar />;
}
