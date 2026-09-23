"use client";

import { useMemo } from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { SignalLaneChart, type SignalLanePoint } from "@/components/operations/SignalLaneChart";
import { computeDynamicDomain, downsampleExtremaPreserving } from "@/lib/monitoring/waveformDisplay";
import { MODALITY_COLOR, type FinalModality } from "@/lib/architecture";
import { useOperationalViewModel, type OperationalModalityState } from "@/lib/monitoring/operationalViewModel";

const ROW_HEIGHT = 46;
const DISPLAY_POINT_BUDGET = 300;
const SYNC_ID = "signal-scope";

function buildLanePoints(entry: OperationalModalityState): { points: SignalLanePoint[]; domain: [number, number] | null; hasTiming: boolean } {
  const plot = entry.plot;
  if (!plot || !plot.values.length) return { points: [], domain: null, hasTiming: false };
  const hasTiming = plot.sampleRateHz != null && plot.sampleRateHz > 0 && plot.startTimestampSeconds != null;
  const { points: sampled } = downsampleExtremaPreserving(plot.values, DISPLAY_POINT_BUDGET);
  const points = sampled.map((p) => ({
    t: hasTiming ? plot.startTimestampSeconds! + p.index / plot.sampleRateHz! : p.index,
    value: p.value,
  }));
  return { points, domain: computeDynamicDomain(plot.values), hasTiming };
}

/**
 * A single plottable-channel lane: identity column, waveform (own y-domain,
 * shared x/time domain), and a real right-side numeric gutter — never text
 * absolutely overlaid on top of the trace (§11.2). When the modality is
 * faulted the waveform is suppressed and replaced with an explicit dashed
 * "withheld" lane rather than a blank or fabricated trace (§11.4).
 */
function SignalLane({ entry, sharedDomain }: { entry: OperationalModalityState; sharedDomain: [number, number] | null }) {
  const color = MODALITY_COLOR[entry.modality];
  const { points, domain } = useMemo(() => buildLanePoints(entry), [entry]);
  const isFaulted = entry.nodeState === "fault";

  return (
    <div className="grid grid-cols-[1fr_54px] items-center gap-2 border-b border-jury-border-subtle py-2 last:border-b-0 sm:grid-cols-[108px_1fr_54px]">
      <div className="hidden flex-col gap-0.5 sm:flex">
        <div className="flex items-center gap-1.5">
          <span aria-hidden="true" className="h-0.5 w-4 shrink-0 rounded-full" style={{ backgroundColor: color }} />
          <span className="text-[11px] font-semibold text-ink-primary">{entry.modality}</span>
        </div>
        <span className="text-[10px] text-ink-muted">{entry.region}</span>
        {entry.plot?.sampleRateHz ? <span className="font-mono text-[9.5px] text-ink-muted">{entry.plot.sampleRateHz} Hz</span> : null}
      </div>

      <div style={{ height: ROW_HEIGHT }} className="col-span-2 sm:col-span-1">
        {isFaulted ? (
          <div className="flex h-full items-center justify-center rounded-[4px] border border-dashed border-jury-fault/50 bg-jury-fault-soft/40 text-[10.5px] font-semibold uppercase tracking-wide text-jury-fault">
            Simulated fault — waveform withheld
          </div>
        ) : points.length && domain ? (
          <SignalLaneChart points={points} domain={domain} sharedDomain={sharedDomain} color={color} unit={entry.plot?.unit ?? null} syncId={SYNC_ID} />
        ) : (
          <p className="flex h-full items-center text-[11px] text-ink-muted">{entry.observation.unavailableReason ?? entry.observation.statusLabel}</p>
        )}
      </div>

      <div className="col-start-2 row-start-1 flex flex-col justify-between py-0.5 font-mono text-[10px] text-ink-muted sm:col-start-3">
        {domain && !isFaulted ? (
          <>
            <span>{domain[1].toFixed(1)}</span>
            <span>{domain[0].toFixed(1)}</span>
          </>
        ) : null}
      </div>

      <div className="col-span-2 flex items-center gap-1.5 text-[10px] text-ink-muted sm:hidden">
        <span aria-hidden="true" className="h-0.5 w-4 shrink-0 rounded-full" style={{ backgroundColor: color }} />
        <span className="font-semibold text-ink-primary">{entry.modality}</span>
        <span>{entry.region}</span>
      </div>
    </div>
  );
}

