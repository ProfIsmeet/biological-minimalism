import clsx from "clsx";
import { AlertTriangle, Cpu, Gauge, Radio, Scale, ShieldQuestion } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import type {
  EngineeringCandidate,
  EngineeringQuantity,
  EngineeringReadiness,
  EngineeringReadinessLevel,
} from "@/lib/types";

// Render a typed engineering quantity (audit H4/§9). An UNKNOWN quantity is
// shown as "Unknown" in amber — never as a fabricated 0.
function QuantityValue({ quantity, prefix = "" }: { quantity: EngineeringQuantity; prefix?: string }) {
  if (quantity.status !== "AVAILABLE" || quantity.value === null) {
    return (
      <p className="mt-0.5 font-mono text-amber-300" title={quantity.reason_if_unavailable ?? undefined}>
        {quantity.display}
      </p>
    );
  }
  return <p className="mt-0.5 font-mono text-slate-200">{prefix}{quantity.display}</p>;
}

const LEVEL_LABEL: Record<EngineeringReadinessLevel, string> = {
  AVAILABLE: "Available",
  PARTIAL: "Partial",
  NOT_READY: "Not ready",
  MISSING: "Missing",
};

const LEVEL_CLASS: Record<EngineeringReadinessLevel, string> = {
  AVAILABLE: "border-emerald-400/20 bg-emerald-400/[0.07] text-emerald-300",
  PARTIAL: "border-amber-400/20 bg-amber-400/[0.07] text-amber-300",
  NOT_READY: "border-slate-500/25 bg-slate-500/[0.08] text-slate-300",
  MISSING: "border-slate-500/20 bg-slate-500/[0.06] text-slate-400",
};

function LevelPill({ level }: { level: EngineeringReadinessLevel }) {
  return (
    <span className={clsx("rounded-full border px-2 py-0.5 text-[10px] font-semibold", LEVEL_CLASS[level])}>
      {LEVEL_LABEL[level]}
    </span>
  );
}

function gateClass(gate: string): string {
  if (gate.startsWith("CONDITIONAL")) return "border-amber-400/25 bg-amber-400/[0.07] text-amber-200";
  if (gate.startsWith("DEPRIORITIZE")) return "border-rose-400/25 bg-rose-400/[0.06] text-rose-200";
  return "border-slate-500/20 bg-slate-500/[0.06] text-slate-300";
}

function CandidateCard({ candidate }: { candidate: EngineeringCandidate }) {
  return (
    <article className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">{candidate.label}</h3>
          <p className="mt-0.5 text-[11px] text-slate-500">{candidate.scientific_target}</p>
        </div>
        <span className={clsx("rounded-full border px-2.5 py-1 text-[10px] font-semibold", gateClass(candidate.gate_status))}>
          {candidate.gate_status.replaceAll("_", " ")}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
        <div><p className="text-slate-600">Scientific direction</p><p className="mt-0.5 text-slate-300">{candidate.scientific_direction}</p></div>
        <div><p className="text-slate-600">New sensing contacts</p><QuantityValue quantity={candidate.incremental_sensing_contacts} prefix="+" /></div>
        <div><p className="text-slate-600">New body region</p><p className="mt-0.5 text-slate-300">{candidate.incremental_body_region}</p></div>
        <div><p className="text-slate-600">New module</p><p className="mt-0.5 text-slate-300">{candidate.incremental_module}</p></div>
        <div className="col-span-2">
          <p className="text-slate-600">Reference component power</p>
          <p className="mt-0.5 flex flex-wrap items-center gap-1.5 text-slate-300">
            <span>{candidate.reference_component_power_display}</span>
            <LevelPill level={candidate.reference_component_power_status} />
          </p>
        </div>
        <div><p className="text-slate-600">Raw data-rate increment</p><QuantityValue quantity={candidate.raw_data_rate_increment} /></div>
        <div><p className="text-slate-600">Mass / BOM</p><p className="mt-0.5 text-slate-300">{candidate.mass_tier} · {candidate.bom_readiness}</p></div>
      </div>

      <p className="mt-3 border-l border-white/10 pl-2.5 text-[11px] leading-relaxed text-slate-400">{candidate.engineering_summary}</p>
      <p className="mt-2 flex items-start gap-1.5 text-[11px] leading-relaxed text-amber-300/80"><AlertTriangle size={12} className="mt-0.5 shrink-0" /> {candidate.caveat}</p>
    </article>
  );
}

