import { Boxes, CircleOff, Gauge, LockKeyhole } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import type {
  HardwareTopologyContract,
  OperationalCostCatalog,
  OperationalQuantity,
  ParetoReadinessDay6,
  TargetEvidenceStatus,
} from "@/lib/types";

function quantityText(quantity: OperationalQuantity): string {
  if (quantity.availability === "unknown") return `Unknown (${quantity.unit})`;
  if (quantity.value !== null) return `${quantity.value.toLocaleString()} ${quantity.unit}`;
  const values = [
    quantity.minimum === null ? null : `min ${quantity.minimum}`,
    quantity.typical === null ? null : `typ ${quantity.typical}`,
    quantity.maximum === null ? null : `max ${quantity.maximum}`,
  ].filter(Boolean);
  return `${values.join(" · ")} ${quantity.unit}`;
}

const STATUS_STYLE: Record<TargetEvidenceStatus, string> = {
  VALIDATED_POSITIVE: "text-emerald-300",
  VALIDATED_NEGATIVE: "text-rose-300",
  PARTIAL_EVIDENCE: "text-cyan-300",
  CANDIDATE: "text-amber-300",
  UNVALIDATED: "text-slate-600",
  NOT_APPLICABLE: "text-slate-600",
};

export function HardwareArchitectureView({
  topology,
  catalog,
  readiness,
}: {
  topology: HardwareTopologyContract;
  catalog: OperationalCostCatalog;
  readiness: ParetoReadinessDay6;
}) {
  const costs = new Map(catalog.components.map((component) => [component.component_id, component.hardware_characterization]));
  const firstComponentId = topology.stable_component_ids.at(0);
  const targets = Object.keys(firstComponentId ? topology.target_coverage[firstComponentId] ?? {} : {});

  return (
    <Panel
      title="Hardware & operational architecture"
      subtitle="Frozen reference topology, representative component classes, and explicit unknowns — not a final BOM"
      icon={<Boxes size={16} />}
      actions={<span className="rounded-full border border-amber-400/20 bg-amber-400/[0.06] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-amber-300">Reference only</span>}
      contentClassName="space-y-4"
    >
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-3">
        {topology.modules.map((module) => (
          <article key={module.module_id} className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
            <div className="flex items-start justify-between gap-2"><div><h3 className="text-sm font-semibold text-slate-200">{module.label}</h3><p className="mt-1 text-[11px] text-cyan-300">{module.body_location}</p></div><span className="text-[9px] uppercase text-slate-500">{module.topology_status.replaceAll("_", " ")}</span></div>
            <p className="mt-3 text-[10px] font-semibold uppercase tracking-wide text-slate-600">Components</p>
            <p className="mt-1 text-[11px] leading-relaxed text-slate-400">{module.component_ids.join(" · ")}</p>
            <p className="mt-3 text-[10px] font-semibold uppercase tracking-wide text-slate-600">Shared once</p>
            <p className="mt-1 text-[11px] leading-relaxed text-violet-300/80">{module.shared_resources.length ? module.shared_resources.join(" · ") : "Boundary unresolved"}</p>
          </article>
        ))}
      </div>

      <div className="space-y-3">
        {topology.components.map((component) => {
          const hardware = costs.get(component.component_id);
          if (!hardware) return null;
          return (
            <details key={component.component_id} className="rounded-lg border border-white/5 bg-white/[0.015]">
              <summary className="cursor-pointer px-4 py-3 text-xs font-semibold text-slate-200">{component.label} <code className="ml-2 text-[9px] text-cyan-400">{component.component_id}</code></summary>
              <div className="grid grid-cols-1 gap-3 border-t border-white/5 p-4 lg:grid-cols-3">
                <div><p className="text-[10px] uppercase text-slate-600">Identity & interface</p><p className="mt-1 text-xs text-slate-300">{hardware.identity.manufacturer} {hardware.identity.part_number_or_class}</p><p className="mt-1 text-[11px] leading-relaxed text-slate-500">{hardware.identity.rationale}</p><p className="mt-2 text-[10px] text-cyan-300">{hardware.host_interface}</p></div>
                <div><p className="text-[10px] uppercase text-slate-600">Component boundary</p><p className="mt-1 text-xs text-slate-300">Active: {quantityText(hardware.power_energy.active_power)}</p><p className="mt-1 text-xs text-slate-300">Average: {quantityText(hardware.power_energy.average_power)}</p><p className="mt-1 text-xs text-slate-300">Daily: {quantityText(hardware.power_energy.daily_energy)}</p><p className="mt-2 text-[10px] leading-relaxed text-amber-300/80">Excludes {hardware.power_energy.excluded_subsystems.join(", ")}.</p></div>
                <div><p className="text-[10px] uppercase text-slate-600">Physical & data</p><p className="mt-1 text-xs text-slate-300">Finished mass: {quantityText(hardware.mass.finished_wearable_mass)}</p><p className="mt-1 text-xs text-slate-300">Raw payload: {quantityText(hardware.data_rate.raw_payload_bit_rate)}</p><p className="mt-1 text-xs text-slate-300">Embedded latency: {quantityText(hardware.compute_memory.embedded_inference_latency)}</p><p className="mt-2 text-[10px] leading-relaxed text-slate-500">Contact: {component.contact_burden.contact_type}</p></div>
              </div>
            </details>
          );
        })}
      </div>

      <div className="overflow-x-auto rounded-lg border border-white/5">
        <table className="w-full min-w-[1050px] text-left text-[10px]">
          <thead className="border-b border-white/5 uppercase tracking-wide text-slate-600"><tr><th className="px-3 py-2">Component</th>{targets.map((target) => <th key={target} className="px-3 py-2">{target.replaceAll("_", " ")}</th>)}</tr></thead>
          <tbody className="divide-y divide-white/5">
            {topology.stable_component_ids.map((componentId) => (
              <tr key={componentId}>
                <td className="px-3 py-2 font-mono text-cyan-300">{componentId}</td>
                {targets.map((target) => {
                  const cell = topology.target_coverage[componentId]?.[target];
                  return cell ? <td key={target} title={cell.note} className={`px-3 py-2 ${STATUS_STYLE[cell.status]}`}>{cell.status.replaceAll("_", " ")}</td> : <td key={target} className="px-3 py-2 text-slate-600">UNAVAILABLE</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <div className="rounded-lg border border-violet-400/15 bg-violet-400/[0.04] p-4"><p className="flex items-center gap-2 text-xs font-semibold text-violet-200"><LockKeyhole size={13} /> Architecture decision rule — frozen before outcome</p><p className="mt-2 text-[11px] leading-relaxed text-slate-400">Judge each component per target across scientific benefit, operational burden, robustness, and provenance. Allowed outcomes are retain, conditional/intermittent use, deprioritize, remove, or future evidence. No universal scalar score and no outcome has been applied.</p></div>
        <div className="rounded-lg border border-amber-400/20 bg-amber-400/[0.05] p-4"><p className="flex items-center gap-2 text-xs font-semibold text-amber-200"><Gauge size={13} /> Pareto readiness: {readiness.classification}</p><p className="mt-2 text-[11px] leading-relaxed text-slate-400">Global: NO · target-specific: NO · formal analysis authorized: NO. {readiness.limited_structural_conclusion}</p></div>
      </div>

      <details className="rounded-lg border border-white/5"><summary className="cursor-pointer px-4 py-3 text-xs text-slate-300">Exact remaining blockers ({readiness.blockers.length})</summary><ul className="space-y-1 border-t border-white/5 p-4 text-[11px] leading-relaxed text-slate-500">{readiness.blockers.map((blocker) => <li key={blocker} className="flex gap-2"><CircleOff size={12} className="mt-0.5 shrink-0 text-rose-300" />{blocker}</li>)}</ul></details>
    </Panel>
  );
}
