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
  VALIDATED_POSITIVE: "text-jury-success",
  VALIDATED_NEGATIVE: "text-jury-fault",
  PARTIAL_EVIDENCE: "text-final-accent",
  CANDIDATE: "text-jury-warning",
  UNVALIDATED: "text-ink-muted",
  NOT_APPLICABLE: "text-ink-muted",
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
      actions={<span className="rounded-full border border-jury-warning/20 bg-jury-warning/[0.06] px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-jury-warning">Reference only</span>}
      contentClassName="space-y-4"
    >
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-3">
        {topology.modules.map((module) => (
          <article key={module.module_id} className="rounded-xl border border-jury-border-subtle bg-surface-2 p-4">
            <div className="flex items-start justify-between gap-2"><div><h3 className="text-sm font-semibold text-ink-primary">{module.label}</h3><p className="mt-1 text-xs text-final-accent">{module.body_location}</p></div><span className="text-xs uppercase text-ink-muted">{module.topology_status.replaceAll("_", " ")}</span></div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">Components</p>
            <p className="mt-1 text-xs leading-relaxed text-ink-secondary">{module.component_ids.join(" · ")}</p>
            <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-ink-muted">Shared once</p>
            <p className="mt-1 text-xs leading-relaxed text-information/80">{module.shared_resources.length ? module.shared_resources.join(" · ") : "Boundary unresolved"}</p>
          </article>
        ))}
      </div>

      <div className="space-y-3">
        {topology.components.map((component) => {
          const hardware = costs.get(component.component_id);
          if (!hardware) return null;
          return (
            <details key={component.component_id} className="rounded-lg border border-jury-border-subtle bg-surface-2">
              <summary className="cursor-pointer px-4 py-3 text-xs font-semibold text-ink-primary">{component.label} <code className="ml-2 text-xs text-final-accent">{component.component_id}</code></summary>
              <div className="grid grid-cols-1 gap-3 border-t border-jury-border-subtle p-4 lg:grid-cols-3">
                <div><p className="text-xs uppercase text-ink-muted">Identity & interface</p><p className="mt-1 text-xs text-ink-secondary">{hardware.identity.manufacturer} {hardware.identity.part_number_or_class}</p><p className="mt-1 text-xs leading-relaxed text-ink-muted">{hardware.identity.rationale}</p><p className="mt-2 text-xs text-final-accent">{hardware.host_interface}</p></div>
                <div><p className="text-xs uppercase text-ink-muted">Component boundary</p><p className="mt-1 text-xs text-ink-secondary">Active: {quantityText(hardware.power_energy.active_power)}</p><p className="mt-1 text-xs text-ink-secondary">Average: {quantityText(hardware.power_energy.average_power)}</p><p className="mt-1 text-xs text-ink-secondary">Daily: {quantityText(hardware.power_energy.daily_energy)}</p><p className="mt-2 text-xs leading-relaxed text-jury-warning/80">Excludes {hardware.power_energy.excluded_subsystems.join(", ")}.</p></div>
                <div><p className="text-xs uppercase text-ink-muted">Physical & data</p><p className="mt-1 text-xs text-ink-secondary">Finished mass: {quantityText(hardware.mass.finished_wearable_mass)}</p><p className="mt-1 text-xs text-ink-secondary">Raw payload: {quantityText(hardware.data_rate.raw_payload_bit_rate)}</p><p className="mt-1 text-xs text-ink-secondary">Embedded latency: {quantityText(hardware.compute_memory.embedded_inference_latency)}</p><p className="mt-2 text-xs leading-relaxed text-ink-muted">Contact: {component.contact_burden.contact_type}</p></div>
              </div>
            </details>
          );
        })}
      </div>

      <div className="overflow-x-auto rounded-lg border border-jury-border-subtle">
        <table className="w-full min-w-[1050px] text-left text-xs">
          <thead className="border-b border-jury-border-subtle uppercase tracking-wide text-ink-muted"><tr><th className="px-3 py-2">Component</th>{targets.map((target) => <th key={target} className="px-3 py-2">{target.replaceAll("_", " ")}</th>)}</tr></thead>
          <tbody className="divide-y divide-jury-border-subtle">
            {topology.stable_component_ids.map((componentId) => (
              <tr key={componentId}>
                <td className="px-3 py-2 font-mono text-final-accent">{componentId}</td>
                {targets.map((target) => {
                  const cell = topology.target_coverage[componentId]?.[target];
                  return cell ? <td key={target} title={cell.note} className={`px-3 py-2 ${STATUS_STYLE[cell.status]}`}>{cell.status.replaceAll("_", " ")}</td> : <td key={target} className="px-3 py-2 text-ink-muted">UNAVAILABLE</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <div className="rounded-lg border border-information/15 bg-information/[0.04] p-4"><p className="flex items-center gap-2 text-xs font-semibold text-information"><LockKeyhole size={13} /> Architecture decision rule — frozen before outcome</p><p className="mt-2 text-xs leading-relaxed text-ink-secondary">Judge each component per target across scientific benefit, operational burden, robustness, and provenance. Allowed outcomes are retain, conditional/intermittent use, deprioritize, remove, or future evidence. No universal scalar score and no outcome has been applied.</p></div>
        <div className="rounded-lg border border-jury-warning/20 bg-jury-warning/[0.05] p-4"><p className="flex items-center gap-2 text-xs font-semibold text-jury-warning"><Gauge size={13} /> Pareto readiness: {readiness.classification}</p><p className="mt-2 text-xs leading-relaxed text-ink-secondary">Global: NO · target-specific: NO · formal analysis authorized: NO. {readiness.limited_structural_conclusion}</p></div>
      </div>

      <details className="rounded-lg border border-jury-border-subtle"><summary className="cursor-pointer px-4 py-3 text-xs text-ink-secondary">Exact remaining blockers ({readiness.blockers.length})</summary><ul className="space-y-1 border-t border-jury-border-subtle p-4 text-xs leading-relaxed text-ink-muted">{readiness.blockers.map((blocker) => <li key={blocker} className="flex gap-2"><CircleOff size={12} className="mt-0.5 shrink-0 text-jury-fault" />{blocker}</li>)}</ul></details>
    </Panel>
  );
}