/** §11.3 — EEG/EOG are final-architecture lanes, never a fabricated flat line. */
function ArchitectureCoverageLane({ entry }: { entry: OperationalModalityState }) {
  const color = MODALITY_COLOR[entry.modality];
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-jury-border-subtle py-2.5 text-[11px] last:border-b-0">
      <span aria-hidden="true" className="h-0.5 w-4 shrink-0 rounded-full opacity-50" style={{ backgroundColor: color }} />
      <span className="font-semibold text-ink-primary">{entry.modality}</span>
      <span className="text-ink-muted">{entry.region}</span>
      <span className="text-ink-secondary">Final architecture modality · no waveform channel in current source</span>
    </div>
  );
}

const PLOTTABLE: FinalModality[] = ["PPG", "IMU", "ECG"];
const ARCHITECTURE_ONLY: FinalModality[] = ["EEG", "EOG"];

/**
 * Prompt 3C §11 — Synchronized signal scope. Replaces the 3B per-row
 * WaveformChart matrix (independent, unaligned time axes) with lanes that
 * share ONE time domain derived from the plots' own real sample rate/start
 * timestamp, a shared recharts `syncId` hover cursor, and a real right-side
 * numeric gutter instead of text overlaid on the trace. EEG/EOG are shown as
 * explicit architecture-coverage lanes, never a synthesized waveform.
 */
export function SignalRibbonMatrix({ selected, onSelect }: { selected: FinalModality; onSelect: (m: FinalModality) => void }) {
  const view = useOperationalViewModel();
  const plottable = PLOTTABLE.map((m) => view.modalities.find((e) => e.modality === m)!);
  const architectureOnly = ARCHITECTURE_ONLY.map((m) => view.modalities.find((e) => e.modality === m)!);

  const sharedDomain = useMemo<[number, number] | null>(() => {
    let min = Infinity;
    let max = -Infinity;
    for (const entry of plottable) {
      const plot = entry.plot;
      if (!plot || !plot.values.length || plot.sampleRateHz == null || plot.startTimestampSeconds == null) continue;
      const start = plot.startTimestampSeconds;
      const end = plot.endTimestampSeconds ?? start + plot.values.length / plot.sampleRateHz;
      if (start < min) min = start;
      if (end > max) max = end;
    }
    return Number.isFinite(min) && Number.isFinite(max) && max > min ? [min, max] : null;
  }, [plottable]);

  return (
    <section aria-labelledby="signal-scope-heading" className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="signal-scope-heading" className="text-sm font-semibold text-ink-primary">
          Synchronized signal scope
        </h2>
        <Link href="/live-monitoring" className="flex items-center gap-1 text-[11px] font-medium text-information underline underline-offset-2">
          Detailed workspace <ArrowUpRight size={11} aria-hidden="true" />
        </Link>
      </div>

      <div className="flex flex-col">
        {plottable.map((entry) => (
          <button
            key={entry.modality}
            type="button"
            onClick={() => onSelect(entry.modality)}
            aria-pressed={selected === entry.modality}
            aria-label={`${entry.modality} — ${entry.region} — ${entry.stateLabel}`}
            className={`block w-full text-left outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#A1D2CC] ${selected === entry.modality ? "bg-[rgba(69,214,229,0.05)]" : ""}`}
          >
            <SignalLane entry={entry} sharedDomain={sharedDomain} />
          </button>
        ))}
        {architectureOnly.map((entry) => (
          <ArchitectureCoverageLane key={entry.modality} entry={entry} />
        ))}
      </div>

      {sharedDomain ? (
        <div className="flex justify-between border-t border-jury-border-subtle pt-1.5 font-mono text-[10px] text-ink-disabled sm:pl-[120px]">
          <span>t={sharedDomain[0].toFixed(2)}s</span>
          <span>t={sharedDomain[1].toFixed(2)}s</span>
        </div>
      ) : null}

      <p className="text-[10px] leading-snug text-ink-muted">
        PPG, IMU and ECG share one real time axis drawn from the confirmed source&rsquo;s own sample rate and start time. EEG and EOG carry no
        waveform channel in this demonstrator and are never synthesised.
      </p>
    </section>
  );
}
