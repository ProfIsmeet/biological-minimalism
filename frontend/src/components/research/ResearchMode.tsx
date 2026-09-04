"use client";

import { useEffect } from "react";
import clsx from "clsx";
import {
  AlertTriangle,
  Archive,
  CheckCircle2,
  ChevronRight,
  CircleSlash2,
  Database,
  FlaskConical,
  Info,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { OperationalCostView } from "@/components/research/OperationalCostView";
import type {
  ResearchBreakdown,
  ResearchBreakdownEntry,
  ResearchConfiguration,
  ResearchExperiment,
  ResearchMetricEstimate,
  ResearchResultClass,
} from "@/lib/types";
import { useResearchStore } from "@/store/researchStore";

const RESULT_PRESENTATION: Record<
  ResearchResultClass,
  { label: string; className: string; icon: typeof CheckCircle2 }
> = {
  positive_marginal_value: {
    label: "Positive marginal value",
    className: "border-emerald-400/25 bg-emerald-400/10 text-emerald-300",
    icon: CheckCircle2,
  },
  negative_marginal_result: {
    label: "Negative marginal result",
    className: "border-amber-400/25 bg-amber-400/10 text-amber-300",
    icon: CircleSlash2,
  },
  robustness_characterization: {
    label: "Robustness characterization",
    className: "border-cyan-400/25 bg-cyan-400/10 text-cyan-300",
    icon: ShieldAlert,
  },
};

function humanize(value: string): string {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function metricText(metric: ResearchMetricEstimate | undefined, precision = 4): string {
  if (!metric || metric.mean === null) return "N/A";
  const scale = metric.unit === "fraction" ? 100 : 1;
  const unit = metric.unit === "fraction" ? "%" : metric.unit;
  const mean = (metric.mean * scale).toFixed(precision);
  const spread = metric.sd === null ? "" : ` ± ${(metric.sd * scale).toFixed(precision)}`;
  return `${mean}${spread} ${unit}`;
}

function signedMetric(metric: ResearchMetricEstimate | null | undefined): string {
  if (!metric || metric.mean === null) return "N/A";
  const prefix = metric.mean > 0 ? "+" : "";
  const spread = metric.sd === null ? "" : ` ± ${metric.sd.toFixed(3)}`;
  return `${prefix}${metric.mean.toFixed(3)}${spread} ${metric.unit}`;
}

function ResultBadge({ resultClass }: { resultClass: ResearchResultClass }) {
  const presentation = RESULT_PRESENTATION[resultClass];
  const Icon = presentation.icon;
  return (
    <span className={clsx("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide", presentation.className)}>
      <Icon size={13} />
      {presentation.label}
    </span>
  );
}

function OverviewCard({
  experiment,
  selected,
  onSelect,
}: {
  experiment: ResearchExperiment;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={clsx(
        "group flex min-h-56 flex-col rounded-xl border p-4 text-left transition-colors",
        selected
          ? "border-cyan-400/35 bg-cyan-400/[0.07]"
          : "border-white/5 bg-white/[0.025] hover:border-white/15 hover:bg-white/[0.04]",
      )}
      aria-pressed={selected}
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <ResultBadge resultClass={experiment.result_class} />
        <ChevronRight size={17} className={clsx("mt-1 shrink-0", selected ? "text-cyan-300" : "text-slate-600 group-hover:text-slate-400")} />
      </div>
      <h3 className="text-sm font-semibold leading-snug text-slate-100">{experiment.title}</h3>
      <p className="mt-2 text-xs leading-relaxed text-slate-400">{experiment.outcome_summary}</p>
      <div className="mt-auto grid grid-cols-2 gap-2 pt-4 text-[11px]">
        <div>
          <p className="uppercase tracking-wide text-slate-600">Target</p>
          <p className="mt-0.5 text-slate-300">{experiment.target}</p>
        </div>
        <div>
          <p className="uppercase tracking-wide text-slate-600">Held out</p>
          <p className="mt-0.5 text-slate-300">{experiment.scope.held_out_subjects.length} subject{experiment.scope.held_out_subjects.length === 1 ? "" : "s"}</p>
        </div>
      </div>
    </button>
  );
}

function configurationById(experiment: ResearchExperiment, id: string): ResearchConfiguration | undefined {
  return experiment.configurations.find((configuration) => configuration.configuration_id === id);
}

function MarginalValueTable({ experiments }: { experiments: ResearchExperiment[] }) {
  const marginalExperiments = experiments.filter((experiment) => experiment.marginal_result !== null);
  return (
    <Panel
      title="Measured marginal sensor value"
      subtitle="Target- and dataset-specific experimental evaluation metrics — never a global sensor score"
      icon={<FlaskConical size={16} />}
      contentClassName="overflow-x-auto p-0"
    >
      <table className="w-full min-w-[880px] text-left text-xs">
        <thead className="border-b border-white/5 bg-white/[0.02] text-[10px] uppercase tracking-wider text-slate-500">
          <tr>
            <th className="px-4 py-3 font-medium">Experiment / target</th>
            <th className="px-4 py-3 font-medium">Baseline</th>
            <th className="px-4 py-3 font-medium">Added sensing</th>
            <th className="px-4 py-3 text-right font-medium">Baseline MAE</th>
            <th className="px-4 py-3 text-right font-medium">Candidate MAE</th>
            <th className="px-4 py-3 text-right font-medium">ΔMAE</th>
            <th className="px-4 py-3 font-medium">Result</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {marginalExperiments.map((experiment) => {
            const marginal = experiment.marginal_result;
            if (!marginal) return null;
            const baseline = configurationById(experiment, marginal.baseline_configuration_id);
            const candidate = configurationById(experiment, marginal.candidate_configuration_id);
            return (
              <tr key={experiment.experiment_id} className="text-slate-300">
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-200">{experiment.dataset}</p>
                  <p className="mt-0.5 text-[11px] text-slate-500">{experiment.target}</p>
                </td>
                <td className="px-4 py-3">{baseline?.label ?? marginal.baseline_configuration_id}</td>
                <td className="px-4 py-3">{marginal.added_sensing}</td>
                <td className="tabular-nums-mono px-4 py-3 text-right">{metricText(baseline?.metrics.mae)}</td>
                <td className="tabular-nums-mono px-4 py-3 text-right">{metricText(candidate?.metrics.mae)}</td>
                <td className={clsx("tabular-nums-mono px-4 py-3 text-right font-semibold", marginal.direction === "improved" ? "text-emerald-300" : "text-amber-300")}>{signedMetric(marginal.delta)}</td>
                <td className="px-4 py-3"><ResultBadge resultClass={experiment.result_class} /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Panel>
  );
}

function ConfigurationGrid({ experiment }: { experiment: ResearchExperiment }) {
  return (
    <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
      {experiment.configurations.map((configuration) => (
        <article key={configuration.configuration_id} className="rounded-lg border border-white/5 bg-white/[0.025] p-4">
          <p className="text-xs font-semibold text-slate-200">{configuration.label}</p>
          <p className="mt-1.5 min-h-10 text-[11px] leading-relaxed text-slate-500">{configuration.description}</p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {configuration.sensing.map((sensor) => (
              <span key={sensor} className="rounded bg-slate-700/40 px-2 py-1 text-[10px] text-slate-300">{sensor}</span>
            ))}
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-2">
            {Object.entries(configuration.metrics).map(([metricName, metric]) => (
              <div key={metricName} className="rounded-md border border-white/5 bg-space-900/60 p-2.5">
                <dt className="text-[10px] uppercase tracking-wide text-slate-600">{humanize(metricName)}</dt>
                <dd className="tabular-nums-mono mt-1 text-xs text-slate-200">{metricText(metric)}</dd>
                {metric.n !== null ? <p className="mt-1 text-[10px] text-slate-600">N = {metric.n.toLocaleString()}</p> : null}
              </div>
            ))}
          </dl>
        </article>
      ))}
    </div>
  );
}

function deltaClass(entry: ResearchBreakdownEntry): string {
  if (entry.delta?.mean === null || entry.delta?.mean === undefined) return "text-slate-500";
  if (Math.abs(entry.delta.mean) < 0.05) return "text-slate-300";
  return entry.delta.mean < 0 ? "text-emerald-300" : "text-amber-300";
}

function BreakdownTable({ breakdown, experiment }: { breakdown: ResearchBreakdown; experiment: ResearchExperiment }) {
  return (
    <div className="overflow-hidden rounded-lg border border-white/5">
      <div className="border-b border-white/5 bg-white/[0.025] px-3 py-2.5">
        <h4 className="text-xs font-semibold text-slate-300">{breakdown.title}</h4>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[620px] text-left text-xs">
          <thead className="text-[10px] uppercase tracking-wide text-slate-600">
            <tr>
              <th className="px-3 py-2 font-medium">Group</th>
              {experiment.configurations.map((configuration) => (
                <th key={configuration.configuration_id} className="px-3 py-2 text-right font-medium">{configuration.label} MAE</th>
              ))}
              <th className="px-3 py-2 text-right font-medium">Candidate − baseline</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {breakdown.entries.map((entry) => (
              <tr key={entry.entry_id}>
                <td className="px-3 py-2.5 text-slate-300">{entry.label}</td>
                {experiment.configurations.map((configuration) => (
                  <td key={configuration.configuration_id} className="tabular-nums-mono px-3 py-2.5 text-right text-slate-300">
                    {metricText(entry.configuration_metrics[configuration.configuration_id]?.mae, 3)}
                  </td>
                ))}
                <td className={clsx("tabular-nums-mono px-3 py-2.5 text-right font-medium", deltaClass(entry))}>{signedMetric(entry.delta)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FaultRows({ entries }: { entries: ResearchBreakdownEntry[] }) {
  return (
    <table className="w-full min-w-[850px] text-left text-xs">
      <thead className="text-[10px] uppercase tracking-wide text-slate-600">
        <tr>
          <th className="px-3 py-2 font-medium">Condition</th>
          <th className="px-3 py-2 font-medium">Target</th>
          <th className="px-3 py-2 text-right font-medium">Severity</th>
          <th className="px-3 py-2 text-right font-medium">Availability</th>
          <th className="px-3 py-2 text-right font-medium">Valid-only MAE</th>
          <th className="px-3 py-2 text-right font-medium">Valid-only RMSE</th>
          <th className="px-3 py-2 text-right font-medium">ΔMAE</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-white/5">
        {entries.map((entry) => {
          const metrics = entry.configuration_metrics.canonical_pipeline;
          return (
            <tr key={entry.entry_id}>
              <td className="max-w-72 px-3 py-2.5 font-mono text-[11px] text-slate-300">{entry.label}</td>
              <td className="px-3 py-2.5 text-slate-400">{String(entry.dimensions.target ?? "—")}</td>
              <td className="tabular-nums-mono px-3 py-2.5 text-right text-slate-400">{entry.dimensions.severity === null ? "—" : String(entry.dimensions.severity)}</td>
              <td className="tabular-nums-mono px-3 py-2.5 text-right text-cyan-300">{metricText(metrics?.availability, 2)}</td>
              <td className="tabular-nums-mono px-3 py-2.5 text-right text-slate-300">{metricText(metrics?.mae, 3)}</td>
              <td className="tabular-nums-mono px-3 py-2.5 text-right text-slate-300">{metricText(metrics?.rmse, 3)}</td>
              <td className={clsx("tabular-nums-mono px-3 py-2.5 text-right", deltaClass(entry))}>{signedMetric(entry.delta)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function RobustnessDetail({ experiment }: { experiment: ResearchExperiment }) {
  const aggregates = experiment.breakdowns.find((item) => item.breakdown_id === "stochastic_fault_aggregates");
  const conditions = experiment.breakdowns.find((item) => item.breakdown_id === "fault_conditions");
  const deterministic = conditions?.entries.filter((entry) => entry.dimensions.stochastic === false) ?? [];
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        <div className="rounded-lg border border-rose-400/15 bg-rose-400/[0.05] p-4">
          <p className="text-xs font-semibold text-rose-200">Accuracy degradation</p>
          <p className="mt-1.5 text-[11px] leading-relaxed text-slate-400">PPG additive noise increased valid-prediction error while availability remained 100%.</p>
        </div>
        <div className="rounded-lg border border-cyan-400/15 bg-cyan-400/[0.05] p-4">
          <p className="text-xs font-semibold text-cyan-200">Availability loss</p>
          <p className="mt-1.5 text-[11px] leading-relaxed text-slate-400">Dropout, flat/full-saturated PPG, and native sample loss caused explicit rejection. Rejected windows have N/A accuracy.</p>
        </div>
        <div className="rounded-lg border border-amber-400/20 bg-amber-400/[0.06] p-4">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-amber-200"><AlertTriangle size={13} /> IMU calibration caveat</p>
          <p className="mt-1.5 text-[11px] leading-relaxed text-slate-400">Fault amplitude used the first affected S14 batch, whose motion variance was substantially below typical later windows. Small degradation is valid only for that implemented perturbation—not universally severe IMU corruption.</p>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-white/5">
        <div className="border-b border-white/5 bg-white/[0.025] px-3 py-2.5">
          <h4 className="text-xs font-semibold text-slate-300">Five-seed stochastic aggregates</h4>
          <p className="mt-0.5 text-[10px] text-slate-600">Availability and valid-only accuracy remain separate; N/A is preserved when no valid prediction exists.</p>
        </div>
        <div className="overflow-x-auto">{aggregates ? <FaultRows entries={aggregates.entries} /> : <p className="p-4 text-xs text-rose-300">Aggregate artifact section unavailable.</p>}</div>
      </div>

      <details className="rounded-lg border border-white/5 bg-white/[0.015]">
        <summary className="cursor-pointer px-4 py-3 text-xs font-semibold text-slate-300">Deterministic fault conditions ({deterministic.length})</summary>
        <div className="overflow-x-auto border-t border-white/5"><FaultRows entries={deterministic} /></div>
      </details>
      <details className="rounded-lg border border-white/5 bg-white/[0.015]">
        <summary className="cursor-pointer px-4 py-3 text-xs font-semibold text-slate-300">All concrete conditions ({conditions?.entries.length ?? 0})</summary>
        <div className="overflow-x-auto border-t border-white/5">{conditions ? <FaultRows entries={conditions.entries} /> : null}</div>
      </details>

      <p className="rounded-lg border border-white/5 bg-space-900/50 px-4 py-3 text-xs leading-relaxed text-slate-400">
        Packet loss is a <strong className="font-semibold text-slate-200">fail-closed pipeline availability</strong> result: the current path requires complete contiguous native-rate windows. It is not evidence that neural-network MAE explodes, and surviving windows form small selected subsets.
      </p>
    </div>
  );
}

function ClaimBoundaries({ experiment }: { experiment: ResearchExperiment }) {
  const groups = [
    { title: "Supported", items: experiment.claim_boundaries.supported, className: "text-emerald-300", icon: CheckCircle2 },
    { title: "Not supported", items: experiment.claim_boundaries.unsupported, className: "text-rose-300", icon: CircleSlash2 },
    { title: "Limitations", items: experiment.claim_boundaries.limitations, className: "text-amber-300", icon: AlertTriangle },
  ];
  return (
    <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
      {groups.map((group) => {
        const Icon = group.icon;
        return (
          <section key={group.title} className="rounded-lg border border-white/5 bg-white/[0.02] p-4">
            <h4 className={clsx("flex items-center gap-1.5 text-xs font-semibold", group.className)}><Icon size={13} /> {group.title}</h4>
            <ul className="mt-3 space-y-2 text-[11px] leading-relaxed text-slate-400">
              {group.items.map((item) => <li key={item} className="border-l border-white/10 pl-2.5">{item}</li>)}
            </ul>
          </section>
        );
      })}
    </div>
  );
}

function Provenance({ experiment }: { experiment: ResearchExperiment }) {
  const provenance = experiment.provenance;
  return (
    <details className="rounded-lg border border-white/5 bg-white/[0.015]">
      <summary className="flex cursor-pointer items-center gap-2 px-4 py-3 text-xs font-semibold text-slate-300"><Archive size={14} className="text-cyan-400" /> Provenance and artifact identity</summary>
      <div className="grid grid-cols-1 gap-4 border-t border-white/5 p-4 text-[11px] lg:grid-cols-2">
        <dl className="space-y-2">
          <div><dt className="text-slate-600">Evidence level</dt><dd className="mt-0.5 text-slate-300">Experimental evaluation metric</dd></div>
          <div><dt className="text-slate-600">Environment</dt><dd className="mt-0.5 text-slate-300">{humanize(experiment.scope.environment_scope)}</dd></div>
          <div><dt className="text-slate-600">Dataset version</dt><dd className="mt-0.5 text-slate-300">{provenance.dataset_version ?? "Not specified"}</dd></div>
          <div><dt className="text-slate-600">Split identity</dt><dd className="mt-0.5 break-all font-mono text-slate-300">{provenance.split_identity ?? "Not specified"}</dd></div>
          <div><dt className="text-slate-600">Source artifact</dt><dd className="mt-0.5 break-all font-mono text-cyan-300">{provenance.source_artifact}</dd></div>
        </dl>
        <div className="space-y-3">
          <div><p className="text-slate-600">Model identity</p><ul className="mt-1 space-y-1 font-mono text-slate-300">{provenance.model_identity.map((item) => <li key={item}>{item}</li>)}</ul></div>
          <div><p className="text-slate-600">Supporting artifacts</p><ul className="mt-1 space-y-1 font-mono text-slate-400">{provenance.supporting_artifacts.map((item) => <li key={item} className="break-all">{item}</li>)}</ul></div>
          {provenance.checkpoints.length ? <div><p className="text-slate-600">Checkpoint identities (artifact paths intentionally omitted)</p><ul className="mt-1 space-y-2">{provenance.checkpoints.map((checkpoint) => <li key={checkpoint.run_id} className="rounded border border-white/5 p-2 font-mono text-slate-400"><span className="text-slate-300">{checkpoint.run_id}</span><br />SHA256 {checkpoint.sha256}<br />{checkpoint.size_bytes.toLocaleString()} bytes</li>)}</ul></div> : null}
        </div>
      </div>
    </details>
  );
}

function ExperimentDetail({ experiment }: { experiment: ResearchExperiment }) {
  const regularBreakdowns = experiment.breakdowns.filter((breakdown) => !["fault_condition", "fault_aggregate"].includes(breakdown.kind));
  return (
    <Panel
      title={experiment.title}
      subtitle={experiment.research_question}
      icon={<Database size={16} />}
      actions={<ResultBadge resultClass={experiment.result_class} />}
      contentClassName="space-y-5"
    >
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3"><p className="text-[10px] uppercase tracking-wide text-slate-600">Dataset</p><p className="mt-1 text-xs text-slate-200">{experiment.dataset}</p></div>
        <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3"><p className="text-[10px] uppercase tracking-wide text-slate-600">Target</p><p className="mt-1 text-xs text-slate-200">{experiment.target}</p></div>
        <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3"><p className="text-[10px] uppercase tracking-wide text-slate-600">Held-out subjects</p><p className="tabular-nums-mono mt-1 text-xs text-slate-200">{experiment.scope.held_out_subjects.length} / {experiment.scope.subjects.length}</p></div>
        <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3"><p className="text-[10px] uppercase tracking-wide text-slate-600">Evaluation windows</p><p className="tabular-nums-mono mt-1 text-xs text-slate-200">{experiment.scope.evaluation_windows.toLocaleString()}</p></div>
      </div>

      <ConfigurationGrid experiment={experiment} />

      {experiment.marginal_result ? (
        <div className={clsx("rounded-lg border p-4", experiment.marginal_result.direction === "improved" ? "border-emerald-400/20 bg-emerald-400/[0.05]" : "border-amber-400/20 bg-amber-400/[0.05]")}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs font-semibold text-slate-200">Marginal result: {humanize(experiment.marginal_result.direction)}</p>
            <p className="tabular-nums-mono text-sm font-semibold text-slate-100">ΔMAE {signedMetric(experiment.marginal_result.delta)}</p>
          </div>
          <p className="mt-2 text-xs text-slate-400">Added sensing: {experiment.marginal_result.added_sensing}</p>
          {experiment.marginal_result.paired_replicates !== null ? <p className="mt-1 text-xs text-slate-400">Paired seeds: {experiment.marginal_result.candidate_worsened_count}/{experiment.marginal_result.paired_replicates} worse for candidate; {experiment.marginal_result.candidate_improved_count}/{experiment.marginal_result.paired_replicates} improved.</p> : null}
          <ul className="mt-3 space-y-1.5 text-[11px] leading-relaxed text-slate-400">{experiment.marginal_result.notes.map((note) => <li key={note}>• {note}</li>)}</ul>
        </div>
      ) : null}

      {experiment.result_class === "robustness_characterization" ? <RobustnessDetail experiment={experiment} /> : (
        <div className="space-y-3">{regularBreakdowns.map((breakdown) => <BreakdownTable key={breakdown.breakdown_id} breakdown={breakdown} experiment={experiment} />)}</div>
      )}

      <ClaimBoundaries experiment={experiment} />
      <Provenance experiment={experiment} />
    </Panel>
  );
}

function LoadingState() {
  return (
    <div className="grid grid-cols-1 gap-3 lg:grid-cols-3" aria-label="Loading research artifacts">
      {[0, 1, 2].map((item) => <div key={item} className="h-56 animate-pulse rounded-xl border border-white/5 bg-white/[0.025]" />)}
    </div>
  );
}

export function ResearchMode() {
  const {
    summaries,
    projectSummary,
    operationalCostCatalog,
    operationalCostError,
    experiments,
    selectedExperimentId,
    loading,
    error,
    load,
    selectExperiment,
  } = useResearchStore();

  useEffect(() => {
    void load();
  }, [load]);

  const experimentList = summaries
    .map((item) => experiments[item.experiment_id])
    .filter((experiment): experiment is ResearchExperiment => experiment !== undefined);
  const selected = selectedExperimentId ? experiments[selectedExperimentId] : undefined;

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col justify-between gap-3 lg:flex-row lg:items-end">
        <div>
          <div className="mb-1.5 flex items-center gap-2 text-cyan-400"><FlaskConical size={18} /><span className="text-[11px] font-semibold uppercase tracking-[0.18em]">Research Mode</span></div>
          <h1 className="text-xl font-semibold text-slate-100">Measured marginal sensor evidence</h1>
          <p className="mt-1 max-w-4xl text-sm leading-relaxed text-slate-500">Biological Minimalism evaluates each added sensing component by measured target-specific marginal value rather than assuming more sensors are inherently better.</p>
        </div>
        {projectSummary ? <div className="flex gap-2 text-[11px]"><span className="rounded-full border border-white/10 px-2.5 py-1 text-slate-400">{projectSummary.available_count}/{projectSummary.experiment_count} artifacts available</span><span className="rounded-full border border-emerald-400/20 bg-emerald-400/[0.05] px-2.5 py-1 text-emerald-300">Read only</span></div> : null}
      </header>

      <div className="flex items-start gap-2 rounded-lg border border-cyan-400/15 bg-cyan-400/[0.04] px-4 py-3 text-xs leading-relaxed text-slate-400">
        <Info size={15} className="mt-0.5 shrink-0 text-cyan-400" />
        <p>MAE and RMSE here are frozen <strong className="font-semibold text-slate-200">experimental evaluation metrics</strong>. They are not live measurements, current-person confidence, or predictive uncertainty.</p>
      </div>

      {error ? (
        <div role="alert" className="flex items-start justify-between gap-4 rounded-lg border border-rose-400/20 bg-rose-400/[0.06] px-4 py-3">
          <div className="flex gap-2"><AlertTriangle size={15} className="mt-0.5 shrink-0 text-rose-300" /><div><p className="text-xs font-semibold text-rose-200">Research artifact loading issue</p><p className="mt-1 text-[11px] leading-relaxed text-slate-400">{error}</p></div></div>
          <button type="button" onClick={() => void load()} className="flex shrink-0 items-center gap-1.5 rounded border border-white/10 px-2.5 py-1.5 text-[11px] text-slate-300 hover:bg-white/5"><RefreshCw size={12} /> Retry</button>
        </div>
      ) : null}

      {loading && !experimentList.length ? <LoadingState /> : (
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          {experimentList.map((experiment) => <OverviewCard key={experiment.experiment_id} experiment={experiment} selected={experiment.experiment_id === selectedExperimentId} onSelect={() => selectExperiment(experiment.experiment_id)} />)}
          {!experimentList.length && !loading ? <p className="col-span-full rounded-lg border border-white/5 p-5 text-sm text-slate-500">No validated research artifacts are available.</p> : null}
        </div>
      )}

      {experimentList.length ? <MarginalValueTable experiments={experimentList} /> : null}
      {operationalCostError ? <p role="alert" className="rounded-lg border border-rose-400/20 bg-rose-400/[0.06] px-4 py-3 text-xs text-rose-200">Operational-cost catalog unavailable: {operationalCostError}</p> : null}
      {operationalCostCatalog ? <OperationalCostView catalog={operationalCostCatalog} experiments={experiments} /> : null}
      {selected ? <ExperimentDetail experiment={selected} /> : null}

      {projectSummary ? (
        <footer className="rounded-lg border border-white/5 bg-white/[0.015] px-4 py-3 text-xs leading-relaxed text-slate-500">{projectSummary.statement} Operational costs remain separate, provenance-bearing dimensions; no Pareto score or final architecture ranking is calculated.</footer>
      ) : null}
    </div>
  );
}
