"use client";

import { useEffect, useRef, useState } from "react";

import { deriveIntegrityRings, type IntegrityState } from "@/lib/monitoring/integrityRings";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";

const SIZE = 232;
const CENTER = SIZE / 2;
const RING_RADII = [42, 60, 78, 96];

const STROKE: Record<IntegrityState, { color: string; dash?: string; opacity: number }> = {
  confirmed: { color: "#45D6E5", opacity: 1 },
  recovered: { color: "#63BFB7", opacity: 1 },
  awaiting: { color: "#D5A45E", dash: "5 4", opacity: 0.9 },
  warmup: { color: "#D5A45E", dash: "9 5", opacity: 0.9 },
  unavailable: { color: "#516269", dash: "2 5", opacity: 0.7 },
  fault: { color: "#D46F70", dash: "6 5", opacity: 1 },
  disconnected: { color: "#516269", opacity: 0.45 },
  source_error: { color: "#D46F70", dash: "2 5", opacity: 0.8 },
};

const STATE_WORD: Record<IntegrityState, string> = {
  confirmed: "Confirmed",
  recovered: "Recovered",
  awaiting: "Awaiting",
  warmup: "Warm-up",
  unavailable: "Unavailable",
  fault: "Simulated fault",
  disconnected: "Disconnected",
  source_error: "Source error",
};

/**
 * Prompt 3B §8 — Concentric Inference Integrity Orbit. Four categorical rings
 * (Source / PPG / IMU / Output) around the current HR value. Every ring is a
 * full circle with a categorical dash/colour treatment — no percentage,
 * confidence, or partial-arc probability. Driven entirely by the shared
 * operational view model.
 */
export function InferenceIntegrityOrbit() {
  const view = useOperationalViewModel();
  const ppg = view.modalities.find((m) => m.modality === "PPG")!;
  const imu = view.modalities.find((m) => m.modality === "IMU")!;
  const predictionAvailable = view.predictionAvailability === "available";
  const inferenceWarmingUp = view.inference?.status === "warming_up";

  // §3C.1 §7 — same fix as HRInferenceCore.tsx: latch "recently faulted" true
  // the instant a fault is seen and only clear it once prediction genuinely
  // resumes, rather than overwriting the ref back to false on the
  // intermediate warm-up render that usually sits between fault-clear and
  // prediction-available (which silently prevented Recovered from ever
  // firing).
  const recentlyFaulted = useRef(false);
  const [recoveredUntil, setRecoveredUntil] = useState<number | null>(null);
  useEffect(() => {
    if (view.faultActive) recentlyFaulted.current = true;
  }, [view.faultActive]);
  useEffect(() => {
    if (recentlyFaulted.current && !view.faultActive && predictionAvailable) {
      setRecoveredUntil(Date.now() + 4000);
      recentlyFaulted.current = false;
    }
  }, [view.faultActive, predictionAvailable]);
  useEffect(() => {
    if (recoveredUntil === null) return;
    const timer = setTimeout(() => setRecoveredUntil(null), Math.max(0, recoveredUntil - Date.now()));
    return () => clearTimeout(timer);
  }, [recoveredUntil]);
  const recovered = recoveredUntil !== null && Date.now() < recoveredUntil;

  const rings = deriveIntegrityRings({
    telemetry: view.telemetryAvailability,
    ppgState: ppg.nodeState,
    imuState: imu.nodeState,
    isReplay: view.isReplay,
    predictionAvailable,
    inferenceWarmingUp: Boolean(inferenceWarmingUp),
    recovered,
  });

  let centerValue: string | null = null;
  let centerReason: string;
  if (view.telemetryAvailability === "source_error") centerReason = "Source error";
  else if (view.telemetryAvailability === "disconnected") centerReason = "Source disconnected";
  else if (view.telemetryAvailability === "awaiting_confirmation") centerReason = "Awaiting confirmed frame";
  else if (!view.isReplay) centerReason = "Not applicable — synthetic demo";
  else if (view.prediction) {
    centerValue = view.prediction.value.toFixed(1);
    centerReason = recovered ? "Recovered" : view.inferenceStatusLabel;
  } else centerReason = view.inferenceStatusLabel;

  return (
    <section aria-labelledby="integrity-orbit-heading" className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="integrity-orbit-heading" className="text-sm font-semibold text-ink-primary">
          Inference integrity
        </h2>
        {recovered ? (
          <span className="rounded-[4px] border border-jury-success/40 bg-jury-success-soft px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-jury-success">Recovered</span>
        ) : view.faultActive ? (
          <span className="rounded-[4px] border border-jury-fault/40 bg-jury-fault-soft px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-jury-fault">Simulated fault</span>
        ) : null}
      </div>

      <div className="flex flex-col items-center gap-3 sm:flex-row sm:items-center sm:gap-5">
        <div className="relative shrink-0" style={{ width: SIZE, height: SIZE }}>
          <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} aria-hidden="true">
            {rings.map((ring, i) => {
              const r = RING_RADII[i]!;
              const s = STROKE[ring.state];
              return (
                <g key={ring.key}>
                  <circle cx={CENTER} cy={CENTER} r={r} fill="none" stroke={s.color} strokeWidth={2} strokeDasharray={s.dash} opacity={s.opacity} />
                  <text x={CENTER} y={CENTER - r - 4} textAnchor="middle" fontSize={10} fontWeight={700} fill={s.color} opacity={Math.min(1, s.opacity + 0.2)}>
                    {ring.label.toUpperCase()}
                  </text>
                </g>
              );
            })}
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5 px-10 text-center">
            {centerValue ? (
              <>
                <span className="font-mono text-[clamp(28px,7vw,40px)] font-semibold leading-none tabular-nums text-ink-primary">{centerValue}</span>
                <span className="text-[11px] text-ink-muted">bpm</span>
                <span className="mt-0.5 max-w-[110px] text-[10px] leading-snug text-ink-secondary">{centerReason}</span>
              </>
            ) : (
              <>
                <span className="text-[18px] font-semibold leading-tight text-ink-disabled">Unavailable</span>
                <span className="mt-0.5 line-clamp-3 max-w-[120px] text-[10px] leading-snug text-ink-muted">{centerReason}</span>
              </>
            )}
          </div>
        </div>

        {/* §18 — textual four-row state summary. */}
        <ul className="flex w-full flex-col gap-1.5 text-[11px]">
          {rings.map((ring) => (
            <li key={ring.key} className="flex items-center justify-between gap-2 rounded-[5px] border border-jury-border-subtle bg-surface-2 px-2 py-1">
              <span className="flex items-center gap-1.5">
                <span aria-hidden="true" className="h-2 w-2 rounded-full" style={{ backgroundColor: STROKE[ring.state].color }} />
                <span className="font-semibold text-ink-primary">{ring.label}</span>
              </span>
              <span className="text-ink-secondary">{STATE_WORD[ring.state]}</span>
            </li>
          ))}
        </ul>
      </div>

      <p className="text-[10px] leading-snug text-ink-muted">Categorical signal-path integrity — not a confidence score.</p>
    </section>
  );
}
