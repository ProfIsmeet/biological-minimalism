"use client";

import { useEffect, type ReactNode } from "react";

import { useResearchStore } from "@/store/researchStore";

/**
 * Single trigger point for useResearchStore.load() on the Experimental
 * Research route. Previously ResearchMode.tsx triggered its own load() in a
 * useEffect; now that the route renders several sibling sections reading
 * the same store (BioZEvidenceSection, SensitivityAblationSection,
 * CandidateSelectionRationale, ExperimentalProvenance, plus the archived
 * ResearchMode), the load must fire exactly once from a single place rather
 * than once per section, so this wraps the whole page instead.
 */
export function ResearchDataLoader({ children }: { children: ReactNode }) {
  const load = useResearchStore((state) => state.load);
  useEffect(() => {
    void load();
  }, [load]);
  return <>{children}</>;
}
