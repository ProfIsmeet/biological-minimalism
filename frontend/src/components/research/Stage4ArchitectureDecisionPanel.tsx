import clsx from "clsx";
import { GitBranch } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import type {
  Stage4ArchitectureAcceptanceGates,
  Stage4ArchitectureCandidateClasses,
  Stage4BatteryTopologyScenarios,
  Stage4CandidateBurdenMatrix,
  Stage4CandidateClassBurdenComparison,
  Stage4ContactElectrodeBurden,
  Stage4GateDBurdenCompleteness,
  Stage4GateECoordinatorOptions,
} from "@/lib/types";

// Renders a value that may be absent as the literal text "UNKNOWN" - never
// blank, never coerced to 0 (master prompt Part XI §37: "Unknown must
// render as UNKNOWN, not zero").
function valueOrUnknown(value: unknown): string {
  if (value === null || value === undefined) return "UNKNOWN";
  if (typeof value === "boolean") return value ? "true" : "false";
  return String(value);
}

// Dedicated Stage-4 architecture-decision panel (closure-prep sprint). This
// component performs no analysis of its own — it renders ONLY what the
// backend already computed/curated, distinguishing current facts (candidate
// classes, gate severities) from unknowns (Gate D known-unknowns) from
// pending science (Gate E) from what remains a Coordinator decision. Gate D
// is rendered NOT_READY/CONDITIONALLY_READY/READY with equal visual weight
// to every other status — a NOT_READY gate must never look "mostly fine"
// (governing prompt Part VIII §37).

const GATE_D_STATUS_CLASS: Record<string, string> = {
  READY: "border-jury-success/25 bg-jury-success/[0.08] text-jury-success",
  CONDITIONALLY_READY: "border-jury-warning/25 bg-jury-warning/[0.08] text-jury-warning",
  NOT_READY: "border-jury-fault/25 bg-jury-fault/[0.08] text-jury-fault",
};

const DOMINANCE_CLASS: Record<string, string> = {
  PARETO_RELEVANT: "border-jury-success/20 bg-jury-success/[0.06] text-jury-success",
  POTENTIALLY_DOMINATED: "border-jury-warning/20 bg-jury-warning/[0.06] text-jury-warning",
  BURDEN_DATA_INCOMPLETE: "border-jury-border-subtle bg-ink-muted/[0.06] text-ink-secondary",
};

const SEVERITY_CLASS: Record<string, string> = {
  HARD_BLOCK: "border-jury-fault/20 bg-jury-fault/[0.06] text-jury-fault",
  COORDINATOR_DECISION_REQUIRED: "border-jury-warning/20 bg-jury-warning/[0.06] text-jury-warning",
  DISCLOSURE_REQUIRED: "border-final-accent/20 bg-final-accent/[0.06] text-final-accent",
  NONBLOCKING: "border-jury-border-subtle bg-ink-muted/[0.06] text-ink-secondary",
};

function Pill({ text, className }: { text: string; className: string }) {
  return <span className={clsx("rounded-full border px-2 py-0.5 text-xs font-semibold", className)}>{text}</span>;
}

function CandidateClassRow({ candidate }: { candidate: Stage4ArchitectureCandidateClasses["classes"][number] }) {
  return (
    <div className="rounded-lg border border-jury-border-subtle bg-surface-2 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-mono text-xs text-ink-secondary">{candidate.class_id}</span>
        <span className="text-xs text-ink-muted">{candidate.pending_science_exposure}</span>
      </div>
      <p className="mt-1.5 text-xs leading-relaxed text-ink-secondary">{candidate.description}</p>
      <p className="mt-1.5 text-xs text-ink-muted">Sensors: {candidate.sensors.join(", ")}</p>
      <p className="mt-1 text-xs text-ink-muted">Evidence: {candidate.evidence_confidence}</p>
    </div>
  );
}

function BurdenClassRow({ item }: { item: Stage4CandidateClassBurdenComparison["classes"][number] }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-jury-border-subtle py-1.5 last:border-0">
      <span className="text-xs text-ink-secondary">{item.class_id}</span>
      <Pill
        text={item.dominance_flag}
        className={DOMINANCE_CLASS[item.dominance_flag] ?? "border-jury-border-subtle bg-ink-muted/[0.06] text-ink-secondary"}
      />
    </div>
  );
}

