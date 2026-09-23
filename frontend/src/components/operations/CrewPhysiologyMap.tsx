"use client";

import { useState } from "react";
import Link from "next/link";
import clsx from "clsx";
import { ArrowUpRight } from "lucide-react";

import { MODALITY_COLOR, type FinalModality } from "@/lib/architecture";
import { downsampleExtremaPreserving } from "@/lib/monitoring/waveformDisplay";
import { useOperationalViewModel, type OperationalModalityState } from "@/lib/monitoring/operationalViewModel";

/** Percent-of-container node positions, chosen to sit on the SVG figure below. */
const NODE_POSITION: Record<FinalModality, { left: number; top: number }> = {
  EEG: { left: 41, top: 9 },
  EOG: { left: 59, top: 9 },
  ECG: { left: 50, top: 37 },
  PPG: { left: 21, top: 61 },
  IMU: { left: 30, top: 67 },
};

function buildSparklinePath(values: number[], width: number, height: number): string | null {
  const finite = values.filter((value) => Number.isFinite(value));
  if (finite.length < 2) return null;
  const { points } = downsampleExtremaPreserving(finite, 24);
  let min = points[0]!.value;
  let max = points[0]!.value;
  for (const point of points) {
    if (point.value < min) min = point.value;
    if (point.value > max) max = point.value;
  }
  const range = max - min || 1;
  return points
    .map((point, index) => {
      const x = (index / (points.length - 1)) * width;
      const y = height - ((point.value - min) / range) * height;
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

function NodeRing({ state, color, size }: { state: OperationalModalityState["nodeState"]; color: string; size: number }) {
  const r = size / 2 - 2;
  const circumference = 2 * Math.PI * r;
  if (state === "confirmed") {
    return (
      <svg width={size} height={size} className="absolute inset-0" aria-hidden="true">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={1.75} />
        <circle cx={size / 2} cy={size / 2} r={r - 5} fill={color} opacity={0.85} />
      </svg>
    );
  }
  if (state === "warmup") {
    return (
      <svg width={size} height={size} className="absolute inset-0" aria-hidden="true">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="#D5A45E"
          strokeWidth={1.75}
          strokeDasharray={`${circumference / 10} ${circumference / 14}`}
        />
        <circle cx={size / 2} cy={size / 2} r={r - 5} fill="#D5A45E" opacity={0.5} />
      </svg>
    );
  }
  if (state === "fault") {
    return (
      <svg width={size} height={size} className="absolute inset-0" aria-hidden="true">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="#D46F70"
          strokeWidth={2}
          strokeDasharray={`${circumference * 0.55} ${circumference * 0.45}`}
        />
        <text x={size / 2} y={size / 2 + 3} textAnchor="middle" fontSize={7} fontWeight={700} fill="#D46F70">
          SIM
        </text>
      </svg>
    );
  }
  if (state === "disconnected") {
    return (
      <svg width={size} height={size} className="absolute inset-0 opacity-40" aria-hidden="true">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#516269" strokeWidth={1.5} />
      </svg>
    );
  }
  // unavailable — open gray ring
  return (
    <svg width={size} height={size} className="absolute inset-0" aria-hidden="true">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#516269" strokeWidth={1.5} strokeDasharray={`${circumference * 0.7} ${circumference * 0.3}`} />
    </svg>
  );
}

/**
 * Dominant operational body/sensor visualization for `/mission-overview`
 * (master prompt 3 §12). A generic technical human outline — not the
 * Digital Twin, not a specific person — showing the five final-architecture
 * sensor placements and their current channel state, all derived from
 * `useOperationalViewModel()`.
 */
export function CrewPhysiologyMap() {
  const view = useOperationalViewModel();
  const [selected, setSelected] = useState<FinalModality>("PPG");
  const selectedEntry = view.modalities.find((entry) => entry.modality === selected) ?? view.modalities[0]!;

  return (
    <section aria-labelledby="crew-physiology-heading" className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4 sm:p-5">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="crew-physiology-heading" className="text-sm font-semibold text-ink-primary">
          Sensing system map
        </h2>
        <span className="text-[11px] uppercase tracking-wide text-ink-muted">CORE_PLUS_CONTEXT · 5 modalities</span>
      </div>

      <div className="relative mx-auto aspect-[3/4] w-full max-w-[360px]">
        <svg viewBox="0 0 300 400" className="absolute inset-0 h-full w-full" aria-hidden="true">
          {/* Region halos — physical module locations, not quality percentages. */}
          <ellipse cx={150} cy={44} rx={58} ry={42} fill="rgba(105,183,173,0.05)" stroke="rgba(105,183,173,0.14)" />
          <ellipse cx={150} cy={150} rx={72} ry={58} fill="rgba(121,167,211,0.04)" stroke="rgba(121,167,211,0.12)" />
          <ellipse cx={78} cy={252} rx={48} ry={38} fill="rgba(199,154,91,0.04)" stroke="rgba(199,154,91,0.12)" />

          {/* Abstract technical human outline. */}
          <g fill="none" stroke="#30464F" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round">
            <circle cx={150} cy={55} r={34} />
            <line x1={150} y1={89} x2={150} y2={112} />
            <path d="M100,150 L90,112 L210,112 L200,150 L200,270 L100,270 Z" />
            <path d="M100,120 L55,190 L48,250" />
            <path d="M200,120 L245,190 L252,250" />
            <path d="M120,270 L112,380" />
            <path d="M180,270 L188,380" />
          </g>
        </svg>

        {view.modalities.map((entry) => {
          const position = NODE_POSITION[entry.modality];
          const color = MODALITY_COLOR[entry.modality];
          const isSelected = entry.modality === selected;
          const sparkline = entry.plot ? buildSparklinePath(entry.plot.values.slice(-96), 44, 16) : null;
          return (
            <button
              key={entry.modality}
              type="button"
              onClick={() => setSelected(entry.modality)}
              aria-pressed={isSelected}
              className={clsx(
                "group absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-1 rounded-full p-1 outline-none transition-transform duration-200 focus-visible:ring-2 focus-visible:ring-final-accent",
                isSelected && "scale-110",
              )}
              style={{ left: `${position.left}%`, top: `${position.top}%` }}
            >
              <span className="relative flex h-9 w-9 items-center justify-center">
                <NodeRing state={entry.nodeState} color={color} size={36} />
              </span>
              <span
                className={clsx(
                  "rounded-[3px] px-1 text-[9px] font-semibold uppercase tracking-wide",
                  isSelected ? "bg-surface-3 text-ink-primary" : "text-ink-muted",
                )}
              >
                {entry.modality}
              </span>
              {sparkline ? (
                <svg width={44} height={16} viewBox="0 0 44 16" className="opacity-80" aria-hidden="true">
                  <path d={sparkline} fill="none" stroke={color} strokeWidth={1.2} />
                </svg>
              ) : null}
            </button>
          );
        })}
      </div>

      <div className="flex flex-col gap-1.5 rounded-[8px] border border-jury-border-subtle bg-surface-2 p-3 text-xs">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="font-semibold text-ink-primary">
            {selectedEntry.modality} <span className="font-normal text-ink-muted">— {selectedEntry.region}</span>
          </span>
          <span
            className={clsx(
              "rounded-[4px] border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
              selectedEntry.nodeState === "confirmed" && "border-jury-success/40 bg-jury-success-soft text-jury-success",
              selectedEntry.nodeState === "warmup" && "border-jury-warning/40 bg-jury-warning-soft text-jury-warning",
              selectedEntry.nodeState === "fault" && "border-jury-fault/40 bg-jury-fault-soft text-jury-fault",
              (selectedEntry.nodeState === "unavailable" || selectedEntry.nodeState === "disconnected") &&
                "border-ink-disabled/40 bg-surface-3 text-ink-disabled",
            )}
          >
            {selectedEntry.stateLabel}
          </span>
        </div>
        <p className="text-ink-secondary">{selectedEntry.observation.statusLabel}</p>
        <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] text-ink-muted sm:grid-cols-4">
          <div>
            <dt className="uppercase tracking-wide">Source</dt>
            <dd className="text-ink-secondary">{view.sourceLabel}</dd>
          </div>
          <div>
            <dt className="uppercase tracking-wide">Channel</dt>
            <dd className="text-ink-secondary">{selectedEntry.observation.channelName ?? "None"}</dd>
          </div>
          <div>
            <dt className="uppercase tracking-wide">Samples</dt>
            <dd className="text-ink-secondary">{selectedEntry.plot ? selectedEntry.plot.values.length : "—"}</dd>
          </div>
          <div>
            <dt className="uppercase tracking-wide">Unit</dt>
            <dd className="text-ink-secondary">{selectedEntry.plot?.unit ?? "Unit not provided"}</dd>
          </div>
        </dl>
        <Link
          href="/live-monitoring"
          className="mt-1 flex w-fit items-center gap-1 text-[11px] font-medium text-information underline underline-offset-2"
        >
          Open detailed waveform <ArrowUpRight size={11} aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}
