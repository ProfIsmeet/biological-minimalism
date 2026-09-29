"use client";

import { useEffect, useState } from "react";

import { SemanticTable, StatusPill } from "@/components/visualization/shared/ChartFrame";
import { CORE_PLUS_CONTEXT_SUMMARY, EOG_DELTA_NOTE, FINAL_SENSOR_INVENTORY, MINIMAL_CORE_SUMMARY, type FinalModality } from "@/lib/architecture";
import { api } from "@/lib/api";
import type { FinalWearableArchitecture } from "@/lib/types";

/**
 * Stage 6 Visualization E — MINIMAL_CORE vs CORE_PLUS_CONTEXT delta matrix
 * (master prompt §15/§18 "replace inappropriate radial selection graphics
 * with a direct delta matrix"). Replaces the decorative SVG radial wedge
 * diagram previously in this file; keeps the same live
 * `api.getFinalWearableArchitecture()` fetch this section already used.
 *
 * Rows come directly from FINAL_SENSOR_INVENTORY (the accepted architecture
 * contract, lib/architecture.ts) — not re-derived. MINIMAL_CORE membership is
 * every modality except EOG (results/stage4_architecture_candidate_classes.json
 * MINIMAL_CORE.sensors: wrist PPG, wrist IMU, chest ECG, frontal EEG); EOG is
 * the sole CORE_PLUS_CONTEXT-only addition, matching EOG_DELTA_NOTE. Burden
 * values are read live from the fetched architecture artifact's
 * contact_model.per_modality_breakdown — never hardcoded — and are shown as
 * "Not available" rather than 0 when the live fetch has not resolved a given
 * modality's contact figure.
 */
const MINIMAL_CORE_MODALITIES: FinalModality[] = ["PPG", "IMU", "ECG", "EEG"];

const ROLE: Record<FinalModality, string> = {
  PPG: "Primary HR estimation input",
  IMU: "Motion-context input for capacity-controlled HR benefit",
  ECG: "Cardiac electrical reference signal",
  EEG: "Cortical activity — sleep-stage classification foundation",
  EOG: "Ocular context — same-dataset incremental sleep-stage value",
};

interface ContactBreakdown {
  min?: number;
  max?: number;
  most_likely?: number;
  unit?: string;
}

function contactsFor(architecture: FinalWearableArchitecture | null, key: string): ContactBreakdown | null {
  const model = architecture?.contact_model as { per_modality_breakdown?: Record<string, ContactBreakdown> } | undefined;
  return model?.per_modality_breakdown?.[key] ?? null;
}

const CONTACT_KEY: Record<FinalModality, string | null> = {
  PPG: "wrist_ppg_plus_imu",
  IMU: "wrist_ppg_plus_imu",
  ECG: "ecg_chest",
  EEG: "frontal_eeg",
  EOG: "eog",
};

export function ArchitectureDeltaMatrix() {
  const [architecture, setArchitecture] = useState<FinalWearableArchitecture | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getFinalWearableArchitecture()
      .then((envelope) => {
        if (!cancelled && envelope.availability === "available") setArchitecture(envelope.architecture);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section aria-labelledby="architecture-delta-heading" className="flex flex-col gap-4 rounded-[12px] border border-jury-border-subtle bg-surface-1 p-6">
      <div>
        <h2 id="architecture-delta-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
          Architecture delta matrix
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
          {MINIMAL_CORE_SUMMARY} vs. {CORE_PLUS_CONTEXT_SUMMARY} (selected). {EOG_DELTA_NOTE} Both remain Pareto-relevant —
          the selected architecture is not presented as a unique mathematical optimum.
        </p>
      </div>

      <SemanticTable
        caption="Per-modality membership, role, incremental burden, and evidence class for MINIMAL_CORE vs CORE_PLUS_CONTEXT"
        columns={["Modality", "Body region", "MINIMAL_CORE", "CORE_PLUS_CONTEXT", "Delta", "Physiological role", "Incremental contacts", "Evidence"]}
        rows={FINAL_SENSOR_INVENTORY.map((entry) => {
          const isCore = MINIMAL_CORE_MODALITIES.includes(entry.modality);
          const isDelta = entry.modality === "EOG";
          const contacts = contactsFor(architecture, CONTACT_KEY[entry.modality] ?? "");
          return {
            key: entry.modality,
            cells: [
              <span key="mod" className="font-semibold text-ink-primary">
                {entry.modality}
              </span>,
              entry.region,
              isCore ? <StatusPill key="mc" label="Member" tone="nominal" /> : <StatusPill key="mc" label="Not included" tone="muted" />,
              <StatusPill key="cpc" label="Member" tone="nominal" />,
              isDelta ? <StatusPill key="delta" label="+ Added" tone="info" /> : <span key="delta">—</span>,
              ROLE[entry.modality],
              contacts?.most_likely != null ? `${contacts.most_likely} ${contacts.unit ?? ""}`.trim() : "Not available",
              isDelta ? "Tier B (same-dataset) / Tier C (bounded external)" : "Tier A (foundation signal, not under incremental-value test)",
            ],
          };
        })}
      />

      <p className="border-t border-jury-border-subtle pt-3 text-xs leading-relaxed text-ink-muted">
        Contact/burden figures are bounded engineering estimates from results/final_wearable_architecture.json — not
        measured or flight-qualified hardware. Static architecture facts above do not depend on the live replay
        source&rsquo;s current coverage; see the Coverage &amp; freshness matrix on Mission Overview for that.
      </p>
    </section>
  );
}