function ContactModalityRow({ modality }: { modality: Stage4ContactElectrodeBurden["modalities"][number] }) {
  const c = modality.total_contacts;
  return (
    <div className="border-b border-jury-border-subtle py-1.5 last:border-0">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs text-ink-secondary">{modality.modality}</span>
        <span className="font-mono text-xs text-ink-secondary">
          {valueOrUnknown(c?.min)}–{valueOrUnknown(c?.max)} {c?.unit ?? ""} (most likely {valueOrUnknown(c?.most_likely)})
        </span>
      </div>
      <p className="text-xs text-ink-muted">
        {modality.anatomical_region} · {modality.electrode_type} · confidence: {modality.confidence}
      </p>
      {modality.unresolved_topology_question ? (
        <p className="mt-0.5 text-xs leading-relaxed text-jury-warning/80">
          Unresolved: {valueOrUnknown((modality.unresolved_topology_question as { question?: string }).question)}
        </p>
      ) : null}
    </div>
  );
}

function BurdenMatrixClassRow({ row }: { row: Stage4CandidateBurdenMatrix["classes"][number] }) {
  const powerRange = row.power_range_mw as { single_shared_mcu_radio?: { battery_side?: number }; per_module_mcu_radio?: { battery_side?: number } };
  return (
    <div className="rounded-lg border border-jury-border-subtle bg-surface-2 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-mono text-xs text-ink-secondary">{row.class_id}</span>
        <span className="text-xs text-ink-muted">{row.module_count} module{row.module_count === 1 ? "" : "s"}</span>
      </div>
      <p className="mt-1 text-xs text-ink-muted">
        Contacts: {valueOrUnknown(row.total_contacts?.min)}–{valueOrUnknown(row.total_contacts?.max)} (most likely {valueOrUnknown(row.total_contacts?.most_likely)})
      </p>
      <p className="mt-0.5 text-xs text-ink-muted">
        Battery-side power: {valueOrUnknown(powerRange?.single_shared_mcu_radio?.battery_side)}–{valueOrUnknown(powerRange?.per_module_mcu_radio?.battery_side)} mW
        (shared vs. per-module MCU/radio)
      </p>
      {row.major_unknowns.length ? (
        <ul className="mt-1 space-y-0.5 text-xs leading-relaxed text-jury-warning/70">
          {row.major_unknowns.map((u) => (
            <li key={u}>• {u}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function BatteryScenarioSummary({ scenarios }: { scenarios: Stage4BatteryTopologyScenarios }) {
  return (
    <div className="rounded-lg border border-jury-border-subtle bg-surface-2 p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-secondary">Battery/electronics topology — {scenarios.not_a_final_battery_selection ? "not a final selection" : ""}</p>
      <p className="mt-1 text-xs leading-relaxed text-ink-secondary">{scenarios.does_ranking_depend_on_topology.verdict}</p>
      <p className="mt-1 text-xs leading-relaxed text-ink-muted">
        Operating-duration requirement: {valueOrUnknown((scenarios.operating_duration_requirement_status as { status?: string }).status)}
      </p>
    </div>
  );
}

function GateRow({ gate }: { gate: Stage4ArchitectureAcceptanceGates["gates"][number] }) {
  return (
    <div className="border-b border-jury-border-subtle py-2 last:border-0">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-mono text-xs text-ink-secondary">{gate.gate_id}</span>
        <Pill text={gate.severity} className={SEVERITY_CLASS[gate.severity] ?? "border-jury-border-subtle bg-ink-muted/[0.06] text-ink-secondary"} />
      </div>
      <p className="mt-1 text-xs leading-relaxed text-ink-muted">{gate.current_readiness}</p>
    </div>
  );
}

export function Stage4ArchitectureDecisionPanel({
  candidateClasses,
  gateD,
  gateDError,
  burdenComparison,
  gateE,
  acceptanceGates,
  contactElectrodeBurden,
  batteryTopologyScenarios,
  candidateBurdenMatrix,
}: {
  candidateClasses: Stage4ArchitectureCandidateClasses | null;
  gateD: Stage4GateDBurdenCompleteness | null;
  gateDError: string | null;
  burdenComparison: Stage4CandidateClassBurdenComparison | null;
  gateE: Stage4GateECoordinatorOptions | null;
  acceptanceGates: Stage4ArchitectureAcceptanceGates | null;
  contactElectrodeBurden: Stage4ContactElectrodeBurden | null;
  batteryTopologyScenarios: Stage4BatteryTopologyScenarios | null;
  candidateBurdenMatrix: Stage4CandidateBurdenMatrix | null;
}) {
  return (
    <Panel
      title="Stage 4 Architecture Decision Prep (historical inputs)"
      subtitle="Pre-closure preparation inputs, preserved as-is — the Coordinator's actual final selection is recorded in the 'Stage 4 Final Architecture' panel above, not here"
      icon={<GitBranch size={16} />}
      contentClassName="space-y-4"
    >
      {gateD ? (
        <div className="rounded-lg border border-jury-border-subtle bg-surface-2 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-ink-secondary">
              Gate D — Burden Completeness
            </span>
            <Pill
              text={gateD.gate_d_burden_completeness}
              className={GATE_D_STATUS_CLASS[gateD.gate_d_burden_completeness] ?? "border-jury-border-subtle bg-ink-muted/[0.06] text-ink-secondary"}
            />
          </div>
          <p className="mt-1.5 text-xs leading-relaxed text-ink-secondary">{gateD.rationale}</p>
          {gateD.gate_d_burden_completeness !== "READY" ? (
            <ul className="mt-2 space-y-1 text-xs leading-relaxed text-jury-warning/80">
              {gateD.what_would_close_it.map((item) => (
                <li key={item}>• {item}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : gateDError ? (
        <p role="alert" className="rounded-lg border border-jury-fault/20 bg-jury-fault/[0.06] px-3 py-2 text-xs text-jury-fault">
          Gate D assessment unavailable: {gateDError}
        </p>
      ) : null}

      {batteryTopologyScenarios ? <BatteryScenarioSummary scenarios={batteryTopologyScenarios} /> : null}

      {contactElectrodeBurden ? (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
            Contact/electrode burden ({contactElectrodeBurden.modalities.length} modalities, bounded ranges)
          </p>
          {contactElectrodeBurden.modalities.map((m) => (
            <ContactModalityRow key={m.modality} modality={m} />
          ))}
        </div>
      ) : null}

      {candidateBurdenMatrix ? (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
            Candidate burden matrix — contacts, module count, power range
          </p>
          <p className="mb-2 text-xs leading-relaxed text-ink-muted">{candidateBurdenMatrix.robustness_analysis.verdict}</p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {candidateBurdenMatrix.classes.map((row) => (
              <BurdenMatrixClassRow key={row.class_id} row={row} />
            ))}
          </div>
        </div>
      ) : null}

      {gateE ? (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
            Gate E — Pending-Science Sensitivity ({gateE.high_sensitivity_items.length} HIGH-sensitivity item
            {gateE.high_sensitivity_items.length === 1 ? "" : "s"}, no option selected)
          </p>
          {gateE.high_sensitivity_items.map((item) => (
            <div key={item.item} className="border-b border-jury-border-subtle py-1.5 last:border-0">
              <p className="text-xs text-ink-secondary">{item.item}</p>
              <p className="text-xs text-ink-muted">
                WAIT / FREEZE_CONDITIONALLY / FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE — Coordinator choice required
              </p>
            </div>
          ))}
        </div>
      ) : null}

      {candidateClasses ? (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
            Candidate architecture classes ({candidateClasses.classes.length}, pre-decision comparison set — the
            Coordinator&rsquo;s final selection, CORE_PLUS_CONTEXT, is recorded above)
          </p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {candidateClasses.classes.map((c) => (
              <CandidateClassRow key={c.class_id} candidate={c} />
            ))}
          </div>
        </div>
      ) : null}

      {burdenComparison ? (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
            Burden comparison — dominance flags (not a final ranking)
          </p>
          {burdenComparison.classes.map((c) => (
            <BurdenClassRow key={c.class_id} item={c} />
          ))}
        </div>
      ) : null}

      {acceptanceGates ? (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
            Acceptance gates A–H
          </p>
          {acceptanceGates.gates.map((g) => (
            <GateRow key={g.gate_id} gate={g} />
          ))}
        </div>
      ) : null}

      <p className="text-xs text-ink-muted">
        pre-closure input snapshot — final_architecture: {candidateClasses?.final_architecture_status ?? "UNRESOLVED"} · formal_pareto:{" "}
        {candidateClasses?.formal_pareto_status ?? "NOT_READY"} (see the Final Architecture panel above for the actual Coordinator decision)
      </p>
    </Panel>
  );
}
