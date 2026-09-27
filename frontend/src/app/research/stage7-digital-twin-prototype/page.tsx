import type { Metadata } from "next";

import { Stage7DigitalTwinPrototype } from "@/prototypes/stage7-digital-twin/Stage7DigitalTwinPrototype";

/**
 * Isolated Stage 7 prototype route. Deliberately NOT linked from any
 * navigation component (Sidebar/MobileNav/AppHeader — none of those files
 * are modified by this branch), and marked noindex/nofollow so it can never
 * be discovered via search or crawled. This route renders ONLY the
 * prototype and its local explanatory material: no backend/API calls, no
 * store writes, no localStorage, no shared live-feed subscription of any
 * kind (confirmed by grep in VERIFICATION_LEDGER.md).
 */
export const metadata: Metadata = {
  title: "Stage 7 Digital Twin Prototype (isolated, not a product route)",
  robots: { index: false, follow: false },
};

export default function Stage7DigitalTwinPrototypePage() {
  return <Stage7DigitalTwinPrototype />;
}
