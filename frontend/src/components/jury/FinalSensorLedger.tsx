"use client";

import { FINAL_SENSOR_INVENTORY } from "@/lib/architecture";
import { deriveModalityObservation, type ModalityObservationState } from "@/lib/monitoring/modalityObservation";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

/**
 * Master-prompt corrective pass §6 — final-sensor ledger. Architecture
 * membership (all five modalities are structurally part of CORE_PLUS_CONTEXT
 * — a static fact) and telemetry observation (what the *current* payload
 * actually reports) are kept as two separate fields, never merged.
 *
 * Prompt-2 update (master prompt §6): the per-modality observation logic
 * that used to live inline here now comes from the shared
 * lib/monitoring/modalityObservation.ts helper, so this ledger and the
 * live-monitoring signal stack can never silently diverge on what
 * "observed" means for a given modality/source. See that module's doc
 * comment for the backend-contract grounding.
 *
 * Prompt-2 corrective pass §2/§5: reads the confirmed snapshot (never a
 * stale cross-source frame) and colors the new
 * "recorded_replay_waiting_for_samples" state neutrally, distinct from both
 * "observed" (success) and "unavailable" (disabled).
 */
function observationColor(state: ModalityObservationState, syntheticStatus: "nominal" | "degraded" | "offline" | undefined): string {
  if (state === "unavailable") return "text-ink-disabled";
  if (state === "recorded_replay_waiting_for_samples") return "text-information";
  if (state === "recorded_replay_observed") return "text-jury-success";
  if (syntheticStatus === "degraded") return "text-jury-warning";
  if (syntheticStatus === "offline") return "text-jury-fault";
  return "text-jury-success";
}

export function FinalSensorLedger() {
  const { snapshot: latest } = useConfirmedSnapshot();
  const sensors = latest?.sensor_health?.sensors;
  const availableChannels = latest?.source.available_channels;
  const channels = latest?.channels;
  const isReplay = useDatasetReplayMode();

  return (
    <div className="overflow-hidden rounded-[10px] border border-jury-border-subtle bg-surface-1">
      <div className="hidden grid-cols-[0.8fr_0.8fr_1.2fr_1.4fr] gap-2 border-b border-jury-border-subtle px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-ink-muted sm:grid">
        <span>Modality</span>
        <span>Region</span>
        <span>Architecture membership</span>
        <span>Telemetry observation</span>
      </div>
      <ul className="divide-y divide-jury-border-subtle">
        {FINAL_SENSOR_INVENTORY.map((entry) => {
          const observation = deriveModalityObservation(entry.modality, { isReplay, channels, availableChannels, sensors });

          return (
            <li
              key={entry.modality}
              className="grid grid-cols-2 gap-x-2 gap-y-1 px-4 py-3 text-sm sm:grid-cols-[0.8fr_0.8fr_1.2fr_1.4fr] sm:items-center"
            >
              <span className="font-semibold text-ink-primary">{entry.modality}</span>
              <span className="text-ink-secondary">{entry.region}</span>
              <span className="text-ink-secondary">Selected — CORE_PLUS_CONTEXT</span>
              <span className={observationColor(observation.state, observation.syntheticHealth?.status)}>
                {observation.statusLabel}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="border-t border-jury-border-subtle px-4 py-2.5 text-[11px] leading-relaxed text-ink-muted">
        Architecture membership is a structural fact from the final architecture artifact; it is never inferred as a
        live signal. Telemetry observation reflects only what the current session&rsquo;s payload actually reports —
        EEG is not present in PPG-DaLiA replay, and EOG has no channel in the current backend contract at all.
      </p>
    </div>
  );
}
