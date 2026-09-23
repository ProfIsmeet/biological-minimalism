import type { Metadata } from "next";

import { AdditionalResearchArchive } from "@/components/experimental/AdditionalResearchArchive";
import { BioZEvidenceSection } from "@/components/experimental/BioZEvidenceSection";
import { CandidateDispositionMatrix } from "@/components/experimental/CandidateDispositionMatrix";
import { CandidateSelectionRationale } from "@/components/experimental/CandidateSelectionRationale";
import { ExperimentalHero } from "@/components/experimental/ExperimentalHero";
import { ExperimentalProvenance } from "@/components/experimental/ExperimentalProvenance";
import { ResearchDataLoader } from "@/components/experimental/ResearchDataLoader";
import { SensitivityAblationSection } from "@/components/experimental/SensitivityAblationSection";
import { ExperimentalDispositionOrbit } from "@/components/visualization/ExperimentalDispositionOrbit";

export const metadata: Metadata = {
  title: "Experimental Research — Biological Minimalism",
  description:
    "Candidate-sensor investigations, sensitivity analyses, and mixed or negative findings that informed the final CORE_PLUS_CONTEXT architecture without being carried into it.",
};

// Master-prompt §9 corrective pass §3 — required section order. Exactly one
// h1 (ExperimentalHero); every primary section below is an h2; the archived
// ResearchMode's internal heading is an h3. This is a genuine research
// narrative built from useResearchStore's typed artifacts, not a relocated
// copy of the old monolithic ResearchMode page.
export default function ExperimentalResearchPage() {
  return (
    <ResearchDataLoader>
      <div className="mx-auto flex min-w-0 max-w-[1360px] flex-col gap-12 overflow-x-hidden px-0 py-2">
        <ExperimentalHero />
        <ExperimentalDispositionOrbit />
        <CandidateDispositionMatrix />
        <BioZEvidenceSection />
        <SensitivityAblationSection />
        <CandidateSelectionRationale />
        <ExperimentalProvenance />
        <AdditionalResearchArchive />
      </div>
    </ResearchDataLoader>
  );
}
