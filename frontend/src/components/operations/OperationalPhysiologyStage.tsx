"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { buildSensorAnchors } from "@/components/visualization/human/humanLayout";
import { MODALITY_COLOR, type FinalModality } from "@/lib/architecture";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";
import { useOperationalEventStore } from "@/store/operationalEventStore";

const PhysiologyAvatar3D = dynamic(() => import("@/components/visualization/human/PhysiologyAvatar3D").then((m) => m.PhysiologyAvatar3D), {
  ssr: false,
  loading: () => <div className="flex h-full min-h-[300px] items-center justify-center text-xs text-ink-muted">Loading physiology stage…</div>,
});

const PRIORITY_MODALITIES: FinalModality[] = ["PPG", "IMU", "ECG"];

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(query.matches);
    const listener = (event: MediaQueryListEvent) => setReduced(event.matches);
    query.addEventListener("change", listener);
    return () => query.removeEventListener("change", listener);
  }, []);
  return reduced;
}

/**
 * Integrated operational physiology surface for `/mission-overview` (master
 * prompt 3A §9, recomposed 3C §7) — replaces the flat SVG `CrewPhysiologyMap`.
 * Combines the volumetric avatar, selected-sensor detail, a compact per-
 * channel state summary for PPG/IMU/ECG (no waveform plots — those live once
 * in the Section 02 synchronized signal scope), and a 3-event ticker, all
 * driven by the one shared operational view model.
 */
export function OperationalPhysiologyStage({ selected: selectedProp, onSelectModality }: { selected?: FinalModality; onSelectModality?: (m: FinalModality) => void } = {}) {
  const view = useOperationalViewModel();
  const events = useOperationalEventStore((state) => state.events);
  const reducedMotion = usePrefersReducedMotion();
  // Prompt 3B §16 — the selected modality may be lifted to a single shared
  // page-level state so the figure, pentagon, ribbon matrix and sensor detail
  // all highlight the same modality. When no controlled prop is supplied this
  // component keeps owning the selection (its standalone/original behaviour).
  const [internalSelected, setInternalSelected] = useState<FinalModality>("PPG");
  const selected = selectedProp ?? internalSelected;
  const setSelected = onSelectModality ?? setInternalSelected;

  const anchors = useMemo(
    () =>
      buildSensorAnchors(
        view.modalities.map((entry) => ({
          modality: entry.modality,
          region: entry.region,
          nodeState: entry.nodeState,
          stateLabel: entry.stateLabel,
          statusLabel: entry.observation.statusLabel,
        })),
        selected,
      ),
    [view.modalities, selected],
  );

  const selectedEntry = view.modalities.find((entry) => entry.modality === selected) ?? view.modalities[0]!;
  const recentEvents = events.slice(-3).reverse();

  return (
    <section aria-labelledby="physiology-stage-heading" className="flex h-full flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="physiology-stage-heading" className="text-sm font-semibold text-ink-primary">
          Sensing system stage
        </h2>
        <span className="text-[11px] uppercase tracking-wide text-ink-muted">CORE_PLUS_CONTEXT · 5 MODALITIES</span>
      </div>

      {/* Prompt 3A.2 §5.2/§6 — the avatar column is widened (64/36) so the
          operational-avatar cell is wide enough (~395px at 1440) to host the
          side-by-side figure + module rail at a properly-sized figure, rather
          than collapsing to the narrow stacked-grid fallback. */}
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[64%_36%]">
        <div className="min-h-[300px] overflow-hidden rounded-[8px] border border-jury-border-subtle bg-surface-2">
          <PhysiologyAvatar3D mode="operational" anchors={anchors} reducedMotion={reducedMotion} onSelectModality={setSelected} />
        </div>

        <div className="flex min-h-0 flex-col gap-3">
          <div className="flex flex-col gap-1 rounded-[8px] border border-jury-border-subtle bg-surface-2 p-3 text-xs">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-semibold text-ink-primary">
                {selectedEntry.modality} <span className="font-normal text-ink-muted">— {selectedEntry.region}</span>
              </span>
              <span className="rounded-[4px] border border-jury-border-subtle px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-ink-secondary">
                {selectedEntry.stateLabel}
              </span>
            </div>
            {/* Prompt 3A.1 §6 — the exact required per-state sentence lives in
                `unavailableReason` (set by applyTelemetryGate/applyFaultOverride
                for every non-active state); `statusLabel` alone is used only
                for the genuinely-active/dataset-scoped cases where no
                gate/fault override applies. */}
            <p className="text-ink-secondary">{selectedEntry.observation.unavailableReason ?? selectedEntry.observation.statusLabel}</p>
          </div>

          {/* §7 — the Command Deck states each channel's category and current
              sample-window metadata; it does not repeat the full waveform
              plots, which live once in the Section 02 synchronized scope. */}
          <div className="flex flex-1 flex-col gap-1.5 overflow-y-auto">
            {PRIORITY_MODALITIES.map((modality) => {
              const entry = view.modalities.find((item) => item.modality === modality)!;
              const sentence = entry.observation.unavailableReason ?? entry.observation.statusLabel;
              return (
                <div key={modality} className="flex items-start gap-2 rounded-[6px] border border-jury-border-subtle bg-surface-2 px-2.5 py-1.5">
                  <span aria-hidden="true" className="mt-1 h-0.5 w-4 shrink-0 rounded-full" style={{ backgroundColor: MODALITY_COLOR[modality] }} />
                  <div className="flex min-w-0 flex-col gap-0.5">
                    <div className="flex flex-wrap items-baseline gap-x-1.5">
                      <span className="text-[11px] font-semibold text-ink-primary">{modality}</span>
                      <span className="text-[10px] text-ink-muted">{entry.observation.channelName ?? "—"}</span>
                      {entry.plot?.sampleRateHz ? (
                        <span className="font-mono text-[9.5px] text-ink-muted">{entry.plot.sampleRateHz} Hz</span>
                      ) : null}
                    </div>
                    <p className="text-[10.5px] leading-snug text-ink-secondary">{sentence}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 border-t border-jury-border-subtle pt-2 text-[11px]">
        <span className="shrink-0 font-semibold uppercase tracking-wide text-ink-muted">Recent</span>
        {recentEvents.length === 0 ? (
          <span className="text-ink-muted">No session events yet.</span>
        ) : (
          recentEvents.map((event) => (
            <span key={event.id} className="rounded-[4px] border border-jury-border-subtle bg-surface-2 px-2 py-0.5 text-ink-secondary">
              {event.label}
              {event.modality ? ` — ${event.modality}` : ""}
            </span>
          ))
        )}
        <Link href="/live-monitoring" className="ml-auto flex shrink-0 items-center gap-1 text-information underline underline-offset-2">
          View all session events <ArrowUpRight size={10} aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}