function panelIcon(dimension: string) {
  if (dimension.toLowerCase().includes("power")) return <Gauge size={13} />;
  if (dimension.toLowerCase().includes("mass")) return <Scale size={13} />;
  if (dimension.toLowerCase().includes("data")) return <Radio size={13} />;
  return <Cpu size={13} />;
}

export function EngineeringReadinessView({ readiness }: { readiness: EngineeringReadiness }) {
  return (
    <Panel
      title="Engineering readiness (Day 11)"
      subtitle="Historical pre-selection burden evidence used to inform the final conditional architecture decision."
      icon={<ShieldQuestion size={16} />}
      actions={
        <span className="inline-flex items-center gap-1.5 rounded-full border border-experimental/30 bg-experimental-soft px-2.5 py-1 text-[10px] font-semibold text-experimental">
          Historical pre-selection artifact
        </span>
      }
      contentClassName="space-y-4"
    >
      <p className="text-[11px] leading-relaxed text-slate-500">
        {readiness.statement} This artifact&rsquo;s own <code>final_architecture_status</code> field
        (&ldquo;{readiness.final_architecture_status}&rdquo;) is preserved verbatim below as raw historical record — the
        final selection, CORE_PLUS_CONTEXT, is recorded separately in the Stage-4 closure artifact shown further down
        this archive.
      </p>

      <section className="overflow-hidden rounded-lg border border-white/5">
        <div className="border-b border-white/5 px-4 py-3">
          <p className="text-xs font-semibold text-slate-200">System readiness panel</p>
          <p className="mt-1 text-[11px] text-slate-500">Unknown quantities render as “Not ready”, never as 0 mW or 0 g.</p>
        </div>
        <div className="divide-y divide-white/5">
          {readiness.panel.map((row) => (
            <div key={row.dimension} className="flex flex-wrap items-start gap-3 px-4 py-2.5">
              <span className="mt-0.5 text-cyan-400" aria-hidden="true">{panelIcon(row.dimension)}</span>
              <div className="min-w-40 flex-1">
                <p className="text-[12px] font-medium text-slate-200">{row.dimension}</p>
                <p className="mt-0.5 text-[11px] leading-relaxed text-slate-500">{row.note}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-slate-300">{row.value_display}</span>
                <LevelPill level={row.status} />
              </div>
            </div>
          ))}
        </div>
      </section>

      <div>
        <p className="mb-2 text-xs font-semibold text-slate-300">Candidate engineering increment (scientific value vs physical burden)</p>
        <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
          {readiness.candidates.map((candidate) => <CandidateCard key={candidate.candidate} candidate={candidate} />)}
        </div>
      </div>

      <section className="rounded-lg border border-amber-400/20 bg-amber-400/[0.045] p-4">
        <p className="text-xs font-semibold text-amber-200">Claim boundaries</p>
        <ul className="mt-2 space-y-1.5 text-[11px] leading-relaxed text-slate-400">
          {readiness.boundaries.map((item) => <li key={item}>• {item}</li>)}
        </ul>
      </section>

      <details className="rounded-lg border border-white/5 bg-white/[0.015]">
        <summary className="cursor-pointer px-4 py-3 text-[11px] font-semibold text-slate-400">Source artifacts ({readiness.source_artifacts.length})</summary>
        <div className="space-y-1 border-t border-white/5 px-4 py-3">
          {readiness.source_artifacts.map((path) => <p key={path} className="break-all font-mono text-[10px] text-cyan-300">{path}</p>)}
        </div>
      </details>
    </Panel>
  );
}
