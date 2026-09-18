import type { Metadata } from "next";

import { FinalSignalStack } from "@/components/monitoring/FinalSignalStack";
import { HrInferencePanel } from "@/components/monitoring/HrInferencePanel";
import { InferenceResponseTimeline } from "@/components/monitoring/InferenceResponseTimeline";
import { MonitoringSessionProvider } from "@/components/monitoring/MonitoringSessionContext";
import { MonitoringSourceStrip } from "@/components/monitoring/MonitoringSourceStrip";
import { ReplaySessionControl } from "@/components/monitoring/ReplaySessionControl";
import { ScopeProvenanceFooter } from "@/components/monitoring/ScopeProvenanceFooter";
import { SimulatedFaultControl } from "@/components/monitoring/SimulatedFaultControl";

export const metadata: Metadata = {
  title: "Signal and Inference Monitor — Biological Minimalism",
};

// Master-prompt 2 §8 — rebuilt as the final signal and inference monitor for
// CORE_PLUS_CONTEXT. Replaces the prior generic mission-control panel grid
// (LiveWaveformsPanel/SensorHealthPanel/TrendPanel/SensorFailureControl,
// which assumed the legacy four-sensor BioZ/temperature demo architecture)
// entirely. Section order is exactly §8.1–§8.8; MonitoringSessionProvider is
// the single fetch boundary for replay/fault session state shared by the
// source strip, replay controls, and fault control below.
export default function LiveMonitoringPage() {
  return (
    <MonitoringSessionProvider>
      <div className="flex flex-col gap-5">
        <div>
          <h1 className="text-lg font-semibold text-slate-100">Signal and inference monitor</h1>
          <p className="mt-1 text-sm text-slate-500">
            Source-aware physiological signals and fault-aware heart-rate inference for the final CORE_PLUS_CONTEXT
            architecture.
          </p>
          <p className="mt-1 text-xs text-slate-600">
            The active source is identified explicitly. Recorded replay and synthetic demo data are not live
            astronaut monitoring.
          </p>
        </div>

        <MonitoringSourceStrip />
        <ReplaySessionControl />
        <FinalSignalStack />
        <HrInferencePanel />
        <SimulatedFaultControl />
        <InferenceResponseTimeline />
        <ScopeProvenanceFooter />
      </div>
    </MonitoringSessionProvider>
  );
}
