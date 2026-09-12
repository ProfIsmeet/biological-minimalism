import clsx from "clsx";
import { CheckCircle2 } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import type {
  FinalWearableArchitecture,
  Stage4FinalClosureManifest,
  Stage4FormalParetoAnalysis,
  Stage4GateECoordinatorDecisions,
} from "@/lib/types";

// Final architecture closure panel. Distinct from Stage4ArchitectureDecisionPanel
// (which remains the pre-closure prep/input surface, kept visible for
// traceability). This panel renders the Coordinator's actual decision: the
// selected class, included/excluded sensors, burden, conditional
// uncertainties, revision triggers, and where every candidate class stands
// (Coordinator selected / Pareto relevant / potentially dominated) — never
// hiding the alternatives (governing prompt Part VII §23).

const CANDIDATE_STATUS_LABEL: Record<string, string> = {
  MINIMAL_CORE: "Pareto relevant (not selected)",
  CORE_PLUS_CONTEXT: "Coordinator selected",
  EVIDENCE_EXTENDED: "Potentially dominated",
  EXPERIMENTAL_EXTENDED: "Potentially dominated",
};

const CANDIDATE_STATUS_CLASS: Record<string, string> = {
  MINIMAL_CORE: "border-cyan-400/25 bg-cyan-400/[0.08] text-cyan-300",
  CORE_PLUS_CONTEXT: "border-emerald-400/30 bg-emerald-400/[0.10] text-emerald-300",
  EVIDENCE_EXTENDED: "border-amber-400/20 bg-amber-400/[0.06] text-amber-300",
  EXPERIMENTAL_EXTENDED: "border-amber-400/20 bg-amber-400/[0.06] text-amber-300",
};

const ALL_CANDIDATE_CLASSES = ["MINIMAL_CORE", "CORE_PLUS_CONTEXT", "EVIDENCE_EXTENDED", "EXPERIMENTAL_EXTENDED"];

function Pill({ text, className }: { text: string; className: string }) {
  return <span className={clsx("rounded-full border px-2 py-0.5 text-[10px] font-semibold", className)}>{text}</span>;
}

function ExclusionRow({
  sensorKey,
  entry,
}: {
  sensorKey: string;
  entry: { reason: string; prohibited_claim: string };
}) {
  return (
    <div className="border-b border-white/5 py-1.5 last:border-0">
      <p className="text-[11px] font-semibold text-slate-300">{sensorKey.replace(/_/g, " ")}</p>
      <p className="mt-0.5 text-[10px] leading-relaxed text-slate-500">{entry.reason}</p>
      <p className="mt-0.5 text-[10px] leading-relaxed text-slate-600">Not claimed: {entry.prohibited_claim}</p>
    </div>
  );
}

