import clsx from "clsx";
import { Cpu, Database, Layers3, LockKeyhole, Scale, Share2 } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import type {
  CostEvidenceLevel,
  OperationalCostCatalog,
  OperationalCostComponent,
  OperationalQuantity,
  ResearchExperiment,
} from "@/lib/types";

const EVIDENCE_LABELS: Record<CostEvidenceLevel, string> = {
  measured: "Project measured",
  manufacturer_spec: "Manufacturer specification",
  literature_estimate: "Literature estimate",
  derived: "Derived",
  architectural_count: "Architectural count",
  unknown: "Unknown",
};

const DIMENSION_LABELS: Record<string, string> = {
  additional_module_count: "Additional module count",
  baseline_model_parameters: "Baseline model parameters",
  candidate_model_parameters: "Candidate model parameters",
  contact_regions_added: "Contact regions added",
  electrodes_or_contacts_added: "Electrodes or contacts added",
  incremental_inference_latency_ms: "Incremental inference latency",
  incremental_mass_g: "Incremental mass",
  incremental_model_parameters: "Incremental model parameters",
  incremental_power_mw: "Incremental power",
  model_input_values_per_window_added: "Model input values added per window",
  optical_contact_sites_added: "Optical contact sites added",
  physical_sensing_sites_added: "Physical sensing sites added",
  raw_bit_rate_added: "Raw bit rate added",
  raw_sample_throughput_added: "Raw sample throughput added",
};

const UNIT_LABELS: Record<string, string> = {
  bit_per_second: "bit/s",
  contact_regions: "contact regions",
  optical_contact_sites: "optical contact sites",
  physical_sites: "physical sites",
  scalar_samples_per_second: "scalar samples/s",
  scalar_values_per_window: "scalar values/window",
};

function humanize(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function numberText(value: number): string {
  return Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: 4 });
}

function quantityText(quantity: OperationalQuantity): string {
  if (quantity.availability === "unknown") return "Not yet quantified";
  const unit = UNIT_LABELS[quantity.unit] ?? quantity.unit;
  if (quantity.value_kind === "exact" && quantity.value !== null) {
    return `${numberText(quantity.value)} ${unit}`;
  }
  const fields = [
    quantity.minimum === null ? null : `min ${numberText(quantity.minimum)}`,
    quantity.typical === null ? null : `typical ${numberText(quantity.typical)}`,
    quantity.maximum === null ? null : `max ${numberText(quantity.maximum)}`,
  ].filter((item): item is string => item !== null);
  return fields.length ? `${fields.join(" · ")} ${unit}` : "Not yet quantified";
}

function evidenceClass(level: CostEvidenceLevel): string {
  if (level === "unknown") return "border-jury-border-strong/30 bg-surface-3/40 text-ink-secondary";
  if (level === "architectural_count") return "border-information/20 bg-information/[0.07] text-information";
  if (level === "derived") return "border-final-accent/20 bg-final-accent/[0.07] text-final-accent";
  return "border-jury-success/20 bg-jury-success/[0.07] text-jury-success";
}

function QuantityRow({ name, quantity }: { name: string; quantity: OperationalQuantity }) {
  return (
    <tr>
      <td className="px-3 py-2.5">
        <p className="text-ink-secondary">{DIMENSION_LABELS[name] ?? humanize(name)}</p>
        <p className="mt-0.5 text-xs uppercase tracking-wide text-ink-muted">{quantity.basis}</p>
      </td>
      <td className={clsx("px-3 py-2.5 font-mono", quantity.availability === "unknown" ? "text-ink-muted" : "text-ink-primary")}>
        {quantityText(quantity)}
      </td>
      <td className="px-3 py-2.5">
        <span className={clsx("inline-flex rounded-full border px-2 py-1 text-xs", evidenceClass(quantity.evidence_level))}>
          {EVIDENCE_LABELS[quantity.evidence_level]}
        </span>
      </td>
    </tr>
  );
}

