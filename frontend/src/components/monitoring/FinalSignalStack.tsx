"use client";

import { WaveformChart } from "@/components/charts/WaveformChart";
import { FINAL_SENSOR_INVENTORY, MODALITY_COLOR, type FinalModality } from "@/lib/architecture";
import { deriveModalityObservation, type ModalityObservation } from "@/lib/monitoring/modalityObservation";
import { resolvePlotSeries, type PlotSeries } from "@/lib/monitoring/plotSeries";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

function SignalRow({ modality, region, observation, plot }: {
  modality: FinalModality;
  region: string;
  observation: ModalityObservation;
  plot: PlotSeries | null;
}) {
  const accessibleLabel = `${modality} ${region} signal — ${observation.statusLabel}${
    plot ? ` — ${plot.values.length} samples${plot.unit ? `, unit ${plot.unit}` : ""}` : ""
  }`;

  return (
    <div
      id={`signal-${modality}`}
      className="grid grid-cols-1 gap-2 border-b border-jury-border-subtle py-3 last:border-0 sm:grid-cols-[176px_1fr] sm:gap-4 sm:py-4 sm:scroll-mt-20"
    >
      <div className="flex flex-col gap-1">
        <span
          aria-hidden="true"
          className="h-0.5 w-8 rounded-full"
          style={{ backgroundColor: MODALITY_COLOR[modality] }}
        />
        <p className="text-sm font-semibold text-ink-primary">
          {modality} <span className="font-normal text-ink-muted">— {region}</span>
        </p>
        <p className="text-[11px] text-ink-muted">{observation.channelName ?? "No channel in current source"}</p>
        <p className="text-[11px] text-ink-secondary">{observation.statusLabel}</p>
      </div>
      <figure
        aria-label={accessibleLabel}
        className={
          observation.state === "recorded_replay_waiting_for_samples"
            ? "flex min-h-[140px] flex-col justify-center rounded-[6px] border border-information/25 bg-information-soft p-2"
            : "flex min-h-[140px] flex-col justify-center rounded-[6px] border border-jury-border-subtle bg-surface-2 p-2"
        }
      >
        {plot ? (
          <WaveformChart
            values={plot.values}
            color={MODALITY_COLOR[modality]}
            height={110}
            unit={plot.unit}
            transform={plot.transform}
            sampleRateHz={plot.sampleRateHz}
            startTimestampSeconds={plot.startTimestampSeconds}
          />
        ) : observation.state === "recorded_replay_waiting_for_samples" ? (
          <figcaption className="flex h-[110px] items-center justify-center text-center text-xs text-information">
            Recorded replay — channel available; waiting for current-window samples.
          </figcaption>
        ) : (
          <figcaption className="flex h-[110px] items-center justify-center text-center text-xs text-ink-muted">
            {observation.unavailableReason
              ?? "Health status reported; no plottable waveform for this channel in the active source."}
          </figcaption>
        )}
      </figure>
    </div>
  );
}

// Master-prompt §8.3/§8.7 — final modality observations. Fixed order: PPG
// (Wrist), IMU (Wrist), ECG (Chest), EEG (Frontal), EOG (Frontal). Every
// row's plot data (or lack of it) traces back to an actual payload field via
// deriveModalityObservation/resolvePlotSeries — no row ever draws a
// placeholder waveform. WaveformChart owns downsampling/domain internally
// (lib/monitoring/waveformDisplay.ts), so this component only supplies raw
// values plus the payload-derived unit/sample-rate/timing metadata.
// Prompt-2 corrective pass §2: reads the confirmed snapshot rather than raw
// `latest`, so a stale cross-source frame can never populate a channel row
// with the wrong source's samples.
export function FinalSignalStack() {
  const isReplay = useDatasetReplayMode();
  const { snapshot: latest, isWaitingForConfirmation } = useConfirmedSnapshot();
  const channels = latest?.channels;
  const availableChannels = latest?.source.available_channels;
  const sensors = latest?.sensor_health?.sensors;
  const syntheticPpgWaveform = latest?.vitals?.ppg_waveform;

  return (
    <section aria-labelledby="signal-stack-heading" className="rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="signal-stack-heading" className="text-sm font-semibold text-ink-primary">
          Final modality observations
        </h2>
        <span className="text-[11px] uppercase tracking-wide text-ink-muted">Selected — CORE_PLUS_CONTEXT</span>
      </div>
      {isWaitingForConfirmation ? (
        <p role="status" className="mt-2 rounded-md border border-information/25 bg-information-soft px-3 py-2 text-xs text-information">
          Waiting for a confirmed frame from the selected source.
        </p>
      ) : null}
      <div className="mt-2">
        {FINAL_SENSOR_INVENTORY.map((entry) => {
          const observation = deriveModalityObservation(entry.modality, { isReplay, channels, availableChannels, sensors });
          const plot = resolvePlotSeries(entry.modality, isReplay, observation, syntheticPpgWaveform);
          return <SignalRow key={entry.modality} modality={entry.modality} region={entry.region} observation={observation} plot={plot} />;
        })}
      </div>
    </section>
  );
}
