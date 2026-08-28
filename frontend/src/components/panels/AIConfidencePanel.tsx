"use client";

import { ShieldCheck } from "lucide-react";

import { LinearMeter } from "@/components/ui/LinearMeter";
import { Panel } from "@/components/ui/Panel";
import { RadialGauge } from "@/components/ui/RadialGauge";
import { confidenceLevel, titleCase } from "@/lib/format";
import { useMissionStore } from "@/store/missionStore";

export function AIConfidencePanel() {
  const confidence = useMissionStore((state) => state.latest?.ai_confidence);

  const entries = Object.entries(confidence?.sensor_contribution ?? {}).sort((a, b) => b[1] - a[1]);

  return (
    <Panel title="AI Confidence" subtitle="Sensor fusion trust & contribution" icon={<ShieldCheck size={16} />}>
      <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-start sm:gap-6">
        <RadialGauge
          value={confidence?.overall_confidence ?? 0}
          label="Overall Confidence"
          level={confidenceLevel(confidence?.overall_confidence ?? 0)}
        />
        <div className="flex w-full flex-1 flex-col gap-3">
          <p className="text-[11px] uppercase tracking-wider text-slate-500">Sensor Contribution</p>
          {entries.length === 0 ? (
            <p className="text-sm text-slate-500">Awaiting telemetry…</p>
          ) : (
            entries.map(([sensor, value]) => (
              <LinearMeter key={sensor} label={titleCase(sensor)} value={value} level="nominal" valueLabel={`${value.toFixed(0)}%`} />
            ))
          )}
        </div>
      </div>
    </Panel>
  );
}