function ComponentCostCard({
  component,
  experiments,
}: {
  component: OperationalCostComponent;
  experiments: Record<string, ResearchExperiment>;
}) {
  const linkedExperiments = component.scientific_experiment_ids
    .map((experimentId) => experiments[experimentId])
    .filter((experiment): experiment is ResearchExperiment => experiment !== undefined);
  const known = Object.values(component.dimensions).filter((item) => item.availability === "known").length;
  const unknown = Object.values(component.dimensions).length - known;

  return (
    <article className="overflow-hidden rounded-xl border border-jury-border-subtle bg-surface-2">
      <div className="border-b border-jury-border-subtle p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-ink-primary">{component.label}</h3>
              <code className="rounded bg-surface-3/60 px-1.5 py-0.5 text-xs text-final-accent">{component.component_id}</code>
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">{component.architecture_role}</p>
          </div>
          <span className="rounded-full border border-jury-border-subtle px-2.5 py-1 text-xs text-ink-secondary">{known} known · {unknown} unknown</span>
        </div>
        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
          <div className="rounded border border-jury-border-subtle p-2.5"><p className="text-xs uppercase text-ink-muted">Physical site</p><p className="mt-1 text-xs text-ink-secondary">{component.physical_site}</p></div>
          <div className="rounded border border-jury-border-subtle p-2.5"><p className="text-xs uppercase text-ink-muted">Operation</p><p className="mt-1 text-xs text-ink-secondary">{humanize(component.operation_mode)} · duty cycle {quantityText(component.duty_cycle)}</p></div>
          <div className="rounded border border-jury-border-subtle p-2.5"><p className="text-xs uppercase text-ink-muted">Candidate hardware</p><p className="mt-1 text-xs text-ink-secondary">{component.candidate_hardware_identity ?? "Not selected"}</p></div>
        </div>
        {linkedExperiments.map((experiment) => (
          <div key={experiment.experiment_id} className="mt-3 rounded border border-final-accent/15 bg-final-accent/[0.04] px-3 py-2 text-xs leading-relaxed text-ink-secondary">
            <span className="font-semibold text-final-accent">Scientific evidence remains separate:</span> {experiment.outcome_summary}
          </div>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[630px] text-left text-xs">
          <thead className="border-b border-jury-border-subtle text-xs uppercase tracking-wide text-ink-muted">
            <tr><th className="px-3 py-2 font-medium">Dimension</th><th className="px-3 py-2 font-medium">Value</th><th className="px-3 py-2 font-medium">Evidence</th></tr>
          </thead>
          <tbody className="divide-y divide-jury-border-subtle">
            {Object.entries(component.dimensions).map(([name, quantity]) => <QuantityRow key={name} name={name} quantity={quantity} />)}
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-1 gap-3 border-t border-jury-border-subtle p-4 lg:grid-cols-2">
        <div className="rounded-lg border border-information/15 bg-information/[0.04] p-3">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-information"><Share2 size={13} /> Shared-hardware context</p>
          <p className="mt-2 text-xs leading-relaxed text-ink-secondary">{component.shared_hardware.integration_context}</p>
          <p className="mt-1.5 text-xs leading-relaxed text-jury-warning/80">{component.shared_hardware.double_counting_risk}</p>
        </div>
        <div className="rounded-lg border border-jury-border-subtle p-3">
          <p className="text-xs font-semibold text-ink-secondary">Operational burden proxies</p>
          <ul className="mt-2 space-y-1 text-xs leading-relaxed text-ink-muted">
            {component.operational_burden_proxies.map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </div>
      </div>
    </article>
  );
}

export function OperationalCostView({
  catalog,
  experiments,
}: {
  catalog: OperationalCostCatalog;
  experiments: Record<string, ResearchExperiment>;
}) {
  const mapped = catalog.components.filter((component) => component.status === "scientifically_mapped");
  const placeholders = catalog.components.filter((component) => component.status === "architecture_placeholder");

  return (
    <Panel
      title="Operational cost — multidimensional contract"
      subtitle="Physical and software burden stays in original units; Unknown is never zero"
      icon={<Scale size={16} />}
      actions={<span className="inline-flex items-center gap-1.5 rounded-full border border-jury-warning/20 bg-jury-warning/[0.06] px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-jury-warning"><LockKeyhole size={12} /> No ranking</span>}
      contentClassName="space-y-4"
    >
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="rounded-lg border border-jury-border-subtle bg-surface-1/50 p-3"><p className="flex items-center gap-1.5 text-xs font-semibold text-ink-primary"><Layers3 size={13} className="text-final-accent" /> Separate dimensions</p><p className="mt-1.5 text-xs leading-relaxed text-ink-muted">Power, mass, contacts, modules, compute, and throughput are never blended into an arbitrary score.</p></div>
        <div className="rounded-lg border border-jury-border-subtle bg-surface-1/50 p-3"><p className="flex items-center gap-1.5 text-xs font-semibold text-ink-primary"><Cpu size={13} className="text-final-accent" /> Supported software metrics</p><p className="mt-1.5 text-xs leading-relaxed text-ink-muted">Parameter and sample counts are derived from frozen model/data contracts—not interpreted as embedded power.</p></div>
        <div className="rounded-lg border border-jury-border-subtle bg-surface-1/50 p-3"><p className="flex items-center gap-1.5 text-xs font-semibold text-ink-primary"><Database size={13} className="text-final-accent" /> Provenance required</p><p className="mt-1.5 text-xs leading-relaxed text-ink-muted">Every populated number cites a repository artifact or explicit architectural-count context.</p></div>
      </div>

      <div className="space-y-3">
        {mapped.map((component) => <ComponentCostCard key={component.component_id} component={component} experiments={experiments} />)}
      </div>

      <details className="rounded-lg border border-jury-border-subtle bg-surface-2">
        <summary className="cursor-pointer px-4 py-3 text-xs font-semibold text-ink-secondary">Architecture placeholders ({placeholders.length})</summary>
        <div className="grid grid-cols-1 gap-2 border-t border-jury-border-subtle p-4 sm:grid-cols-2 xl:grid-cols-3">
          {placeholders.map((component) => (
            <div key={component.component_id} className="rounded-lg border border-jury-border-subtle p-3">
              <div className="flex items-center justify-between gap-2"><p className="text-xs font-medium text-ink-secondary">{component.label}</p><code className="text-xs text-ink-muted">{component.component_id}</code></div>
              <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">{component.physical_site}</p>
              <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-jury-warning/80">Costs unknown · no scientific value assigned</p>
            </div>
          ))}
        </div>
      </details>

      <details className="rounded-lg border border-jury-border-subtle bg-surface-2">
        <summary className="cursor-pointer px-4 py-3 text-xs font-semibold text-ink-secondary">Evidence source table ({catalog.evidence.length})</summary>
        <div className="overflow-x-auto border-t border-jury-border-subtle">
          <table className="w-full min-w-[780px] text-left text-xs">
            <thead className="text-xs uppercase tracking-wide text-ink-muted"><tr><th className="px-3 py-2 font-medium">Evidence</th><th className="px-3 py-2 font-medium">Level</th><th className="px-3 py-2 font-medium">Source</th><th className="px-3 py-2 font-medium">Operating condition</th></tr></thead>
            <tbody className="divide-y divide-jury-border-subtle">
              {catalog.evidence.map((record) => <tr key={record.evidence_id}><td className="px-3 py-2.5 text-ink-secondary">{record.title}</td><td className="px-3 py-2.5"><span className={clsx("rounded-full border px-2 py-1 text-xs", evidenceClass(record.evidence_level))}>{EVIDENCE_LABELS[record.evidence_level]}</span></td><td className="px-3 py-2.5 font-mono text-xs text-final-accent">{record.source_url ? <a className="underline decoration-final-accent/30 underline-offset-2" href={record.source_url} target="_blank" rel="noreferrer">{record.manufacturer ?? record.source_reference}</a> : record.source_reference}<p className="mt-1 font-sans text-xs text-ink-muted">{record.page_or_section}</p></td><td className="px-3 py-2.5 text-xs leading-relaxed text-ink-muted">{record.operating_condition}</td></tr>)}
            </tbody>
          </table>
        </div>
      </details>

      <div className="rounded-lg border border-jury-warning/20 bg-jury-warning/[0.05] p-4">
        <p className="flex items-center gap-1.5 text-xs font-semibold text-jury-warning"><LockKeyhole size={13} /> Final Pareto analysis — disabled</p>
        <p className="mt-1.5 text-xs leading-relaxed text-ink-secondary">The reviewed scientific contract remains a separate evidence dimension in the integrated view above. Day 6 adds component-boundary hardware characterization, but unresolved deployable power, mass, duty cycles, and embedded measurements still prevent final multi-objective analysis.</p>
        <p className="mt-2 font-mono text-xs text-ink-muted">Source-contract join key: {catalog.scientific_join_contract.join_key}</p>
      </div>
    </Panel>
  );
}
