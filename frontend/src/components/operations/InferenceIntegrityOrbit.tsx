"use client";

import { useEffect, useRef, useState } from "react";

import { deriveIntegrityRings, type IntegrityRing } from "@/lib/monitoring/integrityRings";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";
import { INTEGRITY_STATE_TREATMENT, resolveRingStroke, type StageKey } from "@/lib/visualization/operationalVisualTokens";
import { fixedOrbitArcPath } from "@/lib/visualization/concentricOrbitGeometry";

/**
 * Mission Overview §9 — the restored four-ring concentric Inference Integrity
 * graphic, rebuilt at command-deck scale against the SAME authoritative
 * `deriveIntegrityRings` derivation the earlier implementation used (unchanged).
 *
 * WHAT THE RINGS MEAN — and explicitly do not mean:
 *
 * Four categorical path-integrity indicators, outside-in: Source authority,
 * PPG input, IMU input, HR model output. EVERY ring draws the IDENTICAL fixed
 * 300-degree sweep regardless of its state, so a longer or shorter arc can
 * never be misread as "more" or "less". There is no percentage, confidence,
 * probability, reliability or accuracy encoded in any arc length anywhere in
 * this component — state is carried by colour AND dash pattern AND a word in
 * the adjacent legend, never by geometry and never by colour alone.
 *
 * Why the earlier version's labels are gone: commit d49c3a2 correctly removed
 * unreadable 8-10px text set along the circles. That decision is preserved —
 * ring identity lives in a 12px+ legend with matching line swatches, not in
 * micro-text on the arcs.
 */
const DESKTOP = { size: 320, center: 160, radii: [138, 111, 86, 63], strokes: [13, 12, 11, 10] };
const MOBILE = { size: 288, center: 144, radii: [124, 100, 77, 57], strokes: [11, 10, 9.5, 9] };

const STAGE_KEYS: StageKey[] = ["source", "ppg", "imu", "output"];

const RING_LABEL: Record<StageKey, string> = {
  source: "Source authority",
  ppg: "PPG input",
  imu: "IMU input",
  output: "HR output",
};

function OrbitSvg({
  rings,
  geometry,
  className,
}: {
  rings: IntegrityRing[];
  geometry: typeof DESKTOP;
  className: string;
}) {
  return (
    <svg width={geometry.size} height={geometry.size} viewBox={`0 0 ${geometry.size} ${geometry.size}`} className={className} aria-hidden="true" focusable="false">
      {rings.map((ring, i) => {
        const stage = STAGE_KEYS[i]!;
        const r = geometry.radii[i]!;
        const strokeWidth = geometry.strokes[i]!;
        const treatment = INTEGRITY_STATE_TREATMENT[ring.state];
        const color = resolveRingStroke(stage, ring.state);
        const d = fixedOrbitArcPath(geometry.center, geometry.center, r);
        return (
          <g key={ring.key}>
            {/* Subtle full track behind every arc (§9.2) — 3px, low opacity.
                Deliberately no numeric-percent token in this file at all: a
                structural guard forbids one anywhere in these views, and it
                is right to, because the rings encode nothing quantitative. */}
            <path d={d} fill="none" stroke={color} strokeWidth={3} opacity={0.2} strokeLinecap="butt" />
            <path
              d={d}
              fill="none"
              stroke={color}
              strokeWidth={strokeWidth}
              strokeDasharray={treatment.dash}
              strokeLinecap={treatment.roundCap ? "round" : "butt"}
              opacity={treatment.opacity}
            />
          </g>
        );
      })}
    </svg>
  );
}

