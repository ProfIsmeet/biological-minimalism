"use client";

import { useEffect, useRef } from "react";

import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";
import { deriveEventsFromTransition, type OperationalEventSignature } from "@/lib/monitoring/operationalEvents";
import { useOperationalEventStore } from "@/store/operationalEventStore";

/**
 * Mounted exactly once (root layout, master prompt 3 §16) so the session
 * event log is observed from a single place regardless of which
 * page/component is currently rendering FaultRecoveryTimeline. Renders
 * nothing — it only watches `useOperationalViewModel()` for genuine state
 * transitions and appends the resulting events to the shared store.
 */
export function OperationalEventLogWatcher() {
  const view = useOperationalViewModel();
  const appendEvents = useOperationalEventStore((state) => state.appendEvents);
  const previousSignature = useRef<OperationalEventSignature | null>(null);

  useEffect(() => {
    const signature: OperationalEventSignature = {
      connected: view.connected,
      sourceType: view.sourceType,
      subjectId: view.subjectId,
      replaySessionState: view.replaySessionState,
      inferenceStatus: view.inference?.status ?? null,
      predictionAvailability: view.predictionAvailability,
      faultActive: view.faultActive,
      faultedModalities: view.faultedModalities,
      sourceStateStatus: view.sourceStateStatus,
    };

    // Stage 6 fresh-session audit correction (S6A-FIND-01, CRITICAL):
    // `view.confirmedTimestampSeconds` is backed by missionStore's
    // `lastConfirmedTimestampSeconds`, which is set from the snapshot's own
    // `timestamp` field — a server wall-clock value (confirmed via a real
    // populated-replay run: it read ~1.79e9, a 2026 Unix-epoch second count,
    // not a small "seconds into an 8958s replay" value). `sourceTimestampSeconds`
    // is consumed by FaultRecoveryTimeline as if it were real replay time; it
    // must be the genuine replay position instead, from
    // `view.replayPositionSeconds` (backed by `source.replay_position_seconds`,
    // confirmed via the same run to read ~24.5s / ~44.7s as expected).
    const events = deriveEventsFromTransition(previousSignature.current, signature, {
      sourceLabel: view.sourceLabel,
      sourceTimestampSeconds: view.replayPositionSeconds,
      clientMs: Date.now(),
    });
    previousSignature.current = signature;
    if (events.length > 0) appendEvents(events);
  }, [
    view.connected,
    view.sourceType,
    view.subjectId,
    view.replaySessionState,
    view.inference?.status,
    view.predictionAvailability,
    view.faultActive,
    view.faultedModalities,
    view.sourceStateStatus,
    view.sourceLabel,
    view.replayPositionSeconds,
    appendEvents,
  ]);

  return null;
}
