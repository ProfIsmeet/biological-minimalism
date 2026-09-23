"use client";

import Link from "next/link";
import clsx from "clsx";

import { MODALITY_COLOR, type FinalModality } from "@/lib/architecture";
import { round2 } from "@/lib/format";
import { useOperationalViewModel, type ModalityNodeState } from "@/lib/monitoring/operationalViewModel";

/** Body-topology order: EEG/EOG upper orbit, ECG middle, PPG/IMU lower orbit. */
const ORBIT_ORDER: { modality: FinalModality; angleDeg: number }[] = [
  { modality: "EEG", angleDeg: -125 },
  { modality: "EOG", angleDeg: -55 },
  { modality: "ECG", angleDeg: 0 },
  { modality: "PPG", angleDeg: 125 },
  { modality: "IMU", angleDeg: 195 },
];

function nodeColor(state: ModalityNodeState, base: string): string {
  if (state === "fault") return "#D46F70";
  if (state === "disconnected" || state === "unavailable" || state === "source_error") return "#516269";
  if (state === "warmup" || state === "awaiting_confirmation") return "#D5A45E";
  return base;
}

interface SensorConstellationProps {
  compact?: boolean;
}

/**
 * Rapid five-modality availability summary (master prompt 3 §14). Distinct
 * from CrewPhysiologyMap: this is about the sensing/source topology, not
 * anatomical placement, so nodes never connect to each other or to an HR
 * concept — only to the central source node.
 */
export function SensorConstellation({ compact = false }: SensorConstellationProps) {
  const view = useOperationalViewModel();
  const size = compact ? 168 : 220;
  const center = size / 2;
  const orbitRadius = compact ? 62 : 82;
  const nodeSize = compact ? 22 : 28;

  return (
    <section aria-labelledby="sensor-constellation-heading" className={clsx("flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1", compact ? "p-3" : "p-4")}>
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="sensor-constellation-heading" className="text-sm font-semibold text-ink-primary">
          Sensor constellation
        </h2>
        {!compact ? (
          <Link href="/live-monitoring" className="text-[11px] font-medium text-information underline underline-offset-2">
            Live signals
          </Link>
        ) : null}
      </div>

      <div className="relative mx-auto" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="absolute inset-0" aria-hidden="true">
          {ORBIT_ORDER.map(({ modality, angleDeg }) => {
            const rad = (angleDeg * Math.PI) / 180;
            const x = round2(center + orbitRadius * Math.cos(rad));
            const y = round2(center + orbitRadius * Math.sin(rad));
            const entry = view.modalities.find((item) => item.modality === modality)!;
            return (
              <line
                key={modality}
                x1={center}
                y1={center}
                x2={x}
                y2={y}
                stroke={entry.nodeState === "fault" ? "#D46F70" : "#203239"}
                strokeWidth={1}
              />
            );
          })}
        </svg>

        <div
          className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center gap-0.5 rounded-full border border-jury-border-strong bg-surface-2 text-center"
          style={{ left: center, top: center, width: compact ? 56 : 68, height: compact ? 56 : 68 }}
        >
          <span className="text-[9px] font-semibold uppercase tracking-wide text-ink-muted">{view.isReplay ? "Replay" : "Synthetic"}</span>
          <span className={clsx("text-[10px] font-semibold", view.connected ? "text-jury-success" : "text-jury-fault")}>
            {view.connected ? "Connected" : "Down"}
          </span>
        </div>

        {ORBIT_ORDER.map(({ modality, angleDeg }) => {
          const rad = (angleDeg * Math.PI) / 180;
          const x = round2(center + orbitRadius * Math.cos(rad));
          const y = round2(center + orbitRadius * Math.sin(rad));
          const entry = view.modalities.find((item) => item.modality === modality)!;
          const color = nodeColor(entry.nodeState, MODALITY_COLOR[modality]);
          const nodeClassName = "absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-0.5 outline-none focus-visible:ring-2 focus-visible:ring-final-accent";
          const nodeTitle = `${modality} — ${entry.stateLabel}${compact ? " — jump to plot" : ""}`;
          const nodeContent = (
            <>
              <span
                aria-hidden="true"
                className="flex items-center justify-center rounded-full border-2"
                style={{ width: nodeSize, height: nodeSize, borderColor: color, backgroundColor: entry.nodeState === "confirmed" ? `${color}33` : "transparent" }}
              />
              <span className="text-[9px] font-semibold uppercase tracking-wide text-ink-muted">{modality}</span>
            </>
          );
          return compact ? (
            <a key={modality} href={`#signal-${modality}`} className={nodeClassName} style={{ left: x, top: y }} title={nodeTitle}>
              {nodeContent}
            </a>
          ) : (
            <div key={modality} className={nodeClassName} style={{ left: x, top: y }} title={nodeTitle}>
              {nodeContent}
            </div>
          );
        })}
      </div>

      <p className="text-center text-xs text-ink-secondary">
        {view.confirmedModalityCount} of {view.totalModalityCount} channels confirmed
        {view.faultActive ? ` · ${view.faultedModalities.length} simulated fault${view.faultedModalities.length === 1 ? "" : "s"}` : ""}
      </p>
    </section>
  );
}
