"use client";

import { useMemo } from "react";
import { Line, LineChart, ReferenceArea, ResponsiveContainer, XAxis, YAxis } from "recharts";

import { ChartFrame, SemanticTable, StatusPill } from "@/components/visualization/shared/ChartFrame";
import { deriveFaultRecoveryTimeline } from "@/lib/monitoring/faultRecoveryTimeline";
import { useConfirmedHistory } from "@/lib/monitoring/useConfirmedSnapshot";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";
import { useOperationalEventStore } from "@/store/operationalEventStore";

/**
 * Stage 6 Visualization C — Fault & recovery timeline (replaces
 * FaultRecoverySpine + OperationalEventRail, master prompt §12/§18).
 *
 * X-axis is real replay time in seconds (never client wall-clock arrival
 * order, never evenly spaced) — grounded in
 * `OperationalEvent.sourceTimestampSeconds`, which is itself the confirmed
 * snapshot's own clock. When even one relevant event in this session lacks a
 * real timestamp, the chart falls back to a text-only chronology rather than
 * drawing a misleading axis (see faultRecoveryTimeline.ts axisAvailable).
 */
export function FaultRecoveryTimeline() {
  const events = useOperationalEventStore((state) => state.events);
  const view = useOperationalViewModel();
  const history = useConfirmedHistory();

  const hrSamples = useMemo(
    () => history.map((s) => ({ timestampSeconds: s.timestamp, heartRateBpm: s.heart_rate_prediction?.value ?? null })),
    [history],
  );

  const model = useMemo(
    () => deriveFaultRecoveryTimeline(events, hrSamples, view.confirmedTimestampSeconds),
    [events, hrSamples, view.confirmedTimestampSeconds],
  );

  const relevantEvents = model.events.filter((e) => e.eventClass !== "other");
  const hasAnyEvent = relevantEvents.length > 0;

  return (
    <ChartFrame
      id="fault-recovery-timeline"
      title="Fault &amp; recovery timeline"
      unit="replay seconds · HR bpm"
      summary="Real recorded fault-onset, fault-clear, and recovery events from this interface session, plotted against confirmed HR output over replay time. Gaps in the HR line are intervals where output was withheld, not zero."
      minHeightClassName="min-h-[280px]"
      footer={
        <>
          {!hasAnyEvent ? (
            <p className="text-xs text-ink-muted">No fault or recovery events in this interface session. Apply a simulated fault to trace the response.</p>
          ) : !model.axisAvailable ? (
            <div className="flex flex-col gap-2">
              <p className="text-xs text-jury-warning">
                Real replay-time chronology unavailable for one or more events — showing text order only, not a fabricated time axis.
              </p>
              <ol className="flex flex-col gap-1 text-xs text-ink-secondary">
                {relevantEvents.map((e) => (
                  <li key={e.id} className="flex items-center gap-2">
                    <StatusPill
                      label={e.eventClass === "fault_onset" ? "Fault" : e.eventClass === "fault_clear" ? "Cleared" : "Recovery"}
                      tone={e.eventClass === "fault_onset" ? "fault" : "nominal"}
                    />
                    <span className="font-medium text-ink-primary">{e.label}</span>
                    {e.modality ? <span className="text-ink-muted">· {e.modality}</span> : null}
                    {e.simulated ? <span className="text-[10px] uppercase tracking-wide text-ink-disabled">SIMULATED</span> : null}
                  </li>
                ))}
              </ol>
            </div>
          ) : (
            <SemanticTable
              caption="Fault and recovery events with exact replay-time and duration"
              columns={["Event", "Modality", "Replay time (s)", "Duration (s)", "Origin"]}
              rows={model.intervals.map((interval) => ({
                key: interval.id,
                cells: [
                  interval.ongoing ? "Fault (ongoing)" : "Fault — cleared",
                  interval.modality ?? "—",
                  interval.onsetSeconds.toFixed(1),
                  interval.ongoing
                    ? `${(model.domainSeconds ? model.domainSeconds[1] - interval.onsetSeconds : 0).toFixed(1)}+ (ongoing)`
                    : ((interval.clearSeconds ?? interval.onsetSeconds) - interval.onsetSeconds).toFixed(1),
                  interval.simulated ? "SIMULATED" : "Source-reported",
                ],
              }))}
            />
          )}
        </>
      }
    >
      {model.axisAvailable && model.hrPoints.length > 0 && model.domainSeconds ? (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={model.hrPoints} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            {model.intervals.map((interval) => (
              <ReferenceArea
                key={interval.id}
                x1={interval.onsetSeconds}
                x2={interval.ongoing ? model.domainSeconds![1] : (interval.clearSeconds ?? interval.onsetSeconds)}
                fill={interval.simulated ? "#D46F70" : "#D5A45E"}
                fillOpacity={0.12}
                stroke="none"
              />
            ))}
            <XAxis
              dataKey="timeSeconds"
              type="number"
              domain={model.domainSeconds}
              tick={{ fontSize: 12, fill: "#8CA0A6" }}
              tickFormatter={(v: number) => `${v.toFixed(0)}s`}
              axisLine={false}
              tickLine={false}
              label={{ value: "Replay time (s)", position: "insideBottom", offset: -4, fontSize: 12, fill: "#8CA0A6" }}
              height={32}
            />
            <YAxis
              dataKey="heartRateBpm"
              tick={{ fontSize: 12, fill: "#8CA0A6" }}
              axisLine={false}
              tickLine={false}
              width={40}
              label={{ value: "HR (bpm)", angle: -90, position: "insideLeft", fontSize: 12, fill: "#8CA0A6" }}
            />
            <Line type="monotone" dataKey="heartRateBpm" stroke="#69B7AD" strokeWidth={2} dot={false} isAnimationActive={false} connectNulls={false} />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex h-full items-center justify-center text-center text-[13px] leading-snug text-ink-muted">
          {view.isReplay ? "No confirmed HR history in this session yet." : "Not applicable — synthetic demo carries no HR prediction stream."}
        </div>
      )}
    </ChartFrame>
  );
}
