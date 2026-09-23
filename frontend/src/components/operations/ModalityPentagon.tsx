"use client";

import { MODALITY_COLOR, type FinalModality } from "@/lib/architecture";
import { round2 } from "@/lib/format";
import { useOperationalViewModel, type ModalityNodeState } from "@/lib/monitoring/operationalViewModel";

const SIZE = 252;
const CENTER = SIZE / 2;
const RADIUS = 90;

// Anatomical placement (§9): EEG upper-left, EOG upper-right, ECG right,
// PPG left/lower-left, IMU bottom. Angles are standard math degrees (0 = right,
// CCW); SVG y is flipped below.
const VERTEX: { modality: FinalModality; angle: number }[] = [
  { modality: "EEG", angle: 126 },
  { modality: "EOG", angle: 54 },
  { modality: "ECG", angle: 342 },
  { modality: "IMU", angle: 270 },
  { modality: "PPG", angle: 198 },
];
// Perimeter order for the pentagon frame.
const PERIMETER: FinalModality[] = ["EEG", "EOG", "ECG", "IMU", "PPG"];

function pos(angleDeg: number, r: number): { x: number; y: number } {
  const a = (angleDeg * Math.PI) / 180;
  return { x: round2(CENTER + Math.cos(a) * r), y: round2(CENTER - Math.sin(a) * r) };
}

function nodeColor(state: ModalityNodeState, base: string): string {
  if (state === "fault") return "#D46F70";
  if (state === "disconnected" || state === "unavailable" || state === "source_error") return "#516269";
  if (state === "warmup" || state === "awaiting_confirmation") return "#D5A45E";
  return base;
}

function shortState(label: string): string {
  if (label === "No channel in current source") return "No channel";
  if (label === "Connected — awaiting confirmed frame") return "Awaiting";
  return label;
}

/**
 * Prompt 3B §9 — Five-Modality Pentagon. The five final-architecture
 * modalities as ONE connected sensing topology, in anatomical order, with
 * module braces (frontal EEG+EOG, wrist PPG+IMU, chest ECG). It is topology,
 * NOT a score: no filled radar polygon, no aggregate health shape. Vertices
 * are real focusable buttons that drive the shared selected modality.
 */
