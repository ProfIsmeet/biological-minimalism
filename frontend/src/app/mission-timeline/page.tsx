import type { Metadata } from "next";

import { MissionTimelineClient } from "@/app/mission-timeline/MissionTimelineClient";

// Stage 4 fix: this route previously had no server-component page.tsx, so it
// could not export its own `metadata` (Next.js requires a server component
// for that) and the browser tab title fell back to whatever route was last
// statically resolved (observed showing "Biological Minimalism — Final
// Sensing Architecture", the System Brief route's title). Splitting the
// interactive body into MissionTimelineClient restores a correct, stable
// title without changing any client behavior.
export const metadata: Metadata = {
  title: "Mission Timeline — Biological Minimalism",
  description:
    "Chronological record of this interface session's operational events, each stating its origin and the clock its timestamp is measured on, followed by the conceptual architecture checkpoints.",
};

export default function MissionTimelinePage() {
  return <MissionTimelineClient />;
}
