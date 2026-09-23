import type { Metadata } from "next";

import { ConditionalSelectionRadial } from "@/components/systembrief/ConditionalSelectionRadial";
import { EvidenceDecisionFlow } from "@/components/jury/EvidenceDecisionFlow";
import { EvidenceScope } from "@/components/jury/EvidenceScope";
import { ExperimentalBoundary } from "@/components/jury/ExperimentalBoundary";
import { FinalArchitectureMap } from "@/components/jury/FinalArchitectureMap";
import { FinalSensorLedger } from "@/components/jury/FinalSensorLedger";
import { JuryHero } from "@/components/jury/JuryHero";
import { MinimalCoreComparison } from "@/components/jury/MinimalCoreComparison";

export const metadata: Metadata = {
  title: "System Brief — Biological Minimalism",
  description: "Readable architecture explanation and jury walkthrough for the CORE_PLUS_CONTEXT sensing system.",
};

// Master prompt 3 §22/§23 — the explanatory content the old /mission-overview
// incorrectly tried to be, now living on its own route. Required section
// order: identity (JuryHero) → final architecture visualization
// (FinalArchitectureMap, doubling as SystemBriefArchitecture — already the
// vertical anatomical-axis diagram with 5 modality nodes, the PPG+IMU→HR
// relationship, and the EOG context-only distinction) → MINIMAL_CORE
// comparison → conditional selection rationale (radial + evidence/burden
// cards) → evidence scope → final sensor ledger → BioZ/experimental
// boundary + link out. This page may read as a jury walkthrough; it must
// never replace the operational /mission-overview.
export default function SystemBriefPage() {
  return (
    <div className="mx-auto flex min-w-0 max-w-[1360px] flex-col gap-12 overflow-x-hidden px-0 py-2 sm:gap-16">
      <JuryHero />
      <FinalArchitectureMap />
      <MinimalCoreComparison />
      <ConditionalSelectionRadial />
      <EvidenceDecisionFlow />
      <EvidenceScope />
      <FinalSensorLedger />
      <ExperimentalBoundary />
    </div>
  );
}
