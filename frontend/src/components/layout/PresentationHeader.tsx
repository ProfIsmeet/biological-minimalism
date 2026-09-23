"use client";

import clsx from "clsx";
import { Wifi, WifiOff } from "lucide-react";

import { deriveConnectionLabel, deriveSourceLabel } from "@/lib/sourceLabel";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

interface PresentationHeaderProps {
  variant: "final" | "monitoring" | "system" | "experimental" | "reference";
}

const VARIANT_LABEL: Record<PresentationHeaderProps["variant"], string> = {
  final: "Mission Overview",
  monitoring: "Live Signals",
  system: "System Brief",
  experimental: "Experimental Research",
  reference: "Digital Twin Reference",
};

const VARIANT_ACCENT: Record<PresentationHeaderProps["variant"], string> = {
  final: "text-final-accent",
  monitoring: "text-final-accent",
  system: "text-information",
  experimental: "text-experimental",
  reference: "text-ink-muted",
};

/**
 * §18 — static/reference routes describe what the route IS, not the current
 * transport state. Showing "RECORDED REPLAY"/"CONNECTED" on `/digital-twin`
 * (a conceptual, untrained, unvalidated illustration that never calls the
 * backend) or on `/system-brief` (the final architecture document) falsely
 * implied those pages were live telemetry surfaces. Only the two genuinely
 * operational variants — final (/mission-overview) and monitoring
 * (/live-monitoring) — read real connection/source state.
 */
const STATIC_SCOPE_BADGE: Partial<Record<PresentationHeaderProps["variant"], { primary: string; secondary?: string }>> = {
  reference: { primary: "CONCEPTUAL REFERENCE", secondary: "UNTRAINED · UNVALIDATED" },
  system: { primary: "FINAL ARCHITECTURE" },
  experimental: { primary: "RESEARCH EVIDENCE" },
};

// Master-prompt 3 §6.3 — minimal presentation header shared by all five
// routes. Deliberately excludes mission day, mission clock, AI-confidence
// badge, the "Mission Control" label, backdrop blur, and cyan glow — none of
// which belong on any of the demo destinations. Source scope for the two
// operational variants always comes from the shared deriveSourceLabel/
// deriveConnectionLabel helpers, so synthetic data is never labeled "Live"
// here either.
export function PresentationHeader({ variant }: PresentationHeaderProps) {
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  const isReplay = useDatasetReplayMode();
  const sourceLabel = deriveSourceLabel({ connectionStatus, isReplay });
  const connectionLabel = deriveConnectionLabel(connectionStatus);
  const accent = VARIANT_ACCENT[variant];
  const staticScope = STATIC_SCOPE_BADGE[variant];

  return (
    <header className="flex h-14 items-center justify-between gap-4 border-b border-jury-border-subtle bg-canvas px-4 sm:px-6">
      <div className="flex items-center gap-3">
        <p className="text-sm font-semibold text-ink-primary">Biological Minimalism</p>
        <span className="hidden text-jury-border-strong sm:inline">/</span>
        <span className={clsx("hidden text-[11px] font-semibold uppercase tracking-[0.1em] sm:inline", accent)}>
          {VARIANT_LABEL[variant]}
        </span>
      </div>

      {staticScope ? (
        <div className="flex items-center gap-2">
          <span className="rounded-[4px] border border-jury-warning/30 bg-jury-warning-soft px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-jury-warning">
            {staticScope.primary}
          </span>
          {staticScope.secondary ? (
            <span className="hidden text-[10px] uppercase tracking-wider text-ink-muted sm:inline">{staticScope.secondary}</span>
          ) : null}
        </div>
      ) : (
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
      )}
    </header>
  );
}
