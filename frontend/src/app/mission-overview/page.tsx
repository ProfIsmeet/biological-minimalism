import type { Metadata } from "next";

import { AIConfidencePanel } from "@/components/panels/AIConfidencePanel";
import { CognitiveStatusPanel } from "@/components/panels/CognitiveStatusPanel";
import { DigitalTwinPreview } from "@/components/panels/DigitalTwinPreview";
import { PrimaryVitalsPanel } from "@/components/panels/PrimaryVitalsPanel";
import { SensorHealthPanel } from "@/components/panels/SensorHealthPanel";
import { SpaceAdaptationPanel } from "@/components/panels/SpaceAdaptationPanel";
import { MissionModeSwitcher } from "@/components/demos/MissionModeSwitcher";

export const metadata: Metadata = {
  title: "Mission Overview — Biological Minimalism",
};

export default function MissionOverviewPage() {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Mission Overview</h1>
        <p className="text-sm text-slate-500">
          Source-labelled telemetry over WebSocket. Synthetic demo and real recorded-data replay remain explicitly distinguished.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
        <PrimaryVitalsPanel />
        <CognitiveStatusPanel />
        <SpaceAdaptationPanel />
        <AIConfidencePanel />
        <SensorHealthPanel />
        <DigitalTwinPreview />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <MissionModeSwitcher />
      </div>
    </div>
  );
}
