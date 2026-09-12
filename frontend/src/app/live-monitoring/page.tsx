import type { Metadata } from "next";
import { Waves } from "lucide-react";

import { SensorFailureControl } from "@/components/demos/SensorFailureControl";
import { LiveWaveformsPanel } from "@/components/panels/LiveWaveformsPanel";
import { SensorHealthPanel } from "@/components/panels/SensorHealthPanel";
import { TrendPanel } from "@/components/panels/TrendPanel";

export const metadata: Metadata = {
  title: "Live Monitoring — Biological Minimalism",
};

export default function LiveMonitoringPage() {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Live Monitoring</h1>
        <p className="text-sm text-slate-500">Streaming source-labelled telemetry, updated twice per second.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <LiveWaveformsPanel />
        </div>
        <SensorHealthPanel />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <TrendPanel
          title="HRV Trend"
          subtitle="Heart rate variability (RMSSD)"
          icon={<Waves size={16} />}
          color="#4fd8e8"
          unit="ms"
          metric="hrv_rmssd_ms"
        />
        <TrendPanel
          title="Cognitive Load"
          subtitle="EEG-derived workload estimate"
          icon={<Waves size={16} />}
          color="#f5b942"
          unit="/ 100"
          domain={[0, 100]}
          metric="cognitive_load"
        />
      </div>

      <SensorFailureControl />
    </div>
  );
}
