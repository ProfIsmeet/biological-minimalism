import type { Metadata } from "next";

import { AIInsightsClient } from "@/app/ai-insights/AIInsightsClient";

export const metadata: Metadata = {
  title: "AI Insights — Biological Minimalism",
  description: "What AI-derived information is, and is not, available for the currently selected source.",
};

// Stage 8 §13 — the route body is source-aware, so the page shell stays a
// server component (keeping the metadata export) and delegates to a client
// component that reads the confirmed source mode. Same split the Mission
// Timeline route already uses.
export default function AIInsightsPage() {
  return <AIInsightsClient />;
}
