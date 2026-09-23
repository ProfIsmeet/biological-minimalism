import type { Metadata } from "next";

import { MissionOverviewExperience } from "@/components/operations/MissionOverviewExperience";

export const metadata: Metadata = {
  title: "Mission Overview — Biological Minimalism",
};

// Prompt 3B §5/§13 — /mission-overview is now a genuinely scrollable
// operational narrative rather than a fixed four-cell grid. The page stays a
// server component (so `metadata` is exported here) and delegates the whole
// scrollable, stateful experience — including the single page-level selected
// modality shared across the figure, pentagon and ribbon matrix (§16) — to the
// client MissionOverviewExperience.
export default function MissionOverviewPage() {
  return <MissionOverviewExperience />;
}
