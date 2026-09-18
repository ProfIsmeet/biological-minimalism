"use client";

import { WaveformChart } from "@/components/charts/WaveformChart";
import { FINAL_SENSOR_INVENTORY, type FinalModality } from "@/lib/architecture";
import { downsampleForDisplay } from "@/lib/monitoring/formatMonitoringValue";
import { deriveModalityObservation, type ModalityObservation } from "@/lib/monitoring/modalityObservation";
import { resolvePlotSeries, type PlotSeries } from "@/lib/monitoring/plotSeries";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

const MODALITY_COLOR: Record<FinalModality, string> = {
  PPG: "#4fd8e8",
  IMU: "#6b8fd6",
  ECG: "#e0716b",
  EEG: "#a893d1",
  EOG: "#d8b25c",
};

function SignalRow({ modality, region, observation, plot }: {
  modality: FinalModality;
  region: string;
  observation: ModalityObservation;
  plot: PlotSeries | null;
}) {
  const downsampled = plot ? downsampleForDisplay(plot.values) : null;

  return (
    <div className="grid grid-cols-1 gap-2 border-b border-white/5 py-3 last:border-0 sm:grid-cols-[200px_1fr] sm:gap-4 sm:py-4">
      <div className="flex flex-col gap-0.5">
        <p className="text-sm font-semibold text-slate-200">{modality} — {region}</p>
        <p className="text-[11px] text-slate-500">Selected — CORE_PLUS_CONTEXT</p>
        <p className="text-[11px] text-slate-500">{observation.channelName ?? "No channel in current source"}</p>
        <p className="text-[11px] text-slate-400">{observation.statusLabel}</p>
      </div>
      <figure
        aria-label={`${modality} ${region} signal`}
        className={
          observation.state === "recorded_replay_waiting_for_samples"
            ? "flex min-h-[140px] flex-col justify-center rounded-md border border-cyan-400/15 bg-cyan-400/[0.03] p-2"
            : "flex min-h-[140px] flex-col justify-center rounded-md border border-white/5 bg-space-900/40 p-2"
        }
      >
        {plot && downsampled ? (
          <>
            <WaveformChart data={downsampled.values} color={MODALITY_COLOR[modality]} height={110} />
            <figcaption className="mt-1 flex flex-wrap gap-x-3 text-[10px] text-slate-500">
              {plot.unit ? <span>Unit: {plot.unit}</span> : <span>Unit: not provided by current source</span>}
              {plot.transform ? <span>{plot.transform}</span> : null}
              {downsampled.downsampled ? <span>Display downsampled</span> : null}
            </figcaption>
          </>
        ) : observation.state === "recorded_replay_waiting_for_samples" ? (
          // Prompt-2 corrective §5: neutral/informational styling — the
          // channel is confirmed present, just no sample batch has arrived
          // for the current window yet. This must never be styled or worded
          // like the genuinely-unavailable case below.
          <figcaption className="flex h-[110px] items-center justify-center text-center text-xs text-cyan-200/80">
            Recorded replay — channel available; waiting for current-window samples.
          </figcaption>
        ) : (
          <figcaption className="flex h-[110px] items-center justify-center text-center text-xs text-slate-500">
            {observation.unavailableReason
              ?? "Health status reported; no plottable waveform for this channel in the active source."}
          </figcaption>
        )}
      </figure>
    </div>
  );
}

// Master-prompt §8.3 — final modality observations. Fixed order: PPG(Wrist),
// IMU(Wrist), ECG(Chest), EEG(Frontal), EOG(Frontal). Every row's plot data
// (or lack of it) traces back to an actual payload field via
// deriveModalityObservation/resolvePlotSeries — no row ever draws a
// placeholder waveform.
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
    <section aria-labelledby="signal-stack-heading" className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
      <h2 id="signal-stack-heading" className="text-sm font-semibold text-slate-200">
        Final modality observations
      </h2>
      {isWaitingForConfirmation ? (
        <p role="status" className="mt-2 rounded-md border border-cyan-400/20 bg-cyan-400/5 px-3 py-2 text-xs text-cyan-200">
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
