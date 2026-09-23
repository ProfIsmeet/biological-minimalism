"use client";

import Link from "next/link";

import { deriveSourceLabel } from "@/lib/sourceLabel";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

// Master-prompt §7.2 — exact required hero copy. No astronaut/twin/gauge
// imagery, no BioZ, no adaptation score — text and three scope labels only.
export function JuryHero() {
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  const isReplay = useDatasetReplayMode();
  const sourceLabel = deriveSourceLabel({ connectionStatus, isReplay });

  return (
    <header className="flex flex-col gap-5 border-b border-jury-border-subtle pb-8">
      <div className="flex items-center gap-2 text-final-accent">
        <span className="text-[11px] font-semibold uppercase tracking-[0.1em]">Biological Minimalism / Final System</span>
      </div>

      <h1 className="max-w-[760px] text-[38px] font-semibold leading-[1.06] tracking-[-0.04em] text-ink-primary sm:text-[46px] sm:leading-[1.04] lg:text-[56px] lg:leading-[1.02] lg:tracking-[-0.045em]">
        Three body regions. Five sensing modalities. One fault-aware physiological layer.
      </h1>

      <p className="max-w-[720px] text-[17px] leading-[1.55] text-ink-secondary">
        CORE_PLUS_CONTEXT combines wrist PPG + IMU, chest ECG, and frontal EEG + EOG. EOG is the only addition beyond
        MINIMAL_CORE.
      </p>

      <div className="flex flex-wrap items-stretch gap-6 border-t border-jury-border-subtle pt-5 sm:gap-8">
        <div className="flex flex-col gap-0.5">
          <span className="font-mono text-[32px] font-medium leading-none tabular-nums text-ink-primary">03</span>
          <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-muted">Body regions</span>
        </div>
        <span aria-hidden="true" className="w-px self-stretch bg-jury-border-subtle" />
        <div className="flex flex-col gap-0.5">
          <span className="font-mono text-[32px] font-medium leading-none tabular-nums text-ink-primary">05</span>
          <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-muted">Modalities</span>
        </div>
        <span aria-hidden="true" className="w-px self-stretch bg-jury-border-subtle" />
        <div className="flex flex-col gap-0.5">
          <span className="font-mono text-[32px] font-medium leading-none tabular-nums text-final-accent">+01</span>
          <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-muted">EOG context</span>
        </div>
        <span aria-hidden="true" className="w-px self-stretch bg-jury-border-subtle" />
        <div className="flex flex-col gap-0.5">
          <span className="text-sm font-semibold text-information">{sourceLabel}</span>
          <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-muted">Current source</span>
        </div>
      </div>

      <div className="flex flex-col gap-3 pt-1 sm:flex-row">
        <Link
          href="/live-monitoring"
          className="flex h-[42px] items-center justify-center rounded-[7px] bg-final-accent px-4 text-sm font-semibold text-[#07100F] transition-colors duration-150 hover:bg-final-accent-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
        >
          Open live signals
        </Link>
        <Link
          href="/research/experimental"
          className="flex h-[42px] items-center justify-center rounded-[7px] border border-jury-border-strong px-4 text-sm font-semibold text-ink-secondary transition-colors duration-150 hover:bg-surface-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
        >
          View experimental evidence
        </Link>
      </div>
    </header>
  );
}
