"use client";

import { useEffect, useRef, useState } from "react";
import clsx from "clsx";

import { MODALITY_COLOR } from "@/lib/architecture";
import { computeHrSegments } from "@/lib/monitoring/hrSegments";
import { deriveHrCorePresentation } from "@/lib/monitoring/hrOperationalPresentation";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";

const LARGE_DESKTOP_SIZE = 200;
const COMPACT_DESKTOP_SIZE = 176;
const MOBILE_SIZE = 148;
const STROKE = 10;
const GAP_DEGREES = 6;

function polarPoint(cx: number, cy: number, r: number, angleDeg: number): { x: number; y: number } {
  const angleRad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: Math.round((cx + r * Math.cos(angleRad)) * 100) / 100, y: Math.round((cy + r * Math.sin(angleRad)) * 100) / 100 };
}

function arcPath(cx: number, cy: number, r: number, startDeg: number, endDeg: number): string {
  const start = polarPoint(cx, cy, r, startDeg);
  const end = polarPoint(cx, cy, r, endDeg);
  const largeArc = endDeg - startDeg > 180 ? 1 : 0;
  return `M${start.x},${start.y} A${r},${r} 0 ${largeArc} 1 ${end.x},${end.y}`;
}

/**
 * Compact circular HR-inference readout for `/mission-overview`. The outer
 * ring is a fixed four-segment availability checklist (SRC/PPG/IMU/OUT),
 * never a continuous confidence arc.
 */
