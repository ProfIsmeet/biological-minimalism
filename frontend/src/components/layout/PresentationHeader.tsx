"use client";

import clsx from "clsx";
import { Wifi, WifiOff } from "lucide-react";

import { deriveConnectionLabel, deriveSourceLabel } from "@/lib/sourceLabel";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

interface PresentationHeaderProps {
  variant: "final" | "experimental";
}

// Master-prompt corrective pass §2 — minimal presentation header for the
// jury (final) and Experimental Research routes. Deliberately excludes
// mission day, mission clock, AI-confidence badge, the "Mission Control"
// label, backdrop blur, and cyan glow — none of which belong on either demo
// destination. Source scope always comes from the shared
// deriveSourceLabel/deriveConnectionLabel helpers, so synthetic data is
// never labeled "Live" here either.
export function PresentationHeader({ variant }: PresentationHeaderProps) {
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  const isReplay = useDatasetReplayMode();
  const sourceLabel = deriveSourceLabel({ connectionStatus, isReplay });
  const connectionLabel = deriveConnectionLabel(connectionStatus);
  const accent = variant === "final" ? "text-final-accent" : "text-experimental";

  return (
    <header className="flex items-center justify-between gap-4 border-b border-jury-border-subtle bg-canvas px-4 py-3 sm:px-6">
      <div className="flex items-center gap-3">
        <p className="text-sm font-semibold text-ink-primary">Biological Minimalism</p>
        <span className="hidden text-jury-border-strong sm:inline">/</span>
        <span className={clsx("hidden text-[11px] font-semibold uppercase tracking-[0.1em] sm:inline", accent)}>
          {variant === "final" ? "Final System" : "Experimental Research"}
        </span>
      </div>

      <div className="flex items-center gap-3 sm:gap-4">
        <span className="hidden text-xs uppercase tracking-wider text-ink-muted sm:inline">{sourceLabel}</span>
        <span
          className={clsx(
            "flex items-center gap-1.5 rounded-[4px] border px-2.5 py-1 text-[11px] font-medium uppercase tracking-wide",
            connectionStatus === "open"
              ? "border-jury-success/30 bg-jury-success-soft text-jury-success"
              : "border-jury-warning/30 bg-jury-warning-soft text-jury-warning",
          )}
        >
          {connectionStatus === "open" ? <Wifi size={12} aria-hidden="true" /> : <WifiOff size={12} aria-hidden="true" />}
          {connectionLabel}
        </span>
      </div>
    </header>
  );
}
