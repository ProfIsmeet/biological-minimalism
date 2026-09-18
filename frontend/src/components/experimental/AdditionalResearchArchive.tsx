"use client";

import { Archive } from "lucide-react";

import { ResearchMode } from "@/components/research/ResearchMode";
import { PanelHeadingProvider } from "@/components/ui/PanelHeadingContext";

// Master-prompt §9 item 7 / corrective pass §3 — optional subordinate
// disclosure for the pre-existing, scientifically valid ResearchMode
// evidence tree (raw Stage 3/4 audit panels, full experiment browser,
// operational-cost catalog, etc.) that does not belong in the primary
// Experimental Research narrative but should not be discarded. Collapsed by
// default so it never dominates the default page. ResearchMode itself now
// renders its internal title as an h3 (see ResearchMode.tsx), so this
// component's own h2 remains the only second-level heading introduced here.
export function AdditionalResearchArchive() {
  return (
    <section aria-labelledby="archive-heading">
      <details className="rounded-[10px] border border-jury-border-subtle bg-surface-1">
        <summary className="flex cursor-pointer items-center gap-2 px-5 py-4 text-sm font-medium text-ink-secondary">
          <Archive size={16} className="text-ink-muted" aria-hidden="true" />
          <h2 id="archive-heading" className="inline text-base font-semibold text-ink-primary">
            Additional Research Archive
          </h2>
          <span className="ml-auto text-[11px] font-normal text-ink-muted">
            Full Stage 3/4 audit panels, experiment browser, and operational-cost catalog
          </span>
        </summary>
        <div className="border-t border-jury-border-subtle p-5">
          <PanelHeadingProvider value="h3">
            <ResearchMode />
          </PanelHeadingProvider>
        </div>
      </details>
    </section>
  );
}
