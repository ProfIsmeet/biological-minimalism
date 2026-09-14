"use client";

import { useEffect, useState } from "react";
import { CircuitBoard } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { api } from "@/lib/api";
import type { FinalWearableArchitecture } from "@/lib/types";

/**
 * Mission-Overview surface for the FINAL SELECTED wearable architecture.
 *
 * Source of truth is the frozen Stage-4-closure / Stage-5 canonical artifact
 * results/final_wearable_architecture.json, served fail-closed through
 * /research/final-wearable-architecture. This panel NEVER reconstructs
 * architecture state locally and NEVER falls back to a historical Stage-3/4
 * sensor set: if the canonical artifact is unavailable it renders an explicit
 * error, not a stale guess (governing sync task §13).
 *
 * Selected modalities are grouped by body region so a viewer can immediately
 * read Wrist → PPG + IMU, Chest → ECG, Head → frontal EEG + EOG. Evaluated but
 * NOT-selected modalities (thoracic/leg BioZ, second-site PPG, wrist
 * temperature/light) are rendered in a visually distinct "evaluated — not
 * selected" section straight from the artifact's exclusion_rationale — present
 * for honesty, never mixed in with the selected sensors.
 */

// Presentation-only mapping keyed on the canonical per-modality-breakdown IDs
// in results/final_wearable_architecture.json (contact_model.per_modality_breakdown).
// Structure/counts come from the artifact; only the human labels + region
// grouping live here. A key absent from the artifact simply does not render.
const MODALITY_DISPLAY: Record<string, { region: string; sensors: string[] }> = {
  wrist_ppg_plus_imu: { region: "Wrist", sensors: ["PPG", "IMU"] },
  ecg_chest: { region: "Chest", sensors: ["ECG"] },
  frontal_eeg: { region: "Head", sensors: ["Frontal EEG"] },
  eog: { region: "Head", sensors: ["EOG"] },
};

const REGION_ORDER = ["Wrist", "Chest", "Head"];

interface ContactRange {
  min?: number;
  max?: number;
  most_likely?: number;
}

interface ContactModel {
  total_contacts?: ContactRange;
  per_modality_breakdown?: Record<string, ContactRange>;
}

interface BurdenRanges {
  power_mw?: { selected_topology_battery_side?: number };
  mass_g?: { battery_only?: number };
  raw_data_rate_bps?: Record<string, number>;
  contacts?: ContactRange;
}

interface RegionGroup {
  region: string;
  sensors: string[];
  contacts: number | null;
}

function buildRegions(contactModel: ContactModel): RegionGroup[] {
  const breakdown = contactModel.per_modality_breakdown ?? {};
  const byRegion = new Map<string, RegionGroup>();
  for (const [key, display] of Object.entries(MODALITY_DISPLAY)) {
    const entry = breakdown[key];
    if (!entry) continue;
    const contacts = typeof entry.most_likely === "number" ? entry.most_likely : null;
    const existing = byRegion.get(display.region);
    if (existing) {
      existing.sensors.push(...display.sensors);
      if (existing.contacts === null) {
        existing.contacts = contacts;
      } else if (contacts !== null) {
        existing.contacts += contacts;
      }
    } else {
      byRegion.set(display.region, { region: display.region, sensors: [...display.sensors], contacts });
    }
  }
  return REGION_ORDER.filter((r) => byRegion.has(r)).map((r) => byRegion.get(r)!);
}

