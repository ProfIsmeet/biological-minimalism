import type { Metadata } from "next";
import { Gauge } from "lucide-react";

import { AIConfidencePanel } from "@/components/panels/AIConfidencePanel";
import { ExplanationPanel } from "@/components/panels/ExplanationPanel";
import { PrimaryVitalsPanel } from "@/components/panels/PrimaryVitalsPanel";
import { TrendPanel } from "@/components/panels/TrendPanel";

export const metadata: Metadata = {
  title: "AI Insights — Biological Minimalism",
};

export default function AIInsightsPage() {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">AI Insights</h1>
        <p className="text-sm text-slate-500">
          Source-labelled AI output. Replay heart rate comes only from the validated synchronized PPG + IMU model.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <PrimaryVitalsPanel />
        <AIConfidencePanel />
        <TrendPanel
          title="Confidence History"
          subtitle="Overall AI confidence over time"
          icon={<Gauge size={16} />}
          color="#4fd8e8"
          unit="%"
          domain={[0, 100]}
          metric="ai_confidence"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ExplanationPanel target="ai_confidence" title="Why this confidence score?" subtitle="SHAP over sensor signal quality" />
        <ExplanationPanel target="fatigue_risk" title="Why this fatigue estimate?" subtitle="SHAP over HRV, EEG & mission stress" />
      </div>
    </div>
  );
}