export function Stage4FinalArchitecturePanel({
  finalArchitecture,
  finalArchitectureError,
  formalParetoAnalysis,
  gateECoordinatorDecisions,
  closureManifest,
}: {
  finalArchitecture: FinalWearableArchitecture | null;
  finalArchitectureError: string | null;
  formalParetoAnalysis: Stage4FormalParetoAnalysis | null;
  gateECoordinatorDecisions: Stage4GateECoordinatorDecisions | null;
  closureManifest: Stage4FinalClosureManifest | null;
}) {
  if (!finalArchitecture) {
    return finalArchitectureError ? (
      <p role="alert" className="rounded-lg border border-rose-400/20 bg-rose-400/[0.06] px-4 py-3 text-xs text-rose-200">
        Final wearable architecture unavailable: {finalArchitectureError}
      </p>
    ) : null;
  }

  const moduleTopology = finalArchitecture.module_topology as {
    topology_class?: string;
    battery_topology_selected?: string;
    mcu_radio_topology_selected?: string;
  };
  const burden = finalArchitecture.burden_ranges as {
    power_mw?: { selected_topology_battery_side?: number; alternative_single_shared_battery_side_not_selected?: number };
    contacts?: { min: number; max: number; most_likely: number };
  };
  const gateDStatus = finalArchitecture.gate_d_status as {
    gate_d_burden_completeness?: string;
    coordinator_acceptance?: { status?: string };
  };

  return (
    <Panel
      title="Stage 4 Final Architecture"
      subtitle="Coordinator decision — closes the architecture-selection question left UNRESOLVED by every prep artifact below"
      icon={<CheckCircle2 size={16} />}
      contentClassName="space-y-4"
    >
      <div className="rounded-lg border border-emerald-400/25 bg-emerald-400/[0.06] p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-sm font-semibold text-emerald-300">Selected: {finalArchitecture.selected_class}</span>
          <Pill text={gateDStatus.gate_d_burden_completeness ?? "UNKNOWN"} className="border-amber-400/25 bg-amber-400/[0.08] text-amber-300" />
        </div>
        <p className="mt-1.5 text-[11px] leading-relaxed text-slate-400">
          Modalities: {finalArchitecture.selected_modalities.join("; ")}
        </p>
        <p className="mt-1 text-[10px] text-slate-500">
          Body regions: {finalArchitecture.selected_body_regions.join(", ")} · Module topology: {moduleTopology.topology_class ?? "UNKNOWN"} ·{" "}
          battery: {moduleTopology.battery_topology_selected ?? "UNKNOWN"} · MCU/radio: {moduleTopology.mcu_radio_topology_selected ?? "UNKNOWN"}
        </p>
      </div>

      <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Burden (accepted, disclosed)</p>
        <p className="mt-1 text-[10px] leading-relaxed text-slate-500">
          Contacts: {burden.contacts?.min}–{burden.contacts?.max} (most likely {burden.contacts?.most_likely}) · Power (selected distributed
          topology, battery-side): {burden.power_mw?.selected_topology_battery_side} mW — higher than the alternative single-shared-MCU/radio
          figure ({burden.power_mw?.alternative_single_shared_battery_side_not_selected} mW), accepted per Coordinator topology choice, not hidden.
        </p>
      </div>

      <div>
        <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Excluded from final architecture</p>
        {Object.entries(finalArchitecture.exclusion_rationale).map(([key, entry]) => (
          <ExclusionRow key={key} sensorKey={key} entry={entry} />
        ))}
      </div>

      {gateECoordinatorDecisions ? (
        <div>
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Gate E — Coordinator decisions ({gateECoordinatorDecisions.gate_e_pending_science_sensitivity})
          </p>
          {gateECoordinatorDecisions.decisions.map((d) => (
            <div key={d.item} className="border-b border-white/5 py-1.5 last:border-0">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-[11px] text-slate-300">{d.item}</span>
                <Pill text={d.decision} className="border-cyan-400/25 bg-cyan-400/[0.08] text-cyan-300" />
              </div>
              <p className="mt-0.5 text-[10px] leading-relaxed text-amber-300/80">
                Revision trigger: {JSON.stringify(d.revision_trigger.condition ?? d.revision_trigger)}
              </p>
            </div>
          ))}
        </div>
      ) : null}

      {formalParetoAnalysis ? (
        <div>
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Formal Pareto analysis ({formalParetoAnalysis.formal_pareto_status}) — no single score, no unique winner
          </p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {ALL_CANDIDATE_CLASSES.map((classId) => (
              <div key={classId} className="rounded-lg border border-white/10 bg-white/[0.02] p-2.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-mono text-[11px] text-slate-300">{classId}</span>
                  <Pill
                    text={CANDIDATE_STATUS_LABEL[classId] ?? "UNKNOWN"}
                    className={CANDIDATE_STATUS_CLASS[classId] ?? "border-slate-500/20 bg-slate-500/[0.06] text-slate-400"}
                  />
                </div>
              </div>
            ))}
          </div>
          <p className="mt-2 text-[10px] leading-relaxed text-slate-500">{formalParetoAnalysis.coordinator_selection_rationale}</p>
          <p className="mt-1 text-[10px] leading-relaxed text-slate-600">{formalParetoAnalysis.coordinator_selection_is_not_mathematical_dominance}</p>
        </div>
      ) : null}

      {closureManifest ? (
        <p className="text-[10px] text-slate-600">
          Closure manifest status: {closureManifest.status} · {closureManifest.authoritative_artifacts.length} authoritative artifacts hashed ·
          repository SHA at manifest generation: <span className="font-mono">{closureManifest.repository_sha_after_closure.slice(0, 12)}</span>
        </p>
      ) : null}
    </Panel>
  );
}