export function SelectedArchitecturePanel() {
  const [architecture, setArchitecture] = useState<FinalWearableArchitecture | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .getFinalWearableArchitecture()
      .then((envelope) => {
        if (cancelled) return;
        if (envelope.availability !== "available" || !envelope.architecture) {
          setError(envelope.error ?? "Canonical final wearable architecture is unavailable.");
          setArchitecture(null);
        } else {
          setArchitecture(envelope.architecture);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load final wearable architecture.");
        setArchitecture(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const subtitle = architecture
    ? `${architecture.selected_class} · frozen selection (results/final_wearable_architecture.json)`
    : "Frozen selected wearable architecture";

  return (
    <Panel title="Selected Architecture" subtitle={subtitle} icon={<CircuitBoard size={16} />} contentClassName="space-y-4">
      {loading ? (
        <p className="text-sm text-slate-500">Loading canonical architecture…</p>
      ) : !architecture ? (
        <p role="alert" className="rounded-lg border border-rose-400/20 bg-rose-400/[0.06] px-4 py-3 text-xs text-rose-200">
          Selected architecture unavailable — canonical Stage-5 artifact could not be loaded: {error}. No historical
          architecture is substituted.
        </p>
      ) : (
        <SelectedArchitectureBody architecture={architecture} />
      )}
    </Panel>
  );
}

function SelectedArchitectureBody({ architecture }: { architecture: FinalWearableArchitecture }) {
  const contactModel = architecture.contact_model as ContactModel;
  const burden = architecture.burden_ranges as BurdenRanges;
  const moduleTopology = architecture.module_topology as { topology_class?: string; module_ids?: string[] };

  const regions = buildRegions(contactModel);
  const contacts = contactModel.total_contacts ?? burden.contacts;
  const power = burden.power_mw?.selected_topology_battery_side;
  const mass = burden.mass_g?.battery_only;
  const dataRate = burden.raw_data_rate_bps
    ? Object.values(burden.raw_data_rate_bps).reduce((a, b) => a + b, 0)
    : null;
  const moduleCount = moduleTopology.module_ids?.length ?? regions.length;

  return (
    <>
      <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
        {regions.map((region) => (
          <div key={region.region} className="rounded-lg border border-emerald-400/25 bg-emerald-400/[0.06] p-3">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-emerald-300">{region.region}</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {region.sensors.map((sensor) => (
                <span
                  key={sensor}
                  className="rounded-full border border-emerald-400/30 bg-emerald-400/[0.10] px-2 py-0.5 text-[11px] font-medium text-emerald-200"
                >
                  {sensor}
                </span>
              ))}
            </div>
            {region.contacts !== null ? (
              <p className="mt-2 text-[10px] text-slate-500">~{region.contacts} contacts (most likely)</p>
            ) : null}
          </div>
        ))}
      </div>

      <p className="text-[10px] leading-relaxed text-slate-500">
        {regions.length} body regions · {moduleCount} modules · topology {moduleTopology.topology_class ?? "UNKNOWN"}.
        Bounded engineering estimates, not a final BOM: contacts {contacts?.min}–{contacts?.max} (most likely{" "}
        {contacts?.most_likely})
        {typeof dataRate === "number" ? <> · raw data rate {dataRate.toLocaleString()} bps (sum of channels)</> : null}
        {typeof power === "number" ? (
          <> · power ~{power} mW (calculated, distributed-topology battery-side — not a flight-qualified measurement)</>
        ) : null}
        {typeof mass === "number" ? (
          <> · mass {mass} g (battery-only bounded estimate — not a measured assembled-wearable mass)</>
        ) : null}
        .
      </p>

      <div>
        <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-amber-300/80">Evaluated — not selected</p>
        <div className="flex flex-col gap-1.5">
          {Object.entries(architecture.exclusion_rationale).map(([key, entry]) => (
            <div key={key} className="rounded-lg border border-amber-400/15 bg-amber-400/[0.04] px-2.5 py-1.5">
              <div className="flex items-center gap-2">
                <span className="rounded-full border border-amber-400/25 bg-amber-400/[0.08] px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-amber-300">
                  Not selected
                </span>
                <span className="text-[11px] font-medium text-slate-300">{key.replace(/_/g, " ")}</span>
              </div>
              <p className="mt-0.5 text-[10px] leading-relaxed text-slate-500">{entry.reason}</p>
            </div>
          ))}
        </div>
        <p className="mt-1.5 text-[10px] leading-relaxed text-slate-600">
          Excluded from the selected architecture only — their scientific evidence is preserved in Research Mode. Not selected
          does not mean generally useless.
        </p>
      </div>
    </>
  );
}
