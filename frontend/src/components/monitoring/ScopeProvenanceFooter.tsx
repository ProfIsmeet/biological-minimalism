"use client";

import Link from "next/link";

import { useMonitoringSession } from "@/components/monitoring/MonitoringSessionContext";
import { deriveSourceLabel } from "@/lib/monitoring/sourceState";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

// Master-prompt §8.8 — scope and provenance footer. Every field is read from
// the same canonical state the rest of the page uses; the three required
// notes are rendered verbatim.
//
// Prompt-2 corrective pass §2: `latest` is read only through
// `useConfirmedSnapshot()` so this footer can never show a dataset/subject/
// channel-list/model-identity value from a stale cross-source frame.
export function ScopeProvenanceFooter() {
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  const { snapshot: latest } = useConfirmedSnapshot();
  const isReplay = useDatasetReplayMode();
  const { status } = useMonitoringSession();
  const sourceLabel = deriveSourceLabel({ connectionStatus, isReplay });
  const datasetName = latest?.source.dataset_name ?? status?.dataset_name;
  const subjectId = latest?.source.subject_id ?? status?.subject_id;
  const prediction = isReplay ? latest?.heart_rate_prediction : null;
  const availableChannels = latest?.source.available_channels ?? status?.channels.map((channel) => channel.name) ?? [];

  return (
    <footer className="flex flex-col gap-3 rounded-lg border border-white/10 bg-white/[0.015] p-4 text-xs text-slate-400">
      <dl className="grid grid-cols-1 gap-x-6 gap-y-2 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-slate-600">Active source</dt>
          <dd className="mt-0.5 text-slate-300">{sourceLabel}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-slate-600">Dataset</dt>
          <dd className="mt-0.5 text-slate-300">{isReplay ? (datasetName ?? "Dataset unavailable") : "Not applicable"}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-slate-600">Subject</dt>
          <dd className="mt-0.5 text-slate-300">{isReplay ? (subjectId ?? "No subject selected") : "Not applicable"}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-slate-600">Model identity</dt>
          <dd className="mt-0.5 break-all text-slate-300">{prediction ? prediction.provenance.model_id : "Not available"}</dd>
        </div>
        <div className="sm:col-span-2 lg:col-span-2">
          <dt className="text-[10px] uppercase tracking-wide text-slate-600">Channel list</dt>
          <dd className="mt-0.5 text-slate-300">{availableChannels.length ? availableChannels.join(", ") : "None reported by current source"}</dd>
        </div>
        <div className="sm:col-span-2 lg:col-span-2">
          <dt className="text-[10px] uppercase tracking-wide text-slate-600">Current limitation</dt>
          <dd className="mt-0.5 text-slate-300">
            No reference/ground-truth HR channel exists in the current runtime contract; accuracy metrics are only
            available as frozen, offline evaluation artifacts.
          </dd>
        </div>
      </dl>

      <div className="flex flex-col gap-1 border-t border-white/5 pt-3">
        <p>Recorded replay is not live astronaut monitoring.</p>
        <p>The S14 replay, when selected, is a single-participant stress test and not population validation.</p>
        <p>Dashboard values are not the source of scientific Results.</p>
      </div>

      <Link href="/research/experimental" className="w-fit text-cyan-300 underline underline-offset-2">
        See Experimental Research
      </Link>
    </footer>
  );
}
