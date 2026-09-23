"use client";

import { CANDIDATE_DISPOSITION_DISPLAY, FINAL_ARCHITECTURE_ID } from "@/lib/architecture";
import { round2 } from "@/lib/format";
import { useResearchStore } from "@/store/researchStore";

const SIZE = 300;
const CENTER = SIZE / 2;
const CANDIDATE_RADIUS = 118;
const CENTER_RING_RADIUS = 44;

/**
 * Candidate-sensor disposition geometry for `/research/experimental` (master
 * prompt 3 §28). The final architecture sits in a small central reference
 * ring; every candidate sits outside it on a thin spoke. This communicates
 * "investigated, evaluated, not carried forward" — not "broken" or
 * "unsafe" — so candidates use experimental ochre, never final-system teal
 * or fault red.
 */
export function ExperimentalDispositionOrbit() {
  const architecture = useResearchStore((store) => store.finalWearableArchitecture);
  const entries = architecture ? Object.entries(architecture.exclusion_rationale) : [];
  if (entries.length === 0) return null;

  const angleStep = 360 / entries.length;

  return (
    <div className="flex flex-col items-center gap-4 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-6 sm:flex-row sm:items-start sm:gap-8">
      <svg width={SIZE} height={SIZE} role="img" aria-label="Candidate sensors evaluated around the final CORE_PLUS_CONTEXT architecture reference ring, none carried into the final architecture">
        {entries.map(([key], index) => {
          const angleRad = ((index * angleStep - 90) * Math.PI) / 180;
          const x = round2(CENTER + CANDIDATE_RADIUS * Math.cos(angleRad));
          const y = round2(CENTER + CANDIDATE_RADIUS * Math.sin(angleRad));
          return <line key={key} x1={CENTER} y1={CENTER} x2={x} y2={y} stroke="#203239" strokeWidth={1} />;
        })}

        <circle cx={CENTER} cy={CENTER} r={CENTER_RING_RADIUS} fill="rgba(105,183,173,0.08)" stroke="#69B7AD" strokeWidth={1.5} />
        <text x={CENTER} y={CENTER - 2} textAnchor="middle" fontSize={10} fontWeight={700} fill="#69B7AD">
          {FINAL_ARCHITECTURE_ID}
        </text>
        <text x={CENTER} y={CENTER + 12} textAnchor="middle" fontSize={8} fill="#B6C4C9">
          Final architecture
        </text>

        {entries.map(([key], index) => {
          const angleRad = ((index * angleStep - 90) * Math.PI) / 180;
          const x = round2(CENTER + CANDIDATE_RADIUS * Math.cos(angleRad));
          const y = round2(CENTER + CANDIDATE_RADIUS * Math.sin(angleRad));
          const display = CANDIDATE_DISPOSITION_DISPLAY[key];
          return (
            <g key={key}>
              <circle cx={x} cy={y} r={20} fill="rgba(199,154,91,0.1)" stroke="#C79A5B" strokeWidth={1.25} />
              <text x={x} y={y + 3} textAnchor="middle" fontSize={8} fontWeight={600} fill="#C79A5B">
                {(display?.label ?? key).split(" ")[0]}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="flex flex-col gap-2">
        <p className="text-xs leading-relaxed text-ink-secondary">
          Candidates outside the reference ring were investigated and evaluated but not carried into the final
          CORE_PLUS_CONTEXT architecture. This does not mean unsafe, broken, or scientifically useless — see each
          candidate&rsquo;s evidence below.
        </p>
        <ul className="flex flex-col gap-1.5 text-[11px] text-ink-muted">
          {entries.map(([key]) => {
            const display = CANDIDATE_DISPOSITION_DISPLAY[key];
            return (
              <li key={key} className="flex items-center gap-1.5">
                <span aria-hidden="true" className="h-1.5 w-1.5 shrink-0 rounded-full bg-experimental" />
                <span className="font-medium text-ink-secondary">{display?.label ?? key.replace(/_/g, " ")}</span>
                <span>— {display?.region ?? "Not specified"}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