export function HRInferenceCore() {
  const view = useOperationalViewModel();
  const ppg = view.modalities.find((entry) => entry.modality === "PPG")!;
  const imu = view.modalities.find((entry) => entry.modality === "IMU")!;

  const [size, setSize] = useState(LARGE_DESKTOP_SIZE);
  useEffect(() => {
    function applySize() {
      setSize(window.innerWidth < 640 ? MOBILE_SIZE : window.innerWidth < 1536 ? COMPACT_DESKTOP_SIZE : LARGE_DESKTOP_SIZE);
    }
    applySize();
    window.addEventListener("resize", applySize);
    return () => window.removeEventListener("resize", applySize);
  }, []);
  const center = size / 2;
  const radius = center - STROKE / 2 - 4;

  // Prompt 3A.1 §4.2 — a single telemetry-availability check replaces the
  // previous ad hoc `connected && !isWaitingForConfirmation` combination, so
  // this ring also fails closed during a REST-only source_error (where the
  // WebSocket could technically still be open).
  const sourceConfirmed = view.telemetryAvailability === "active";
  const ppgAvailable = ppg.nodeState === "confirmed";
  const imuAvailable = imu.nodeState === "confirmed";
  const modelOutputAvailable = view.predictionAvailability === "available";

  const segments = computeHrSegments({
    sourceConfirmed,
    ppgAvailable,
    imuAvailable,
    modelOutputAvailable,
    ppgFaulted: ppg.nodeState === "fault",
    imuFaulted: imu.nodeState === "fault",
  });

  // §3C.1 §7 — latches true the instant a fault is seen and only clears once
  // output genuinely resumes. A plain "record last faultActive value" ref
  // instead gets overwritten to false by the intermediate warm-up render
  // (faultActive already false, modelOutputAvailable still false) that
  // usually follows a Clear-fault action, so the later render where
  // modelOutputAvailable finally flips true no longer sees a fault in its
  // immediate past and the Recovered badge silently never fires.
  const recentlyFaulted = useRef(false);
  const [recoveredUntil, setRecoveredUntil] = useState<number | null>(null);
  useEffect(() => {
    if (view.faultActive) recentlyFaulted.current = true;
  }, [view.faultActive]);
  useEffect(() => {
    if (recentlyFaulted.current && !view.faultActive && modelOutputAvailable) {
      setRecoveredUntil(Date.now() + 4000);
      recentlyFaulted.current = false;
    }
  }, [view.faultActive, modelOutputAvailable]);
  useEffect(() => {
    if (recoveredUntil === null) return;
    const timeout = setTimeout(() => setRecoveredUntil(null), Math.max(0, recoveredUntil - Date.now()));
    return () => clearTimeout(timeout);
  }, [recoveredUntil]);
  const showRecovered = recoveredUntil !== null && Date.now() < recoveredUntil;

  const arcSpan = 360 / segments.length;

  const { centerValue, centerReason, nextStateText } = deriveHrCorePresentation({
    telemetryAvailability: view.telemetryAvailability,
    isReplay: view.isReplay,
    predictionValue: view.prediction?.value ?? null,
    inferenceStatusLabel: view.inferenceStatusLabel,
    faultActive: view.faultActive,
    requiredWindowSeconds: view.inference?.required_window_seconds ?? null,
  });

  return (
    <section aria-labelledby="hr-core-heading" className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-3">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="hr-core-heading" className="text-sm font-semibold text-ink-primary">
          Heart-rate inference
        </h2>
        {showRecovered ? (
          <span className="rounded-[4px] border border-jury-success/40 bg-jury-success-soft px-2 py-1 text-xs font-semibold uppercase tracking-wide text-jury-success">
            Recovered
          </span>
        ) : view.faultActive ? (
          <span className="rounded-[4px] border border-jury-fault/40 bg-jury-fault-soft px-2 py-1 text-xs font-semibold uppercase tracking-wide text-jury-fault">
            Simulated fault
          </span>
        ) : null}
      </div>

      <p className="text-xs leading-snug text-ink-muted">Four independent availability checks · not confidence or model certainty</p>

      <p className="rounded-[6px] border border-jury-border-subtle bg-surface-2 px-2.5 py-2 text-xs leading-snug text-ink-secondary">
        {nextStateText}
      </p>

      <div className="relative mx-auto" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
          <circle cx={center} cy={center} r={radius} fill="none" stroke="#16262C" strokeWidth={STROKE} />
          {segments.map((segment, index) => {
            const start = index * arcSpan + GAP_DEGREES / 2;
            const end = (index + 1) * arcSpan - GAP_DEGREES / 2;
            return (
              <path
                key={segment.key}
                d={arcPath(center, center, radius, start, end)}
                fill="none"
                stroke={segment.faulted ? "#D46F70" : segment.on ? "#69B7AD" : "#30464F"}
                strokeWidth={STROKE}
                strokeLinecap="round"
                strokeDasharray={segment.faulted ? `${STROKE} ${STROKE * 0.7}` : undefined}
              />
            );
          })}
        </svg>
        {/* The four categorical states (SRC/PPG/IMU/OUT) used to be labeled
            in-ring at 8px, unreadable from any real viewing distance. The
            ring now carries color/state only; the readable 13px checklist
            below is the sole source of truth for what each segment means —
            removes redundant unreadable text instead of duplicating it. */}
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-1 px-8 text-center">
          {centerValue ? (
            <>
              <span className="font-mono text-[clamp(38px,10vw,56px)] font-semibold leading-none tabular-nums text-ink-primary">{centerValue}</span>
              <span className="text-sm text-ink-muted">bpm</span>
              <span className="mt-1 max-w-[140px] text-[13px] leading-snug text-ink-secondary">{centerReason}</span>
            </>
          ) : (
            <>
              <span className="text-[26px] font-semibold leading-tight text-ink-disabled">Unavailable</span>
              <span className="mt-1 line-clamp-3 max-w-[150px] text-[13px] leading-snug text-ink-secondary">{centerReason}</span>
            </>
          )}
        </div>
      </div>

      <ul className="grid grid-cols-1 gap-1.5 text-[13px] text-ink-secondary min-[420px]:grid-cols-2">
        {segments.map((segment) => (
          <li key={segment.key} className="flex items-center gap-1.5">
            <span aria-hidden="true" className={clsx("h-2 w-2 shrink-0 rounded-full", segment.faulted ? "bg-jury-fault" : segment.on ? "bg-final-accent" : "bg-ink-disabled")} />
            <span className="font-semibold text-ink-primary">{segment.abbr}</span> {segment.label}: {segment.on ? "Yes" : "No"}
          </li>
        ))}
      </ul>
      <p className="flex items-center justify-center gap-1.5 text-xs text-ink-muted">
        <span style={{ color: MODALITY_COLOR.PPG }}>PPG</span> + <span style={{ color: MODALITY_COLOR.IMU }}>IMU</span> → <span className="font-semibold text-final-accent">HR</span>
      </p>
    </section>
  );
}
