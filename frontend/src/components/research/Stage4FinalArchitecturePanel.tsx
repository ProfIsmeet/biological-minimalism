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
  MINIMAL_CORE: "border-final-accent/25 bg-final-accent/[0.08] text-final-accent",
  CORE_PLUS_CONTEXT: "border-jury-success/30 bg-jury-success/[0.10] text-jury-success",
  EVIDENCE_EXTENDED: "border-jury-warning/20 bg-jury-warning/[0.06] text-jury-warning",
  EXPERIMENTAL_EXTENDED: "border-jury-warning/20 bg-jury-warning/[0.06] text-jury-warning",
};

const ALL_CANDIDATE_CLASSES = ["MINIMAL_CORE", "CORE_PLUS_CONTEXT", "EVIDENCE_EXTENDED", "EXPERIMENTAL_EXTENDED"];

function Pill({ text, className }: { text: string; className: string }) {
  return <span className={clsx("rounded-full border px-2 py-0.5 text-xs font-semibold", className)}>{text}</span>;
}

function ExclusionRow({
  sensorKey,
  entry,
}: {
  sensorKey: string;
  entry: { reason: string; prohibited_claim: string };
}) {
  return (
    <div className="border-b border-jury-border-subtle py-1.5 last:border-0">
      <p className="text-xs font-semibold text-ink-secondary">{sensorKey.replace(/_/g, " ")}</p>
      <p className="mt-0.5 text-xs leading-relaxed text-ink-muted">{entry.reason}</p>
      <p className="mt-0.5 text-xs leading-relaxed text-ink-muted">Not claimed: {entry.prohibited_claim}</p>
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
      <p role="alert" className="rounded-lg border border-jury-fault/20 bg-jury-fault/[0.06] px-4 py-3 text-xs text-jury-fault">
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
      <div className="rounded-lg border border-jury-success/25 bg-jury-success/[0.06] p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-sm font-semibold text-jury-success">Selected: {finalArchitecture.selected_class}</span>
          <Pill text={gateDStatus.gate_d_burden_completeness ?? "UNKNOWN"} className="border-jury-warning/25 bg-jury-warning/[0.08] text-jury-warning" />
        </div>
        <p className="mt-1.5 text-xs leading-relaxed text-ink-secondary">
          Modalities: {finalArchitecture.selected_modalities.join("; ")}
        </p>
        <p className="mt-1 text-xs text-ink-muted">
          Body regions: {finalArchitecture.selected_body_regions.join(", ")} · Module topology: {moduleTopology.topology_class ?? "UNKNOWN"} ·{" "}
          battery: {moduleTopology.battery_topology_selected ?? "UNKNOWN"} · MCU/radio: {moduleTopology.mcu_radio_topology_selected ?? "UNKNOWN"}
        </p>
      </div>

      <div className="rounded-lg border border-jury-border-subtle bg-surface-2 p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-secondary">Burden (accepted, disclosed)</p>
        <p className="mt-1 text-xs leading-relaxed text-ink-muted">
          Contacts: {burden.contacts?.min}–{burden.contacts?.max} (most likely {burden.contacts?.most_likely}) · Power (selected distributed
          topology, battery-side): {burden.power_mw?.selected_topology_battery_side} mW — higher than the alternative single-shared-MCU/radio
          figure ({burden.power_mw?.alternative_single_shared_battery_side_not_selected} mW), accepted per Coordinator topology choice, not hidden.
        </p>
      </div>

      <div>
        <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">Excluded from final architecture</p>
        {Object.entries(finalArchitecture.exclusion_rationale).map(([key, entry]) => (
          <ExclusionRow key={key} sensorKey={key} entry={entry} />
        ))}
      </div>

      {gateECoordinatorDecisions ? (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
            Gate E — Coordinator decisions ({gateECoordinatorDecisions.gate_e_pending_science_sensitivity})
          </p>
          {gateECoordinatorDecisions.decisions.map((d) => (
            <div key={d.item} className="border-b border-jury-border-subtle py-1.5 last:border-0">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs text-ink-secondary">{d.item}</span>
                <Pill text={d.decision} className="border-final-accent/25 bg-final-accent/[0.08] text-final-accent" />
              </div>
              <p className="mt-0.5 text-xs leading-relaxed text-jury-warning/80">
                Revision trigger: {JSON.stringify(d.revision_trigger.condition ?? d.revision_trigger)}
              </p>
            </div>
          ))}
        </div>
      ) : null}

      {formalParetoAnalysis ? (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
            Formal Pareto analysis ({formalParetoAnalysis.formal_pareto_status}) — no single score, no unique winner
          </p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {ALL_CANDIDATE_CLASSES.map((classId) => (
              <div key={classId} className="rounded-lg border border-jury-border-subtle bg-surface-2 p-2.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-mono text-xs text-ink-secondary">{classId}</span>
                  <Pill
                    text={CANDIDATE_STATUS_LABEL[classId] ?? "UNKNOWN"}
                    className={CANDIDATE_STATUS_CLASS[classId] ?? "border-jury-border-subtle bg-ink-muted/[0.06] text-ink-secondary"}
                  />
                </div>
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs leading-relaxed text-ink-muted">{formalParetoAnalysis.coordinator_selection_rationale}</p>
          <p className="mt-1 text-xs leading-relaxed text-ink-muted">{formalParetoAnalysis.coordinator_selection_is_not_mathematical_dominance}</p>
        </div>
      ) : null}

      {closureManifest ? (
        <p className="text-xs text-ink-muted">
          Closure manifest status: {closureManifest.status} · {closureManifest.authoritative_artifacts.length} authoritative artifacts hashed ·
          repository SHA at manifest generation: <span className="font-mono">{closureManifest.repository_sha_after_closure.slice(0, 12)}</span>
        </p>
      ) : null}
    </Panel>
  );
}
