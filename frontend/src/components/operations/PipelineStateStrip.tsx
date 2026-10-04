"use client";

import { useState } from "react";

import { StatusPill } from "@/components/visualization/shared/ChartFrame";
import { deriveHexFlow, type HexNodeId, type HexNodeState } from "@/lib/monitoring/inferenceHexFlow";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";

const STATE_TONE: Record<HexNodeState, "nominal" | "warning" | "fault" | "muted"> = {
  confirmed: "nominal",
  awaiting: "warning",
  blocked: "muted",
  fault: "fault",
  unavailable: "muted",
  disconnected: "muted",
  source_error: "fault",
};

const NODE_DETAIL: Record<HexNodeId, string> = {
  source: "The active telemetry source — replay dataset/subject or the synthetic demo. Every downstream stage depends on this being confirmed.",
  ppgInput: "PPG channel confirmed and within the current inference window, or blocked/faulted/unavailable.",
  imuInput: "IMU channel confirmed and within the current inference window, or blocked/faulted/unavailable.",
  window: "Requires BOTH PPG and IMU confirmed before the model input window can assemble — one confirmed input alone is insufficient.",
  model: "The HR model runs only once the window is ready; a blocked window keeps the model idle, never producing a fabricated output.",
  output: "The confirmed HR value and its timestamp — withheld, not zeroed, whenever any upstream stage is not confirmed.",
};

/**
 * Stage 6 Visualization B — Source → window → model → output pipeline
 * strip (master prompt §11/§18 "replace operational hex flow with a linear
 * process representation"). Reuses the existing, unmodified
 * `deriveHexFlow` pure derivation (lib/monitoring/inferenceHexFlow.ts) —
 * only the rendering changes from hexagonal geometry to a direct linear
 * strip of state chips connected by directional arrows. Selecting a block
 * reveals its provenance/current-requirement text; no information is
 * hover-only.
 */
export function PipelineStateStrip() {
  const view = useOperationalViewModel();
  const ppg = view.modalities.find((m) => m.modality === "PPG")!;
  const imu = view.modalities.find((m) => m.modality === "IMU")!;
  const { nodes } = deriveHexFlow({
    telemetry: view.telemetryAvailability,
    ppgState: ppg.nodeState,
    imuState: imu.nodeState,
    isReplay: view.isReplay,
    predictionAvailable: view.predictionAvailability === "available",
    inferenceWarmingUp: view.inference?.status === "warming_up",
  });

  const [expanded, setExpanded] = useState<HexNodeId | null>(null);
  const nodeById = (id: HexNodeId) => nodes.find((n) => n.id === id)!;
  // Linear presentation order: Source -> PPG/IMU (side-by-side inputs) -> Window -> Model -> Output.
  const chain: HexNodeId[] = ["source", "window", "model", "output"];

  // Renders a plain <div>, never <li> — this is nested inside a wrapping
  // <li> at every call site below, and an <li> cannot validly contain
  // another <li> without an intervening <ol>/<ul> (confirmed via a real
  // hydration-mismatch error in browser testing before this fix — see
  // docs/ismet-stage6-scientific-visualization-redesign/FINDING_LEDGER.md).
  function Chip({ id }: { id: HexNodeId }) {
    const n = nodeById(id);
    const isOpen = expanded === id;
    return (
      <div className="flex flex-1 flex-col items-stretch gap-1 min-w-[128px]">
        <button
          type="button"
          onClick={() => setExpanded(isOpen ? null : id)}
          aria-expanded={isOpen}
          className="flex min-h-[58px] flex-col items-center justify-center gap-1.5 rounded-[8px] border border-jury-border-subtle bg-surface-2 px-3 py-3 text-center min-[768px]:min-h-[68px] outline-none transition-colors hover:border-final-accent/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
        >
          <span className="text-[13px] font-semibold text-ink-primary">{n.label}</span>
          <StatusPill label={n.state === "fault" ? "Simulated fault" : n.state} tone={STATE_TONE[n.state]} />
        </button>
        {isOpen ? <p className="rounded-[6px] border border-jury-border-subtle bg-surface-1 p-2 text-xs leading-relaxed text-ink-secondary">{NODE_DETAIL[id]}</p> : null}
      </div>
    );
  }

  return (
    <section aria-labelledby="pipeline-strip-heading" className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="pipeline-strip-heading" className="text-sm font-semibold text-ink-primary">
          Source → window → model → output
        </h2>
        <span className="text-xs uppercase tracking-wide text-ink-muted">Categorical pipeline state · not a confidence score</span>
      </div>

      {/* Desktop: linear horizontal strip. Mobile: vertical ordered process list. */}
      <ol className="flex flex-col gap-2 min-[1180px]:hidden" aria-label="Pipeline stages, in order">
        <li>
          <Chip id="source" />
        </li>
        <li className="flex gap-2">
          <Chip id="ppgInput" />
          <Chip id="imuInput" />
        </li>
        {chain.slice(1).map((id) => (
          <li key={id}>
            <Chip id={id} />
          </li>
        ))}
      </ol>
      <ol className="hidden items-start gap-2 min-[1180px]:flex" aria-label="Pipeline stages, in order">
        <li>
          <Chip id="source" />
        </li>
        <li className="flex flex-1 flex-col gap-2">
          <div className="flex gap-2">
            <Chip id="ppgInput" />
            <Chip id="imuInput" />
          </div>
        </li>
        {chain.slice(1).map((id) => (
          <li key={id}>
            <Chip id={id} />
          </li>
        ))}
      </ol>

      <p className="text-xs leading-snug text-ink-muted">
        {nodeById("window").state === "blocked"
          ? "Window assembly requires both PPG and IMU — one confirmed input alone is insufficient."
          : "PPG + IMU assemble the model input window; the model produces the HR output. Select any stage for its exact requirement."}
      </p>
    </section>
  );
}
