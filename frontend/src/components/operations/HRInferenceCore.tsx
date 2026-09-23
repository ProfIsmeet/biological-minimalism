"use client";

import { useEffect, useRef, useState } from "react";
import clsx from "clsx";

import { MODALITY_COLOR } from "@/lib/architecture";
import { computeHrSegments } from "@/lib/monitoring/hrSegments";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";

const DESKTOP_SIZE = 180;
const MOBILE_SIZE = 158;
const STROKE = 9;
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
 * Compact circular HR-inference readout for `/mission-overview` (master
 * prompt 3A §10). Diameter is capped to 158–180px so `Unavailable` never
 * dominates the mobile viewport; the outer ring stays a fixed four-segment
 * categorical display (SRC/PPG/IMU/OUT), never a continuous confidence arc.
 */
export function HRInferenceCore() {
  const view = useOperationalViewModel();
  const ppg = view.modalities.find((entry) => entry.modality === "PPG")!;
  const imu = view.modalities.find((entry) => entry.modality === "IMU")!;

  const [size, setSize] = useState(DESKTOP_SIZE);
  useEffect(() => {
    function applySize() {
      setSize(window.innerWidth < 640 ? MOBILE_SIZE : DESKTOP_SIZE);
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

  let centerValue: string | null = null;
  let centerReason: string;
  if (view.telemetryAvailability === "source_error") {
    centerReason = "Source error";
  } else if (view.telemetryAvailability === "disconnected") {
    centerReason = "Source disconnected";
  } else if (view.telemetryAvailability === "awaiting_confirmation") {
    centerReason = "Awaiting confirmed frame";
  } else if (!view.isReplay) {
    centerReason = "Not applicable — synthetic demo";
  } else if (view.prediction) {
    centerValue = view.prediction.value.toFixed(1);
    centerReason = view.inferenceStatusLabel;
  } else {
    centerReason = view.inferenceStatusLabel;
  }

  return (
    <section aria-labelledby="hr-core-heading" className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-3">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="hr-core-heading" className="text-sm font-semibold text-ink-primary">
          Heart-rate inference
        </h2>
        {showRecovered ? (
          <span className="rounded-[4px] border border-jury-success/40 bg-jury-success-soft px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-jury-success">
            Recovered
          </span>
        ) : view.faultActive ? (
          <span className="rounded-[4px] border border-jury-fault/40 bg-jury-fault-soft px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-jury-fault">
            Simulated fault
          </span>
        ) : null}
      </div>

      <div className="relative mx-auto" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
          <circle cx={center} cy={center} r={radius} fill="none" stroke="#16262C" strokeWidth={STROKE} />
          {segments.map((segment, index) => {
            const start = index * arcSpan + GAP_DEGREES / 2;
            const end = (index + 1) * arcSpan - GAP_DEGREES / 2;
            const mid = (start + end) / 2;
            const labelPoint = polarPoint(center, center, radius + STROKE / 2 + 8, mid);
            return (
              <g key={segment.key}>
                <path
                  d={arcPath(center, center, radius, start, end)}
                  fill="none"
                  stroke={segment.faulted ? "#D46F70" : segment.on ? "#69B7AD" : "#30464F"}
                  strokeWidth={STROKE}
                  strokeLinecap="round"
                  strokeDasharray={segment.faulted ? `${STROKE} ${STROKE * 0.7}` : undefined}
                />
                <text x={labelPoint.x} y={labelPoint.y} textAnchor="middle" dominantBaseline="middle" fontSize={8} fontWeight={700} fill={segment.faulted ? "#D46F70" : segment.on ? "#69B7AD" : "#516269"}>
                  {segment.abbr}
                </text>
              </g>
            );
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5 px-7 text-center">
          {centerValue ? (
            <>
              <span className="font-mono text-[clamp(30px,9vw,46px)] font-semibold leading-none tabular-nums text-ink-primary">{centerValue}</span>
              <span className="text-[12px] text-ink-muted">bpm</span>
              <span className="mt-0.5 max-w-[120px] text-[11px] leading-snug text-ink-secondary">{centerReason}</span>
            </>
          ) : (
            <>
              <span className="text-[20px] font-semibold leading-tight text-ink-disabled">Unavailable</span>
              <span className="mt-0.5 line-clamp-3 max-w-[130px] text-[11px] leading-snug text-ink-muted">{centerReason}</span>
            </>
          )}
        </div>
      </div>

      <ul className="grid grid-cols-2 gap-x-3 gap-y-1 text-[10px] text-ink-secondary">
        {segments.map((segment) => (
          <li key={segment.key} className="flex items-center gap-1.5">
            <span aria-hidden="true" className={clsx("h-1.5 w-1.5 rounded-full", segment.on ? "bg-final-accent" : "bg-ink-disabled")} />
            <span className="font-semibold">{segment.abbr}</span> {segment.label}: {segment.on ? "Yes" : "No"}
          </li>
        ))}
      </ul>
      <p className="flex items-center justify-center gap-1.5 text-[10px] text-ink-muted">
        <span style={{ color: MODALITY_COLOR.PPG }}>PPG</span> + <span style={{ color: MODALITY_COLOR.IMU }}>IMU</span> → <span className="font-semibold text-final-accent">HR</span>
      </p>
    </section>
  );
}
