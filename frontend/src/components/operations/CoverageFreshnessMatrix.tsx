"use client";

import { MODALITY_COLOR, type FinalModality } from "@/lib/architecture";
import { StatusPill, SemanticTable } from "@/components/visualization/shared/ChartFrame";
import { useOperationalViewModel, type OperationalModalityState } from "@/lib/monitoring/operationalViewModel";

/**
 * Stage 6 Visualizations A + D — Selected-architecture-vs-observed-coverage
 * matrix, merged with modality freshness (master prompt §10/§13/§18 "move or
 * replace the modality pentagon with the coverage matrix"). Rows are the five
 * final-architecture modalities (PPG/IMU/ECG/EEG/EOG); columns separate
 * "selected architecture" (a static fact, lib/architecture.ts
 * FINAL_SENSOR_INVENTORY) from "current observation" (a live fact, this
 * modality's ModalityNodeState) — merged into one component rather than two
 * near-duplicate row-per-modality views, since both questions share the exact
 * same row structure and the exact same live view model.
 *
 * This runtime exposes no per-channel last-confirmed-age or numeric
 * freshness threshold (checked: lib/monitoring/modalityObservation.ts has no
 * per-channel timestamp field) — so "freshness" here is the honest
 * categorical backend state (confirmed / warm-up / fault / unavailable /
 * disconnected / awaiting-confirmation / source-error), not an invented age
 * bar. The one authoritative session-level "as of" time
 * (view.replayPositionSeconds) is shown once, not fabricated per row.
 */
function tone(state: OperationalModalityState["nodeState"]): "nominal" | "warning" | "fault" | "muted" {
  if (state === "confirmed") return "nominal";
  if (state === "fault" || state === "source_error") return "fault";
  if (state === "warmup" || state === "awaiting_confirmation") return "warning";
  return "muted";
}

function coverageText(entry: OperationalModalityState, isReplay: boolean): string {
  if (entry.observation.state === "unavailable") {
    return isReplay ? "Not provided by this replay" : "Not reported by current telemetry";
  }
  if (entry.observation.state === "recorded_replay_waiting_for_samples") return "Awaiting confirmation";
  return "Currently observed";
}

export function CoverageFreshnessMatrix({
  selected,
  onSelect,
  compact = false,
}: {
  selected?: FinalModality;
  onSelect?: (m: FinalModality) => void;
  compact?: boolean;
}) {
  const view = useOperationalViewModel();

  return (
    <section aria-labelledby="coverage-freshness-heading" className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="coverage-freshness-heading" className="text-sm font-semibold text-ink-primary sm:text-base">
          Coverage &amp; freshness
        </h2>
        <span className="text-xs uppercase tracking-wide text-ink-muted">CORE_PLUS_CONTEXT selected · {view.isReplay ? "recorded replay" : "synthetic demo"}</span>
      </div>
      <p className="text-sm leading-relaxed text-ink-secondary">
        Selected architecture membership is a static fact and is not equivalent to what the current source actually
        provides. A replay may carry only part of the final five-modality architecture.
      </p>

      <ul className="flex flex-col gap-2">
        {view.modalities.map((entry) => {
          const isSel = selected === entry.modality;
          const content = (
            <>
              <span
                aria-hidden="true"
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: MODALITY_COLOR[entry.modality], opacity: entry.nodeState === "confirmed" ? 1 : 0.35 }}
              />
              <span className="flex min-w-[60px] flex-col">
                <span className="text-sm font-semibold text-ink-primary">{entry.modality}</span>
                <span className="text-[11px] text-ink-muted">{entry.region}</span>
              </span>
              <span className="flex-1 text-xs text-ink-secondary">{coverageText(entry, view.isReplay)}</span>
              <StatusPill label={entry.stateLabel} tone={tone(entry.nodeState)} />
            </>
          );
          return (
            <li key={entry.modality}>
              {onSelect ? (
                <button
                  type="button"
                  onClick={() => onSelect(entry.modality)}
                  aria-pressed={isSel}
                  className={`flex w-full items-center gap-2 rounded-[6px] border px-2 py-2 text-left outline-none transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC] ${
                    isSel ? "border-final-accent/60 bg-final-accent-soft" : "border-jury-border-subtle bg-surface-2"
                  }`}
                >
                  {content}
                </button>
              ) : (
                <div className="flex w-full items-center gap-2 rounded-[6px] border border-jury-border-subtle bg-surface-2 px-2 py-2">{content}</div>
              )}
            </li>
          );
        })}
      </ul>

      {!compact ? (
        <SemanticTable
          caption="Exact coverage and inference role per modality"
          columns={["Modality", "Region", "Selected architecture", "Current observation", "Inference role", "Absence/fault reason"]}
          rows={view.modalities.map((entry) => ({
            key: entry.modality,
            cells: [
              entry.modality,
              entry.region,
              "CORE_PLUS_CONTEXT member",
              coverageText(entry, view.isReplay),
              entry.modality === "PPG" || entry.modality === "IMU" ? "HR inference input" : "Architecture member — not consumed by the demonstrated HR pipeline",
              entry.observation.unavailableReason ?? (entry.nodeState === "fault" ? "Simulated fault active" : "—"),
            ],
          }))}
        />
      ) : null}

      <p className="text-xs leading-snug text-ink-muted">
        {/* Fresh-session audit correction (S6A-FIND-01, CRITICAL, same root
            cause as FaultRecoveryTimeline): this line used
            view.confirmedTimestampSeconds (a wall-clock epoch value) and
            mislabeled it "replay t=" — confirmed via a real populated-replay
            run showing "replay t=1790704719.9s". view.replayPositionSeconds
            is the genuine in-session replay-position field. */}
        As of {view.replayPositionSeconds !== null ? `replay t=${view.replayPositionSeconds.toFixed(1)}s` : "no confirmed frame yet"} ·
        this runtime does not expose a per-channel last-confirmed age, so state is shown categorically rather than as an invented freshness bar.
      </p>
    </section>
  );
}
