import type { Metadata } from "next";

import { DigitalTwinClient } from "@/app/digital-twin/DigitalTwinClient";

/**
 * Stage 8 §16 — this route previously exported no metadata at all. Because
 * the page component is a client component (the WebGL stage is loaded through
 * next/dynamic with ssr:false), it could not export `metadata` even in
 * principle, so it silently inherited the layout's default title and
 * description — the generic product title. In a tab strip, a bookmark list,
 * or a link preview it was indistinguishable from any other route.
 *
 * Split into a thin server shell owning the metadata plus a client component
 * owning the view, the same pattern /ai-insights and /mission-timeline use.
 */
export const metadata: Metadata = {
  title: "Digital Twin Architecture — Biological Minimalism",
  description:
    "How the accepted wrist, chest, and frontal sensing modules map onto a future physiological-model scaffold. Architecture only: untrained, unvalidated, and not personalized.",
};

export default function DigitalTwinPage() {
  return <DigitalTwinClient />;
}
