"use client";

import { ChevronDown } from "lucide-react";

import { FaultRecoverySpine } from "@/components/operations/FaultRecoverySpine";
import { HRInferenceCore } from "@/components/operations/HRInferenceCore";
import { InferenceHexFlow } from "@/components/operations/InferenceHexFlow";
import { InferenceIntegrityOrbit } from "@/components/operations/InferenceIntegrityOrbit";
import { MissionStatusBar } from "@/components/operations/MissionStatusBar";
import { ModalityPentagon } from "@/components/operations/ModalityPentagon";
import { OperationalEventRail } from "@/components/operations/OperationalEventRail";
import { OperationalPhysiologyStage } from "@/components/operations/OperationalPhysiologyStage";
import { OperationalProvenanceChain } from "@/components/operations/OperationalProvenanceChain";
import { RecentHrEstimateTrend } from "@/components/operations/RecentHrEstimateTrend";
import { SignalRibbonMatrix } from "@/components/operations/SignalRibbonMatrix";
import { ScopeProvenanceFooter } from "@/components/monitoring/ScopeProvenanceFooter";
import { useMissionUiStore } from "@/store/missionUiStore";

function SectionHeader({ index, kicker, title, blurb }: { index: string; kicker: string; title: string; blurb: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-information">
        {index} · {kicker}
      </span>
      <h2 className="text-[19px] font-semibold leading-tight tracking-[-0.02em] text-ink-primary sm:text-[22px]">{title}</h2>
      <p className="max-w-2xl text-sm leading-relaxed text-ink-secondary">{blurb}</p>
    </div>
  );
}

/**
 * Prompt 3B §5/§13 — the operational mission narrative as one genuinely
 * scrollable document, not a fixed dashboard. Five stacked sections carry the
 * viewer from the live command deck, down the signal path, through inference
 * integrity, into fault/recovery, and out to the honest operational boundary.
 *
 * §16 — the selected modality is a single page-level state so the holographic
 * figure, the pentagon, and the ribbon matrix all highlight the same modality.
 */
export function MissionOverviewExperience() {
  // Prompt-4 §22 — the selected modality lives in a UI store so the demo reset
  // (fired from the DemoControlDrawer) can return it to PPG. Behaviour is
  // otherwise identical to the previous page-level useState.
  const selected = useMissionUiStore((state) => state.selectedModality);
  const setSelected = useMissionUiStore((state) => state.setSelectedModality);

  return (
    <div className="mx-auto flex min-w-0 max-w-[1480px] flex-col gap-12 overflow-x-hidden px-0 py-2 sm:gap-16">
      <h1 className="sr-only">Mission overview — operational sensing narrative</h1>

      {/* Section 1 — Command Deck. */}
      <section aria-labelledby="sec-command-deck" className="flex flex-col gap-4">
        <div id="sec-command-deck">
          <SectionHeader
            index="01"
            kicker="Command Deck"
            title="Live operational sensing status"
            blurb="The confirmed state of the CORE_PLUS_CONTEXT sensing system right now — source identity, per-modality confirmation, and the current heart-rate inference, all from one shared telemetry gate."
          />
        </div>
        <MissionStatusBar />
        {/* §6 — the outer command-hero grid now splits at `xl` (>=1280px)
            into an 8/4 column ratio, one breakpoint level ABOVE
            OperationalPhysiologyStage's own internal `lg` (>=1024px) avatar/
            detail split. The previous shared `lg` breakpoint on both grids
            caused a double split in the 1024-1279px tablet band (stage,
            detail rail, AND HR card all fighting for width at once); now the
            tablet band gives the stage the full row so its own internal
            split has real room, and only >=1280px introduces the secondary
            column. */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,8fr)_minmax(300px,4fr)]">
          <OperationalPhysiologyStage selected={selected} onSelectModality={setSelected} />
          <div className="flex flex-col gap-4">
            <HRInferenceCore />
            <RecentHrEstimateTrend />
          </div>
        </div>

        {/* Scroll cue (§5). */}
        <a
          href="#sec-signal-geometry"
          className="mx-auto mt-2 flex flex-col items-center gap-1 rounded-full px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-muted outline-none transition-colors hover:text-information focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
        >
          Scroll for signal path &amp; fault response
          <ChevronDown size={16} aria-hidden="true" className="motion-safe:animate-bounce" />
        </a>
      </section>

      {/* Section 2 — Signal Geometry. */}
      <section aria-labelledby="sec-signal-geometry" className="flex flex-col gap-4">
        <div id="sec-signal-geometry">
          <SectionHeader
            index="02"
            kicker="Signal Geometry"
            title="Architecture coverage and synchronized signal streams"
            blurb="The final five-modality architecture is shown alongside the channels observable in the current source. EEG and EOG remain part of the final architecture but are never synthesised when the replay does not carry them."
          />
        </div>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
          <SignalRibbonMatrix selected={selected} onSelect={setSelected} />
          <ModalityPentagon selected={selected} onSelect={setSelected} />
        </div>
      </section>

      {/* Section 3 — Inference Integrity. */}
      <section aria-labelledby="sec-inference-integrity" className="flex flex-col gap-4">
        <div id="sec-inference-integrity">
          <SectionHeader
            index="03"
            kicker="Inference Integrity"
            title="How the heart-rate output is assembled"
            blurb="The categorical integrity of the signal path — not a confidence score. Both PPG and IMU must be confirmed and windowed before the model can produce a heart-rate output."
          />
        </div>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <InferenceIntegrityOrbit />
          <InferenceHexFlow />
        </div>
      </section>

      {/* Section 4 — Fault & Recovery. */}
      <section aria-labelledby="sec-fault-recovery" className="flex flex-col gap-4">
        <div id="sec-fault-recovery">
          <SectionHeader
            index="04"
            kicker="Fault & Recovery"
            title="What happens when an input degrades"
            blurb="Simulated faults localise to their input, suppress the affected waveform, and hold back the heart-rate output until recovery — traced here from this session's own recorded events."
          />
        </div>
        <FaultRecoverySpine />
        <OperationalEventRail />
      </section>

      {/* Section 5 — Operational Boundary. */}
      <section aria-labelledby="sec-operational-boundary" className="flex flex-col gap-4">
        <div id="sec-operational-boundary">
          <SectionHeader
            index="05"
            kicker="Operational Boundary"
            title="What this demonstrator does and does not claim"
            blurb="The honest edge of the system: the final architecture, the replay-only scope of heart-rate inference, and what remains untrained or out of scope."
          />
        </div>
        <OperationalProvenanceChain />
        <ScopeProvenanceFooter />
      </section>
    </div>
  );
}
