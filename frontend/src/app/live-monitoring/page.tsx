import type { Metadata } from "next";

import { RouteHeader } from "@/components/layout/RouteHeader";
import { FinalSignalStack } from "@/components/monitoring/FinalSignalStack";
import { HrInferencePanel } from "@/components/monitoring/HrInferencePanel";
import { InferenceResponseTimeline } from "@/components/monitoring/InferenceResponseTimeline";
import { MonitoringSourceStrip } from "@/components/monitoring/MonitoringSourceStrip";
import { PublicPresentationNotice } from "@/components/monitoring/PublicPresentationNotice";
import { ReplaySessionControl } from "@/components/monitoring/ReplaySessionControl";
import { ScopeProvenanceFooter } from "@/components/monitoring/ScopeProvenanceFooter";
import { SimulatedFaultControl } from "@/components/monitoring/SimulatedFaultControl";
import { SensorConstellation } from "@/components/operations/SensorConstellation";
import { PUBLIC_PRESENTATION_MODE } from "@/lib/config";

export const metadata: Metadata = {
  title: "Signal and Inference Monitor — Biological Minimalism",
  description:
    "Source-aware physiological signals and fault-aware heart-rate inference for CORE_PLUS_CONTEXT, from recorded replay or synthetic demo data.",
};

// Master-prompt 2 §8 — rebuilt as the final signal and inference monitor for
// CORE_PLUS_CONTEXT. Section order is §8.1–§8.8; MonitoringSessionProvider
// (now mounted once in the root layout, master prompt 3 §6) is the single
// fetch boundary for replay/fault session state shared by the source strip,
// replay controls, and fault control below.
// Master-prompt 3 §8.1/§8.2/§21 — 8/4 desktop workspace grid: main signal
// workspace (modality observations → HR inference → inference response →
// scope/provenance) in columns 1–8, a compact SensorConstellation
// jump-to-plot topology plus replay/fault controls in the columns 9–12
// rail. Collapses to one column in the same semantic reading order at
// tablet/mobile widths.
export default function LiveMonitoringPage() {
  return (
    <div className="mx-auto flex min-w-0 max-w-[1480px] flex-col gap-5 overflow-x-hidden px-0 py-2">
      <RouteHeader
        eyebrow="Live signals / source-aware monitor"
        title="Signal and inference monitor"
        lede="Source-aware physiological signals and fault-aware heart-rate inference for CORE_PLUS_CONTEXT."
        caveat="Recorded replay and synthetic demo data are not live astronaut monitoring."
      />

      <MonitoringSourceStrip />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        <div className="flex flex-col gap-5 lg:col-span-8">
          <FinalSignalStack />
          <HrInferencePanel />
          <InferenceResponseTimeline />
          <ScopeProvenanceFooter />
        </div>
        <div className="flex flex-col gap-5 lg:col-span-4">
          <SensorConstellation compact />
          {PUBLIC_PRESENTATION_MODE ? (
            <PublicPresentationNotice />
          ) : (
            <>
              <ReplaySessionControl />
              <SimulatedFaultControl />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