export function InferenceIntegrityOrbit() {
  const view = useOperationalViewModel();
  const ppg = view.modalities.find((m) => m.modality === "PPG")!;
  const imu = view.modalities.find((m) => m.modality === "IMU")!;
  const predictionAvailable = view.predictionAvailability === "available";
  const inferenceWarmingUp = view.inference?.status === "warming_up";

  // Latch "recently faulted" true the instant a fault is seen and only clear
  // it once prediction genuinely resumes — preserved verbatim from the prior
  // implementation (it fixes a real bug where the intermediate warm-up render
  // between fault-clear and prediction-available silently prevented Recovered
  // from ever firing).
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

  // Centre content (§9.4). A value is shown ONLY when the authoritative view
  // model currently has one — never a retained previous value behind an
  // unavailable state, and never "0 bpm" as a stand-in for missing output.
  let centerValue: string | null = null;
  let centerReason: string;
  if (view.telemetryAvailability === "source_error") centerReason = "Source error";
  else if (view.telemetryAvailability === "disconnected") centerReason = "Source disconnected";
  else if (view.telemetryAvailability === "awaiting_confirmation") centerReason = "Awaiting confirmation";
  else if (!view.isReplay) centerReason = "Not applicable — synthetic demo";
  else if (view.prediction) {
    centerValue = view.prediction.value.toFixed(1);
    centerReason = recovered ? "Recovered" : "Model output available";
  } else centerReason = view.inferenceStatusLabel;

  const accessibleSummary = rings
    .map((ring, i) => `${RING_LABEL[STAGE_KEYS[i]!]}: ${INTEGRITY_STATE_TREATMENT[ring.state].word}`)
    .join(". ");

  return (
    <section
      aria-labelledby="integrity-orbit-heading"
      aria-describedby="integrity-orbit-desc"
      className="flex h-full flex-col gap-4 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-[18px]"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="integrity-orbit-heading" className="text-[17px] font-semibold leading-tight text-ink-primary">
          Inference integrity
        </h2>
        <span className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Categorical · not a confidence score</span>
      </div>
      <p id="integrity-orbit-desc" className="sr-only">
        Four categorical signal-path integrity rings. Every ring uses an identical fixed arc length; arc length never encodes a
        quantity. Current states — {accessibleSummary}.
      </p>

      <div className="flex flex-col items-center gap-4">
        <div className="relative shrink-0">
          <OrbitSvg rings={rings} geometry={DESKTOP} className="hidden sm:block" />
          <OrbitSvg rings={rings} geometry={MOBILE} className="block sm:hidden" />

          {/* The innermost ring (r=63, 10px stroke) leaves only ~116px of
              clear diameter, so ONLY the value and its unit live inside the
              circle. The label, status and the required "Not model
              confidence" note are rendered immediately BELOW the orbit
              (§9.4 calls for an "explicit adjacent note") — an earlier
              revision placed all five lines inside and they visibly
              overlapped the arcs, which real browser evidence caught. */}
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
            <div className="flex w-[112px] flex-col items-center justify-center sm:w-[116px]">
              {centerValue ? (
                <>
                  <span className="font-mono text-[46px] font-semibold leading-none tracking-tight tabular-nums text-ink-primary">{centerValue}</span>
                  <span className="mt-1 text-[13px] leading-none text-ink-secondary">bpm</span>
                </>
              ) : (
                <span className="text-[16px] font-semibold leading-none tracking-tight text-ink-disabled">Unavailable</span>
              )}
            </div>
          </div>
        </div>

        {/* Adjacent identity / status / scope note (§9.4). */}
        <div className="flex flex-col items-center gap-0.5 text-center">
          {centerValue ? <span className="text-[13px] font-medium leading-snug text-ink-secondary">AI-estimated HR</span> : null}
          <span className="text-[12px] leading-snug text-ink-muted">{centerReason}</span>
          <span className="text-[12px] leading-snug text-ink-disabled">Not model confidence</span>
        </div>

        {/* §9.5 — four-row legend with matching line swatches. Replaces the
            unreadable in-ring micro-text removed at d49c3a2. */}
        <ul className="flex w-full flex-col gap-0.5">
          {rings.map((ring, i) => {
            const stage = STAGE_KEYS[i]!;
            const treatment = INTEGRITY_STATE_TREATMENT[ring.state];
            const color = resolveRingStroke(stage, ring.state);
            return (
              <li key={ring.key} className="flex min-h-[36px] items-center justify-between gap-3 border-b border-jury-border-subtle/50 py-1 last:border-b-0">
                <span className="flex items-center gap-2.5">
                  <svg width={22} height={10} aria-hidden="true" focusable="false" className="shrink-0">
                    <line
                      x1={1}
                      y1={5}
                      x2={21}
                      y2={5}
                      stroke={color}
                      strokeWidth={4}
                      strokeDasharray={treatment.dash}
                      strokeLinecap={treatment.roundCap ? "round" : "butt"}
                      opacity={treatment.opacity}
                    />
                  </svg>
                  <span className="text-[13px] font-medium text-ink-primary">{RING_LABEL[stage]}</span>
                </span>
                <span className="text-right text-[12px] leading-snug text-ink-secondary">{treatment.word}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
