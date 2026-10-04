"use client";

import { MODALITY_COLOR } from "@/lib/architecture";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";

/**
 * A one-line "which simulated-fault region is affected right now" readout,
 * independent of the full 3D physiology stage.
 * Exists specifically so mobile (390px) and tablet (1024px) first viewports
 * can satisfy the "affected modality/body region" contract without requiring
 * the full-height avatar render to be scrolled into view first — the avatar
 * remains the detailed, secondary presentation; this is the fast-glance one.
 * Reads the same shared view model every other operational component reads;
 * never invents a region or severity that is not already derived elsewhere.
 */
export function AffectedRegionSummary() {
  const view = useOperationalViewModel();

  if (view.telemetryAvailability !== "active") {
    return (
      <div className="flex items-center gap-2 rounded-[8px] border border-jury-border-subtle bg-surface-1 px-3.5 py-2.5 text-sm text-ink-muted">
        <span aria-hidden="true" className="h-2 w-2 shrink-0 rounded-full bg-ink-disabled" />
        Affected region unavailable — {view.telemetryAvailability === "disconnected" ? "source disconnected" : view.telemetryAvailability === "source_error" ? "source error" : "awaiting confirmed frame"}
      </div>
    );
  }

  const faulted = view.modalities.find((entry) => entry.nodeState === "fault");
  const unconfirmed = view.modalities.find((entry) => entry.nodeState !== "confirmed" && entry.nodeState !== "fault" && entry.observation.channelName);

  if (faulted) {
    return (
      <div className="flex items-center gap-2 rounded-[8px] border border-jury-fault/40 bg-jury-fault-soft px-3.5 py-2.5 text-sm">
        <span aria-hidden="true" className="h-2 w-2 shrink-0 rounded-full bg-jury-fault" />
        <span className="font-semibold text-jury-fault">Affected: {faulted.region}</span>
        <span className="text-ink-secondary">
          — <span style={{ color: MODALITY_COLOR[faulted.modality] }}>{faulted.modality}</span> simulated fault
        </span>
      </div>
    );
  }

  if (unconfirmed) {
    return (
      <div className="flex items-center gap-2 rounded-[8px] border border-jury-border-subtle bg-surface-1 px-3.5 py-2.5 text-sm">
        <span aria-hidden="true" className="h-2 w-2 shrink-0 rounded-full bg-ink-disabled" />
        <span className="font-semibold text-ink-primary">{unconfirmed.region}</span>
        <span className="text-ink-secondary">
          — <span style={{ color: MODALITY_COLOR[unconfirmed.modality] }}>{unconfirmed.modality}</span> not confirmed
        </span>
      </div>
    );
  }

  const confirmedRegions = Array.from(new Set(view.modalities.filter((entry) => entry.nodeState === "confirmed").map((entry) => entry.region)));

  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 rounded-[8px] border border-jury-border-subtle bg-surface-1 px-3.5 py-2.5 text-sm">
      <span aria-hidden="true" className="h-2 w-2 shrink-0 rounded-full bg-final-accent" />
      <span className="font-semibold text-ink-primary">No active simulated-fault region</span>
      <span className="text-ink-secondary">
        — {confirmedRegions.length > 0
          ? `${view.isReplay ? "confirmed replay inputs" : "confirmed synthetic inputs"}: ${confirmedRegions.join(", ")}`
          : `no ${view.isReplay ? "replay" : "synthetic"} input region currently confirmed`}
      </span>
    </div>
  );
}
