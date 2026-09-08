import clsx from "clsx";
import { AlertTriangle, Archive, CheckCircle2, CircleDashed, Gauge, Link2, Scale } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import type {
  DecisionInputComponent,
  OperationalQuantity,
  ParetoDecisionInputs,
  ReadinessAvailability,
} from "@/lib/types";

const READINESS_LABELS: Record<ReadinessAvailability, string> = {
  AVAILABLE: "Available",
  PARTIAL: "Partial",
  MISSING: "Missing",
};

const READINESS_CLASS: Record<ReadinessAvailability, string> = {
  AVAILABLE: "border-emerald-400/20 bg-emerald-400/[0.07] text-emerald-300",
  PARTIAL: "border-amber-400/20 bg-amber-400/[0.07] text-amber-300",
  MISSING: "border-slate-500/20 bg-slate-500/[0.06] text-slate-400",
};

const MATRIX_LABELS = {
  scientific_benefit: "Scientific benefit",
  power: "Power",
  mass: "Mass",
  contact_burden: "Contact burden",
  module_burden: "Module burden",
  compute_data_burden: "Compute / data",
  robustness_evidence: "Robustness",
  evidence_provenance: "Provenance",
} as const;

function signed(value: number, digits = 3): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(digits)}`;
}

function quantityValue(quantity: OperationalQuantity | undefined): string {
  if (!quantity || quantity.availability === "unknown") return "Unknown";
  if (quantity.value !== null) return `${quantity.value.toLocaleString()} ${quantity.unit.replaceAll("_", " ")}`;
  return "Known range";
}

function ComponentCard({ component }: { component: DecisionInputComponent }) {
  const science = component.scientific_marginal_value;
  const cost = component.operational_cost;
  const favorable = science.direction === "POSITIVE";
  return (
    <article className="overflow-hidden rounded-xl border border-white/5 bg-white/[0.02]">
      <div className="border-b border-white/5 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-slate-100">{component.label}</h3>
              <code className="rounded bg-space-700/60 px-1.5 py-0.5 text-[10px] text-cyan-300">{component.component_id}</code>
            </div>
            <p className="mt-1.5 text-xs text-slate-500">Heart-rate evidence from {science.dataset_id}; interpreted only within its frozen experiment.</p>
          </div>
          <span className={clsx("rounded-full border px-2.5 py-1 text-[10px] font-semibold", favorable ? "border-emerald-400/20 bg-emerald-400/[0.07] text-emerald-300" : "border-amber-400/20 bg-amber-400/[0.07] text-amber-300")}>
            {science.direction} within experiment
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 p-4 xl:grid-cols-2">
        <section className="rounded-lg border border-cyan-400/15 bg-cyan-400/[0.035] p-3">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-cyan-200"><Gauge size={13} /> Scientific marginal value</p>
          <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
            <div><p className="text-slate-600">Baseline MAE</p><p className="mt-0.5 font-mono text-slate-200">{science.baseline_metrics.mae.mean.toFixed(4)} bpm</p></div>
            <div><p className="text-slate-600">Candidate MAE</p><p className="mt-0.5 font-mono text-slate-200">{science.candidate_metrics.mae.mean.toFixed(4)} bpm</p></div>
            <div><p className="text-slate-600">MAE benefit</p><p className={clsx("mt-0.5 font-mono", favorable ? "text-emerald-300" : "text-amber-300")}>{signed(science.absolute_benefit.mae_bpm)} bpm</p></div>
            <div><p className="text-slate-600">Relative improvement</p><p className={clsx("mt-0.5 font-mono", favorable ? "text-emerald-300" : "text-amber-300")}>{signed(science.relative_improvement.mae_fraction * 100, 2)}%</p></div>
            <div><p className="text-slate-600">RMSE benefit</p><p className="mt-0.5 font-mono text-slate-300">{signed(science.absolute_benefit.rmse_bpm)} bpm</p></div>
            <div><p className="text-slate-600">Evidence strength</p><p className="mt-0.5 text-slate-300">{science.evidence_strength}</p></div>
          </div>
          {science.capacity_confound ? (
            <p className="mt-3 rounded border border-amber-400/25 bg-amber-400/[0.05] px-2.5 py-1.5 text-[10px] leading-relaxed text-amber-200/90">
              Capacity-confounded: the raw MAE benefit above includes model-capacity effect
              {typeof science.capacity_confound.fraction_of_original_gap_explained_by_capacity_alone === "number"
                ? ` (~${Math.round(science.capacity_confound.fraction_of_original_gap_explained_by_capacity_alone * 100)}% of the original gap is capacity alone)`
                : ""}
              . The capacity-controlled genuine sensor benefit is
              {typeof science.capacity_confound.genuine_imu_information_benefit_on_matched_capacity_mae_bpm === "number"
                ? ` ~${science.capacity_confound.genuine_imu_information_benefit_on_matched_capacity_mae_bpm.toFixed(3)} bpm`
                : " smaller"}
              {science.capacity_confound.genuine_imu_information_benefit_seed_consistency
                ? ` (${science.capacity_confound.genuine_imu_information_benefit_seed_consistency} seeds)`
                : ""}
              — do not read the raw benefit as the current pure marginal sensor value.
            </p>
          ) : null}
          <p className="mt-3 text-[11px] leading-relaxed text-slate-500">{Object.values(science.heterogeneity).join(" · ")}</p>
        </section>

        <section className="rounded-lg border border-violet-400/15 bg-violet-400/[0.035] p-3">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-violet-200"><Scale size={13} /> Operational burden</p>
          <dl className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
            <div><dt className="text-slate-600">Power</dt><dd className="mt-0.5 text-slate-300">{quantityValue(cost.dimensions.incremental_power_mw)}</dd></div>
            <div><dt className="text-slate-600">Mass</dt><dd className="mt-0.5 text-slate-300">{quantityValue(cost.dimensions.incremental_mass_g)}</dd></div>
            <div><dt className="text-slate-600">Physical sites added</dt><dd className="mt-0.5 text-slate-300">{quantityValue(cost.dimensions.physical_sensing_sites_added)}</dd></div>
            <div><dt className="text-slate-600">Modules added</dt><dd className="mt-0.5 text-slate-300">{quantityValue(cost.dimensions.additional_module_count)}</dd></div>
            <div><dt className="text-slate-600">Model parameters added</dt><dd className="mt-0.5 text-slate-300">{quantityValue(cost.dimensions.incremental_model_parameters)}</dd></div>
            <div><dt className="text-slate-600">Input values added</dt><dd className="mt-0.5 text-slate-300">{quantityValue(cost.dimensions.model_input_values_per_window_added)}</dd></div>
          </dl>
          <p className="mt-3 text-[11px] leading-relaxed text-amber-300/80">{cost.shared_hardware.double_counting_risk}</p>
          <p className="mt-2 text-[10px] text-slate-600">{cost.known_dimensions.length} quantified dimensions · {cost.unknown_dimensions.length} unresolved dimensions</p>
        </section>
      </div>

      {component.robustness_evidence ? (
        <div className="mx-4 mb-4 rounded-lg border border-emerald-400/15 bg-emerald-400/[0.035] p-3">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-emerald-200"><CheckCircle2 size={13} /> Separate robustness evidence resolved</p>
          <p className="mt-2 text-[11px] leading-relaxed text-slate-400">Official held-out {component.robustness_evidence.subject_id}; {component.robustness_evidence.condition_count} controlled conditions and {component.robustness_evidence.total_condition_windows.toLocaleString()} condition-window opportunities.</p>
          <p className="mt-2 text-[11px] leading-relaxed text-amber-200/80">{component.robustness_evidence.imu_calibration_caveat}</p>
          <p className="mt-1.5 text-[11px] leading-relaxed text-slate-500">{component.robustness_evidence.packet_loss_interpretation}</p>
        </div>
      ) : (
        <div className="mx-4 mb-4 rounded-lg border border-white/5 px-3 py-2 text-[11px] text-slate-500">No component-specific robustness experiment is currently available.</div>
      )}

      <details className="border-t border-white/5">
        <summary className="flex cursor-pointer items-center gap-2 px-4 py-3 text-[11px] font-semibold text-slate-400"><Link2 size={12} /> Provenance and claim boundaries</summary>
        <div className="space-y-2 border-t border-white/5 px-4 py-3 text-[10px] leading-relaxed text-slate-500">
          <p className="break-all font-mono text-cyan-300">{science.provenance.source_artifact}</p>
          <p className="break-all font-mono text-cyan-300">{science.provenance.contract_path}</p>
          <p>{science.claim_boundaries.unsupported.join(" ")}</p>
        </div>
      </details>
    </article>
  );
}

export function DecisionInputsView({ artifact }: { artifact: ParetoDecisionInputs }) {
  const matrixKeys = Object.keys(MATRIX_LABELS) as (keyof typeof MATRIX_LABELS)[];
  return (
    <Panel
      title="Day 5 integrated decision inputs"
      subtitle="Scientific value, operational burden, and robustness remain separate evidence dimensions"
      icon={<CircleDashed size={16} />}
      actions={<span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/25 bg-amber-400/[0.07] px-2.5 py-1 text-[10px] font-semibold text-amber-200"><AlertTriangle size={12} /> PARETO {artifact.readiness.pareto_status}</span>}
      contentClassName="space-y-4"
    >
      <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
        {artifact.components.map((component) => <ComponentCard key={component.component_id} component={component} />)}
      </div>

      <section className="overflow-hidden rounded-lg border border-white/5">
        <div className="border-b border-white/5 px-4 py-3">
          <p className="text-xs font-semibold text-slate-200">Evidence readiness matrix</p>
          <p className="mt-1 text-[11px] text-slate-500">Partial and missing entries stay explicit; qualitative burdens are not converted into coordinates.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-left text-[11px]">
            <thead className="border-b border-white/5 text-[10px] uppercase tracking-wide text-slate-600"><tr><th className="px-3 py-2 font-medium">Component</th>{matrixKeys.map((key) => <th key={key} className="px-3 py-2 font-medium">{MATRIX_LABELS[key]}</th>)}</tr></thead>
            <tbody className="divide-y divide-white/5">
              {artifact.readiness.component_matrix.map((row) => <tr key={row.component_id}><td className="px-3 py-2.5 font-mono text-cyan-300">{row.component_id}</td>{matrixKeys.map((key) => { const value = row[key]; return <td key={key} className="px-3 py-2.5"><span className={clsx("rounded-full border px-2 py-1 text-[9px]", READINESS_CLASS[value])}>{READINESS_LABELS[value]}</span></td>; })}</tr>)}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <section className="rounded-lg border border-amber-400/20 bg-amber-400/[0.045] p-4">
          <p className="text-xs font-semibold text-amber-200">Why final Pareto analysis is not ready</p>
          <ul className="mt-2 space-y-1.5 text-[11px] leading-relaxed text-slate-400">{artifact.readiness.missing_requirements.map((item) => <li key={item}>• {item}</li>)}</ul>
        </section>
        <section className="rounded-lg border border-cyan-400/15 bg-cyan-400/[0.035] p-4">
          <p className="text-xs font-semibold text-cyan-200">Interpretation boundary</p>
          <p className="mt-2 text-[11px] leading-relaxed text-slate-400">{artifact.readiness.cross_dataset_restriction}</p>
          <p className="mt-2 text-[11px] leading-relaxed text-slate-500">{artifact.readiness.limited_structural_observation}</p>
        </section>
      </div>

      <details className="rounded-lg border border-white/5 bg-white/[0.015]">
        <summary className="flex cursor-pointer items-center gap-2 px-4 py-3 text-xs font-semibold text-slate-300"><Archive size={13} /> Integrated source identities ({artifact.source_artifacts.length})</summary>
        <div className="space-y-2 border-t border-white/5 p-4">{artifact.source_artifacts.map((source) => <div key={source.path} className="rounded border border-white/5 p-2 text-[10px]"><p className="font-mono text-cyan-300">{source.path}</p><p className="mt-1 break-all font-mono text-slate-600">SHA256 {source.sha256}</p><p className="mt-1 text-slate-500">{source.role}</p></div>)}</div>
      </details>
    </Panel>
  );
}
