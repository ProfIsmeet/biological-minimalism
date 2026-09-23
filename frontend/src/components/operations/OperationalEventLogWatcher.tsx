"use client";

import { useEffect, useRef } from "react";

import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";
import { deriveEventsFromTransition, type OperationalEventSignature } from "@/lib/monitoring/operationalEvents";
import { useOperationalEventStore } from "@/store/operationalEventStore";

/**
 * Mounted exactly once (root layout, master prompt 3 §16) so the session
 * event log is observed from a single place regardless of which
 * page/component is currently rendering OperationalEventRail. Renders
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

    const events = deriveEventsFromTransition(previousSignature.current, signature, {
      sourceLabel: view.sourceLabel,
      sourceTimestampSeconds: view.confirmedTimestampSeconds,
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
    view.confirmedTimestampSeconds,
    appendEvents,
  ]);

  return null;
}
