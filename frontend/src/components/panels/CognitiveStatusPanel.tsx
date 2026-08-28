"use client";

import { BrainCircuit } from "lucide-react";

import { LinearMeter } from "@/components/ui/LinearMeter";
import { Panel } from "@/components/ui/Panel";
import { riskLevel, confidenceLevel } from "@/lib/format";
import { useMissionStore } from "@/store/missionStore";

export function CognitiveStatusPanel() {
  const cognitive = useMissionStore((state) => state.latest?.cognitive);

  return (
    <Panel title="Cognitive Status" subtitle="EEG-derived workload & alertness" icon={<BrainCircuit size={16} />}>
      <div className="flex flex-col gap-4">
        <LinearMeter label="Cognitive Load" value={cognitive?.cognitive_load ?? 0} level={riskLevel(cognitive?.cognitive_load ?? 0)} valueLabel={cognitive ? `${cognitive.cognitive_load.toFixed(0)}` : "—"} />
        <LinearMeter label="Fatigue" value={cognitive?.fatigue ?? 0} level={riskLevel(cognitive?.fatigue ?? 0)} valueLabel={cognitive ? `${cognitive.fatigue.toFixed(0)}` : "—"} />
        <LinearMeter
          label="Circadian Stability"
          value={cognitive?.circadian_stability ?? 0}
          level={confidenceLevel(cognitive?.circadian_stability ?? 0)}
          valueLabel={cognitive ? `${cognitive.circadian_stability.toFixed(0)}` : "—"}
        />
        <LinearMeter
          label="EEG Attention"
          value={cognitive?.eeg_attention ?? 0}
          level={confidenceLevel(cognitive?.eeg_attention ?? 0)}
          valueLabel={cognitive ? `${cognitive.eeg_attention.toFixed(0)}` : "—"}
        />
      </div>
    </Panel>
  );
}
