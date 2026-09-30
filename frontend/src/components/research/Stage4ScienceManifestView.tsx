import { ShieldCheck } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import type {
  Stage4ArchitectureDecisionInputsScience,
  Stage4ScienceClaimLedger,
  Stage4ScienceConsumptionManifest,
  Stage4SensorValueMatrix,
} from "@/lib/types";

// Renders the Science Owner's Stage-4 handoff package VERBATIM — this is the
// authoritative safe-wording/classification surface (governing prompt Part
// XI). No string here is authored or paraphrased by Integration Owner code;
// every field is Science-Owner text, rendered as-is. Negative/mixed results
// (LBNP, QDE, PTT) get identical visual treatment to supportive ones
// (governing prompt §30).

const STRENGTH_CLASS: Record<string, string> = {
  SAFE: "border-emerald-400/25 bg-emerald-400/[0.08] text-emerald-300",
  SAFE_WITH_LIMITATION: "border-cyan-400/20 bg-cyan-400/[0.06] text-cyan-300",
  HISTORICAL_ONLY: "border-jury-border-subtle bg-ink-muted/[0.06] text-ink-secondary",
  UNSAFE: "border-rose-400/25 bg-rose-400/[0.08] text-rose-300",
  PENDING: "border-amber-400/20 bg-amber-400/[0.06] text-amber-300",
};

function StrengthPill({ strength }: { strength: string }) {
  return (
    <span
      className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${STRENGTH_CLASS[strength] ?? "border-jury-border-subtle bg-ink-muted/[0.06] text-ink-secondary"}`}
    >
      {strength}
    </span>
  );
}

function FamilyCard({ family }: { family: Stage4ScienceConsumptionManifest["families"][number] }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-mono text-xs text-ink-secondary">{family.family_id}</span>
        <span className="rounded-full border border-cyan-400/20 bg-cyan-400/[0.06] px-2 py-0.5 text-xs font-semibold text-cyan-300">
          {family.evidence_classification}
        </span>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-ink-primary">{family.strongest_safe_claim}</p>
      <p className="mt-1.5 text-xs leading-relaxed text-amber-300/80">
        Must not claim: {family.prohibited_overclaim}
      </p>
      {family.heterogeneity ? (
        <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">{family.heterogeneity}</p>
      ) : null}
      {family.unresolved_limitation ? (
        <p className="mt-1 text-xs leading-relaxed text-ink-muted">{family.unresolved_limitation}</p>
      ) : null}
      <p className="mt-2 truncate font-mono text-xs text-ink-muted" title={family.governing_artifact}>
        {family.governing_artifact}
      </p>
    </div>
  );
}

function ModalityRow({ modality }: { modality: Stage4SensorValueMatrix["modalities"][number] }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/5 py-1.5 last:border-0">
      <span className="text-xs text-ink-secondary">{modality.modality}</span>
      <span className="max-w-[45%] truncate text-xs text-ink-muted" title={modality.supported_target_use}>
        {modality.supported_target_use}
      </span>
      <span className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5 text-xs font-semibold text-ink-secondary">
        {modality.architecture_implication}
      </span>
    </div>
  );
}

function ClaimRow({ claim }: { claim: Stage4ScienceClaim }) {
  return (
    <div className="border-b border-white/5 py-2 last:border-0">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-mono text-xs text-ink-muted">{claim.claim_id}</span>
        <StrengthPill strength={claim.strength} />
      </div>
      <p className="mt-1 text-xs leading-relaxed text-ink-primary">{claim.exact_safe_wording}</p>
      <p className="mt-1 text-xs leading-relaxed text-rose-300/70">Prohibited: {claim.prohibited_stronger_wording}</p>
    </div>
  );
}

type Stage4ScienceClaim = Stage4ScienceClaimLedger["claims"][number];

export function Stage4ScienceManifestView({
  manifest,
  sensorValueMatrix,
  claimLedger,
  architectureDecisionInputs,
}: {
  manifest: Stage4ScienceConsumptionManifest;
  sensorValueMatrix: Stage4SensorValueMatrix | null;
  claimLedger: Stage4ScienceClaimLedger | null;
  architectureDecisionInputs: Stage4ArchitectureDecisionInputsScience | null;
}) {
  return (
    <Panel
      title="Science Owner Stage 4 Handoff — Authoritative Safe Claims"
      subtitle="Every claim below is Science-Owner-authored and rendered verbatim, cross-verified against the live resolver on every read"
      icon={<ShieldCheck size={16} />}
      contentClassName="space-y-4"
    >
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {manifest.families.map((family) => (
          <FamilyCard key={family.family_id} family={family} />
        ))}
      </div>

      {sensorValueMatrix ? (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
            Sensor-value decision inputs ({sensorValueMatrix.modalities.length} modalities)
          </p>
          {sensorValueMatrix.modalities.map((m) => (
            <ModalityRow key={m.modality} modality={m} />
          ))}
        </div>
      ) : null}

      {claimLedger ? (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
            Claim ledger ({claimLedger.claims.length} claim areas)
          </p>
          {claimLedger.claims.map((c) => (
            <ClaimRow key={c.claim_id} claim={c} />
          ))}
        </div>
      ) : null}

      {architectureDecisionInputs ? (
        <p className="text-xs text-ink-muted">
          pre-closure input snapshot — architecture decision inputs: {architectureDecisionInputs.candidates.length} candidates ·
          final_architecture: {architectureDecisionInputs.final_architecture_status} · formal_pareto:{" "}
          {architectureDecisionInputs.formal_pareto_status} (decision inputs only — not a selection)
        </p>
      ) : null}
    </Panel>
  );
}
