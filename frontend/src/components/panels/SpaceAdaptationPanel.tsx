"use client";

import { Orbit } from "lucide-react";

import { LinearMeter } from "@/components/ui/LinearMeter";
import { Panel } from "@/components/ui/Panel";
import { confidenceLevel, riskLevel } from "@/lib/format";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

export function SpaceAdaptationPanel() {
  const adaptation = useMissionStore((state) => state.latest?.space_adaptation);
  const isReplay = useDatasetReplayMode();

  return (
    <Panel title="Space Adaptation" subtitle="Microgravity / mission-mode physiology" icon={<Orbit size={16} />}>
      {isReplay ? (
        <p className="text-sm leading-relaxed text-slate-500">
          Unavailable during recorded-data replay. Heart rate is the only validated AI target in this integration.
        </p>
      ) : <div className="flex flex-col gap-4">
        <LinearMeter
          label="Fluid Shift Risk"
          value={adaptation?.fluid_shift_risk ?? 0}
          level={riskLevel(adaptation?.fluid_shift_risk ?? 0)}
          valueLabel={adaptation ? `${adaptation.fluid_shift_risk.toFixed(0)}` : "—"}
        />
        <LinearMeter
          label="Autonomic Balance"
          value={adaptation?.autonomic_balance ?? 0}
          level={confidenceLevel(adaptation?.autonomic_balance ?? 0)}
          valueLabel={adaptation ? `${adaptation.autonomic_balance.toFixed(0)}` : "—"}
        />
        <LinearMeter
          label="Thermal Stability"
          value={adaptation?.thermal_stability ?? 0}
          level={confidenceLevel(adaptation?.thermal_stability ?? 0)}
          valueLabel={adaptation ? `${adaptation.thermal_stability.toFixed(0)}` : "—"}
        />
      </div>}
    </Panel>
  );
}
