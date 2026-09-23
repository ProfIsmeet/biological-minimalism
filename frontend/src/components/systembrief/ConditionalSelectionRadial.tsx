"use client";

import { useEffect, useState } from "react";

import { CORE_PLUS_CONTEXT_SUMMARY, EOG_DELTA_NOTE, FINAL_ARCHITECTURE_ID, MINIMAL_CORE_SUMMARY } from "@/lib/architecture";
import { api } from "@/lib/api";
import { round2 } from "@/lib/format";
import type { FinalWearableArchitecture } from "@/lib/types";

interface Dimension {
  label: string;
  minimalCore: string;
  corePlusContext: string;
}

const SIZE = 260;
const CENTER = SIZE / 2;
const RING_MINIMAL = 60;
const RING_FINAL = 98;

/**
 * Radial MINIMAL_CORE vs CORE_PLUS_CONTEXT comparison for `/system-brief`
 * (master prompt 3 §24). Both architectures are members of the Pareto set;
 * wedges are categorical labels around two concentric rings, never a
 * continuous area/score that would imply false numeric precision over
 * bounded engineering estimates.
 */
export function ConditionalSelectionRadial() {
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

  const burden = architecture?.burden_ranges as
    | { power_mw?: { selected_topology_battery_side?: number }; mass_g?: { battery_only?: number }; contacts?: { min?: number; max?: number; most_likely?: number } }
    | undefined;
  const power = burden?.power_mw?.selected_topology_battery_side;
  const mass = burden?.mass_g?.battery_only;
  const contacts = burden?.contacts?.most_likely;

  const dimensions: Dimension[] = [
    { label: "Body regions", minimalCore: "3", corePlusContext: "3" },
    { label: "Modalities", minimalCore: "4", corePlusContext: "5" },
    { label: "Mass (battery-only)", minimalCore: "Not available", corePlusContext: mass != null ? `${mass} g` : "Not available" },
    { label: "Power (battery-side)", minimalCore: "Not available", corePlusContext: power != null ? `~${power} mW` : "Not available" },
    { label: "Contacts (most likely)", minimalCore: "Not available", corePlusContext: contacts != null ? `${contacts}` : "Not available" },
  ];
  const wedgeAngle = 360 / dimensions.length;

  return (
    <section aria-labelledby="conditional-selection-heading" className="flex flex-col gap-4 rounded-[12px] border border-jury-border-subtle bg-surface-1 p-6">
      <div>
        <h2 id="conditional-selection-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
          Conditional evidence–burden selection
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
          {MINIMAL_CORE_SUMMARY} (inner ring) vs. {CORE_PLUS_CONTEXT_SUMMARY} (outer ring, {FINAL_ARCHITECTURE_ID}). {EOG_DELTA_NOTE}
        </p>
      </div>

      <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start sm:gap-8">
        <svg width={SIZE} height={SIZE} role="img" aria-label="Radial comparison of MINIMAL_CORE and CORE_PLUS_CONTEXT burden dimensions">
          <circle cx={CENTER} cy={CENTER} r={RING_FINAL} fill="none" stroke="#203239" strokeWidth={1} />
          <circle cx={CENTER} cy={CENTER} r={RING_MINIMAL} fill="none" stroke="#203239" strokeWidth={1} />
          {dimensions.map((_, index) => {
            const angleRad = ((index * wedgeAngle - 90) * Math.PI) / 180;
            const x = round2(CENTER + RING_FINAL * Math.cos(angleRad));
            const y = round2(CENTER + RING_FINAL * Math.sin(angleRad));
            return <line key={index} x1={CENTER} y1={CENTER} x2={x} y2={y} stroke="#16262C" strokeWidth={1} />;
          })}
          {dimensions.map((dimension, index) => {
            const midAngle = index * wedgeAngle + wedgeAngle / 2 - 90;
            const rad = (midAngle * Math.PI) / 180;
            const labelX = round2(CENTER + (RING_FINAL + 20) * Math.cos(rad));
            const labelY = round2(CENTER + (RING_FINAL + 20) * Math.sin(rad));
            return (
              <text
                key={dimension.label}
                x={labelX}
                y={labelY}
                textAnchor="middle"
                fontSize={9}
                fill="#B6C4C9"
                className="font-sans"
              >
                {dimension.label}
              </text>
            );
          })}
          <circle cx={CENTER} cy={CENTER} r={4} fill="#69B7AD" />
        </svg>

        <ul className="flex w-full flex-col divide-y divide-jury-border-subtle rounded-[8px] border border-jury-border-subtle bg-surface-2 text-xs">
          {dimensions.map((dimension) => (
            <li key={dimension.label} className="grid grid-cols-3 gap-2 px-3 py-2">
              <span className="text-ink-muted">{dimension.label}</span>
              <span className="text-ink-secondary">{dimension.minimalCore}</span>
              <span className="font-medium text-final-accent">{dimension.corePlusContext}</span>
            </li>
          ))}
          <li className="grid grid-cols-3 gap-2 px-3 py-2 text-[10px] font-semibold uppercase tracking-wide text-ink-disabled">
            <span>Dimension</span>
            <span>MINIMAL_CORE</span>
            <span>CORE_PLUS_CONTEXT</span>
          </li>
        </ul>
      </div>

      <p className="border-t border-jury-border-subtle pt-3 text-xs leading-relaxed text-ink-muted">
        Conditional evidence–burden engineering selection; not a unique mathematical optimum.
      </p>
    </section>
  );
}