export function ModalityPentagon({ selected, onSelect }: { selected: FinalModality; onSelect: (m: FinalModality) => void }) {
  const view = useOperationalViewModel();
  const byModality = (m: FinalModality) => view.modalities.find((x) => x.modality === m)!;

  const eeg = pos(126, RADIUS);
  const eog = pos(54, RADIUS);
  const ppg = pos(198, RADIUS);
  const imu = pos(270, RADIUS);
  const frontalMid = pos(90, RADIUS + 14);
  const wristMid = pos(234, RADIUS + 14);
  // §12 — CHEST previously sat directly beneath the ECG vertex's own state
  // label (a literal text-on-text collision). Chest has only one member
  // (ECG), so there is no natural brace midpoint; instead the label is
  // placed outside the polygon at the angle bisecting IMU→ECG, mirroring how
  // FRONTAL/WRIST sit outside their own two-vertex arcs, well clear of the
  // ECG vertex's own dot/name/state-label column.
  const chestMid = pos((270 + 342) / 2, RADIUS + 14);

  return (
    <section aria-labelledby="pentagon-heading" className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="pentagon-heading" className="text-sm font-semibold text-ink-primary">
          Sensing topology
        </h2>
        <span className="text-[10px] uppercase tracking-wide text-ink-muted">CORE_PLUS_CONTEXT</span>
      </div>

      <div className="relative mx-auto" style={{ width: SIZE, height: SIZE }}>
        <svg width={SIZE} height={SIZE} className="absolute inset-0" aria-hidden="true">
          {/* Pentagon frame (topology, not a filled radar). */}
          <polygon
            points={PERIMETER.map((m) => {
              const v = VERTEX.find((x) => x.modality === m)!;
              const p = pos(v.angle, RADIUS);
              return `${p.x},${p.y}`;
            }).join(" ")}
            fill="none"
            stroke="#203239"
            strokeWidth={1.2}
          />
          {/* Module braces. */}
          <path d={`M${eeg.x},${eeg.y} Q${frontalMid.x},${frontalMid.y} ${eog.x},${eog.y}`} fill="none" stroke="#45D6E5" strokeWidth={1.6} opacity={0.5} />
          <path d={`M${ppg.x},${ppg.y} Q${wristMid.x},${wristMid.y} ${imu.x},${imu.y}`} fill="none" stroke="#45D6E5" strokeWidth={1.6} opacity={0.5} />
          {/* Spokes to centre. */}
          {VERTEX.map((v) => {
            const p = pos(v.angle, RADIUS);
            return <line key={v.modality} x1={CENTER} y1={CENTER} x2={p.x} y2={p.y} stroke="#152128" strokeWidth={1} />;
          })}
          <text x={frontalMid.x} y={frontalMid.y - 8} textAnchor="middle" fontSize={10} fontWeight={700} fill="#63BFB7" opacity={0.85}>FRONTAL</text>
          <text x={wristMid.x} y={wristMid.y + 14} textAnchor="middle" fontSize={10} fontWeight={700} fill="#63BFB7" opacity={0.85}>WRIST</text>
          <text x={chestMid.x} y={chestMid.y + 2} textAnchor="middle" fontSize={10} fontWeight={700} fill="#63BFB7" opacity={0.85}>CHEST</text>
        </svg>

        {/* Centre summary. */}
        <div className="absolute left-1/2 top-1/2 flex h-[72px] w-[72px] -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center gap-0.5 rounded-full border border-jury-border-strong bg-surface-2 text-center">
          <span className="text-[9.5px] font-semibold uppercase tracking-wide text-ink-muted">{view.isReplay ? "Replay" : "Synthetic"}</span>
          <span className={view.connected ? "text-[11px] font-semibold text-jury-success" : "text-[11px] font-semibold text-jury-fault"}>{view.connected ? "Connected" : "Down"}</span>
          <span className="font-mono text-[10px] text-ink-muted">{view.confirmedModalityCount}/{view.totalModalityCount}</span>
        </div>

        {/* Vertex buttons. */}
        {VERTEX.map((v) => {
          const entry = byModality(v.modality);
          const p = pos(v.angle, RADIUS);
          const color = nodeColor(entry.nodeState, MODALITY_COLOR[v.modality]);
          const isSel = selected === v.modality;
          return (
            <button
              key={v.modality}
              type="button"
              onClick={() => onSelect(v.modality)}
              aria-pressed={isSel}
              aria-label={`${v.modality} — ${entry.region} — ${entry.stateLabel}`}
              className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-0.5 rounded-[6px] px-1 py-0.5 outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
              style={{ left: p.x, top: p.y, background: isSel ? "rgba(69,214,229,0.14)" : "transparent", boxShadow: isSel ? "0 0 0 1.5px rgba(69,214,229,0.6)" : "none" }}
            >
              <span aria-hidden="true" className="flex h-4 w-4 items-center justify-center rounded-full border-2" style={{ borderColor: color, background: entry.nodeState === "confirmed" ? `${color}33` : "transparent" }} />
              <span className="text-[11px] font-bold leading-none text-ink-primary">{v.modality}</span>
              <span className="text-[10px] leading-none text-ink-muted">{shortState(entry.stateLabel)}</span>
            </button>
          );
        })}
      </div>

      {/* §12/§17 — separates final-architecture membership from what the
          current source actually carries, instead of the old ambiguous
          "N of 5 currently confirmed" (which read as if only N of 5 belong
          to the final architecture). */}
      <p className="text-center text-[11px] font-semibold text-ink-secondary">
        {view.isReplay
          ? `${view.confirmedModalityCount} replay-observable channel${view.confirmedModalityCount === 1 ? "" : "s"} · ${view.totalModalityCount} final modalities`
          : `${view.confirmedModalityCount} of ${view.totalModalityCount} confirmed in this synthetic session`}
      </p>
      {view.isReplay && view.confirmedModalityCount < view.totalModalityCount ? (
        <p className="text-center text-[10px] leading-snug text-ink-muted">
          EEG and EOG are retained in the final architecture; this replay carries no EEG/EOG channel.
        </p>
      ) : null}
    </section>
  );
}
