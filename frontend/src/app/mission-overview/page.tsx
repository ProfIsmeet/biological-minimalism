import type { Metadata } from "next";

import { EvidenceDecisionFlow } from "@/components/jury/EvidenceDecisionFlow";
import { EvidenceScope } from "@/components/jury/EvidenceScope";
import { ExperimentalBoundary } from "@/components/jury/ExperimentalBoundary";
import { FaultAwareInference } from "@/components/jury/FaultAwareInference";
import { FinalArchitectureMap } from "@/components/jury/FinalArchitectureMap";
import { JuryHero } from "@/components/jury/JuryHero";
import { MinimalCoreComparison } from "@/components/jury/MinimalCoreComparison";
import { PhysiologicalView } from "@/components/jury/PhysiologicalView";
import { SourceStatusStrip } from "@/components/jury/SourceStatusStrip";

export const metadata: Metadata = {
  title: "Mission Overview — Biological Minimalism",
};

// Master-prompt §7 — required section order. This replaces the old
// panel-grid dashboard (SelectedArchitecturePanel banner above
// PrimaryVitals/CognitiveStatus/SpaceAdaptation/AIConfidence/SensorHealth/
// DigitalTwinPreview + MissionModeSwitcher) entirely; none of that
// information architecture remains underneath this page.
export default function MissionOverviewPage() {
  return (
    <div className="mx-auto flex min-w-0 max-w-[1360px] flex-col gap-[72px] overflow-x-hidden px-0 py-2">
      <SourceStatusStrip />
      <JuryHero />
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <div className="lg:col-span-7">
          <FinalArchitectureMap />
        </div>
        <div className="lg:col-span-5">
          <MinimalCoreComparison />
        </div>
      </div>
      <PhysiologicalView />
      <FaultAwareInference />
      <EvidenceDecisionFlow />
      <EvidenceScope />
      <ExperimentalBoundary />
    </div>
  );
}
