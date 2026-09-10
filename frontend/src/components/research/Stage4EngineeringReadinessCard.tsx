import clsx from "clsx";
import { Cpu } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import type { Stage4EngineeringReadiness, Stage4EvidenceClass, Stage4EvidenceQuantity } from "@/lib/types";

// Renders ONLY the typed Stage4EngineeringReadiness projection the backend
// already computed — this component performs no arithmetic and invents no
// number. `evidence_class` is always shown as explicit text (never color
// alone) so a reference-scenario engineering assumption can never be
// mistaken for a frozen datasheet value (governing prompt §25/§34/§35).

const EVIDENCE_LABEL: Record<Stage4EvidenceClass, string> = {
  DATASHEET_DIRECT: "Datasheet (direct)",
  DATASHEET_CALCULATED: "Datasheet (calculated)",
  ENGINEERING_ASSUMPTION: "Engineering assumption",
  ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE: "Mechanical allowance estimate",
  ASSUMED_USE_SCHEDULE: "Assumed use schedule",
};

const EVIDENCE_CLASS: Record<Stage4EvidenceClass, string> = {
  DATASHEET_DIRECT: "border-emerald-400/25 bg-emerald-400/[0.08] text-emerald-300",
  DATASHEET_CALCULATED: "border-emerald-400/20 bg-emerald-400/[0.06] text-emerald-400/90",
  ENGINEERING_ASSUMPTION: "border-amber-400/25 bg-amber-400/[0.08] text-amber-300",
  ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE: "border-amber-400/20 bg-amber-400/[0.06] text-amber-200",
  ASSUMED_USE_SCHEDULE: "border-slate-500/20 bg-slate-500/[0.06] text-slate-400",
};

function EvidencePill({ evidenceClass }: { evidenceClass: Stage4EvidenceClass }) {
  return (
    <span className={clsx("rounded-full border px-2 py-0.5 text-[10px] font-semibold", EVIDENCE_CLASS[evidenceClass])}>
      {EVIDENCE_LABEL[evidenceClass]}
    </span>
  );
}

function QuantityRow({ label, quantity }: { label: string; quantity: Stage4EvidenceQuantity }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/5 py-1.5 last:border-0">
      <span className="text-[11px] text-slate-400">{label}</span>
      <div className="flex items-center gap-2">
        <span className="font-mono text-[12px] text-slate-200">
          {quantity.status === "AVAILABLE" ? quantity.display : "Unavailable"}
        </span>
        <EvidencePill evidenceClass={quantity.evidence_class} />
      </div>
    </div>
  );
}

export function Stage4EngineeringReadinessCard({ readiness }: { readiness: Stage4EngineeringReadiness }) {
  const { system_average_power, system_data_rate, system_mass, bom } = readiness;
  return (
    <Panel
      title="Stage 4 Engineering Readiness"
      subtitle="Power / data-rate / mass / BOM evidence advancement — reference scenario, not a final architecture"
      icon={<Cpu size={16} />}
      contentClassName="space-y-3"
    >
      <p className="text-[11px] leading-relaxed text-slate-500">{readiness.statement}</p>

      <div>
        <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          System average power — {system_average_power.status}
        </p>
        <QuantityRow label="Load-side (base topology)" quantity={system_average_power.base_topology_load_side_mw} />
        <QuantityRow label="Battery-side (÷ regulator efficiency)" quantity={system_average_power.base_topology_battery_side_mw} />
      </div>

      <div>
        <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          System mass — {system_mass.status} ({system_mass.tier_achieved})
        </p>
        <QuantityRow label="Base topology (excl. leg module)" quantity={system_mass.system_mass_base_topology_excl_leg_g} />
        <QuantityRow label="EOG incremental mass" quantity={system_mass.eog_incremental_mass_g} />
      </div>

      <div>
        <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Data rate</p>
        <QuantityRow label="Raw total (base topology)" quantity={system_data_rate.system_raw_total_bps} />
        <QuantityRow label="Transmitted (protocol-overhead adjusted)" quantity={system_data_rate.system_transmitted_bps} />
        <p className="mt-1 text-[10px] text-slate-600">Processed/internal rate: {system_data_rate.processed_data_rate_status}</p>
      </div>

      <div>
        <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          BOM — {bom.not_a_final_bom ? "not a final BOM" : "final"}
        </p>
        <ul className="space-y-1 text-[11px] leading-relaxed text-slate-500">
          {bom.still_missing.map((item) => (
            <li key={item}>• {item}</li>
          ))}
        </ul>
      </div>

      <p className="text-[10px] text-slate-600">
        final_architecture: {readiness.final_architecture_status} · formal_pareto: {readiness.formal_pareto_status}
      </p>
    </Panel>
  );
}
