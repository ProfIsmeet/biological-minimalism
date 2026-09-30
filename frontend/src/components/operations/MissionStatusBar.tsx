"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";

import { DemoControlDrawer } from "@/components/operations/DemoControlDrawer";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";
import { deriveOperationalPhase, PHASE_PRESENTATION } from "@/lib/visualization/operationalVisualTokens";

/**
 * Starts `null` (matching server render) and is set to a real timestamp only
 * after mount, so the server-rendered markup and the client's first render
 * are identical — `Date.now()` can never be used as initial state without
 * causing a hydration mismatch between the two clocks.
 */
function useNowMs(intervalMs: number): number | null {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now());
    const id = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
}

function formatUtcClock(ms: number): string {
  return `${new Date(ms).toISOString().slice(11, 19)} UTC`;
}

function fieldTone(kind: "primary" | "fault" | "muted" | "success" | "warning"): string {
  if (kind === "fault") return "text-jury-fault";
  if (kind === "success") return "text-jury-success";
  if (kind === "warning") return "text-jury-warning";
  if (kind === "muted") return "text-ink-secondary";
  return "text-ink-primary";
}

interface Field {
  label: string;
  value: string;
  tone: "primary" | "fault" | "muted" | "success" | "warning";
}

/**
 * Row 1 of `/mission-overview` (master prompt 3 §11). A compact instrument
 * strip, not a tall explanatory card — every field is a real derived value
 * from the shared operational view model, and the scope label is a single
 * short sentence rather than the old long Results disclaimer paragraph.
 */
export function MissionStatusBar() {
  const view = useOperationalViewModel();
  const nowMs = useNowMs(1000);
  // Mission Overview §8.1/§19 — one stable categorical phase word replaces
  // both the per-second confirmed-frame age ticker (removed: it changed
  // every second purely to prove liveness, and its appear/disappear cycle
  // was visually distracting) and the raw CONNECTING/UNAVAILABLE labels that
  // previously rendered fault-red during ordinary startup.
  // `view.confirmedTimestampSeconds` itself is deliberately NOT deleted — it
  // remains the authoritative freshness input for guards, history isolation
  // and tests; only this visible presentation of it is gone. A structural
  // guard asserts the removed field label never reappears in this file.
  const phase = deriveOperationalPhase({
    connectionLabel: view.connectionLabel,
    telemetryAvailability: view.telemetryAvailability,
  });
  const phasePresentation = PHASE_PRESENTATION[phase];

  // Prompt 3A.1 §4.3/§4.4 — session identity must never leak through while
  // telemetry is flatly disconnected or the REST source-state channel is
  // erroring; it may legitimately show the *target* identity while a
  // switch-in-progress (`awaiting_confirmation`) is resolving, since that is
  // not stale data, it is the confirmed destination of an in-flight action.
  const sessionIdentity =
    view.telemetryAvailability === "disconnected"
      ? "No session"
      : view.telemetryAvailability === "source_error"
        ? "Session unavailable"
        : view.isReplay
          ? `${view.datasetName ?? "PPG-DaLiA"} · ${view.subjectId ?? "subject not loaded"}`
          : "Synthetic demo session";

  // Prompt 3A.1 §5 — "Do not display None for simulated fault when the
  // system cannot currently confirm fault state. Use Unavailable." — `None`
  // is only ever shown while telemetry is active and genuinely confirms no
  // fault is running.
  const faultValue =
    view.telemetryAvailability !== "active"
      ? "Unavailable"
      : view.faultActive
        ? view.faultSummaryLabel.replace("Simulated fault active — ", "")
        : "None";

  // Master prompt 3A §12 — required order: session, source, connection,
  // replay state, simulated fault, last confirmed frame, session clock. A
  // field that is genuinely not applicable (replay state while synthetic,
  // frame age before any frame is confirmed) is omitted entirely rather
  // than shown as a long placeholder sentence.
  // §8.1 — during the ordinary startup window the source is not "UNAVAILABLE
  // (fault red)", it is simply not established yet. Only a genuine
  // authoritative failure (`source_error`) or a real drop earns fault red.
  const sourceIsGenuinelyFailed = phase === "source_error" || phase === "disconnected";
  const fields: Field[] = [
    { label: "Session", value: sessionIdentity, tone: "primary" },
    {
      label: "Source",
      value: sourceIsGenuinelyFailed ? view.sourceLabel : phase === "connected" ? view.sourceLabel : phasePresentation.label,
      tone: sourceIsGenuinelyFailed ? "fault" : phase === "connected" ? "primary" : "warning",
    },
    { label: "Status", value: phasePresentation.label, tone: phasePresentation.tone === "nominal" ? "success" : phasePresentation.tone === "fault" ? "fault" : "warning" },
  ];
  if (view.isReplay) fields.push({ label: "Replay state", value: view.replaySessionStateLabel, tone: view.telemetryAvailability === "active" ? "muted" : "warning" });
  fields.push({ label: "Simulated fault", value: faultValue, tone: view.faultActive && view.telemetryAvailability === "active" ? "fault" : "muted" });
  fields.push({ label: "Session time", value: nowMs === null ? "—" : formatUtcClock(nowMs), tone: "muted" });

  // A11y fix (Stage 2 A1): `role="status"` is an implicit `aria-live="polite"`
  // region. Applying it to the WHOLE strip re-announces the entire field set
  // every time ANY field's rendered text changes — which historically
  // included both the session clock and a per-second confirmed-frame age
  // ticker. That means a screen reader user hears this whole block re-read
  // once per second, forever, regardless of whether anything meaningful
  // happened.
  //
  // Fix is structural, not time-based throttling: the visible strip below
  // carries NO live-region role at all (so per-second re-renders are silent
  // to assistive tech), and a separate, visually-hidden summary — built
  // ONLY from the fields that represent real state transitions (session,
  // source, status, replay state, fault) — is the sole `aria-live` region.
  // Because that summary's own text never includes the clock, it can only
  // change (and therefore only be announced) when one of those meaningful
  // fields actually changes value. The frame-age field was removed outright
  // in the Mission Overview recomposition (§19), so the clock is now the
  // only per-second value needing exclusion.
  const announceableFields = fields.filter((field) => field.label !== "Session time");
  const liveSummary = announceableFields.map((field) => `${field.label}: ${field.value}`).join(". ");

  // Fault gets its own full-width, never-truncated row instead of sharing a
  // same-size grid cell with routine identity fields (Session/Source/Session
  // time) — a genuinely active fault is the single most operationally
  // important fact on this page and must outrank everything else visually,
  // not read as "one more field among six." The routine grid keeps the
  // remaining fields; "Simulated fault" is removed from it when active.
  const faultIsActive = view.faultActive && view.telemetryAvailability === "active";
  const routineFields = faultIsActive ? fields.filter((field) => field.label !== "Simulated fault") : fields;

  return (
    <div className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 px-4 py-3">
      <span className="sr-only" role="status" aria-live="polite">
        {liveSummary}
      </span>

      {faultIsActive ? (
        <div className="flex items-start gap-3 rounded-[8px] border border-jury-fault/40 bg-jury-fault-soft px-3.5 py-3">
          <span aria-hidden="true" className="mt-0.5 h-2.5 w-2.5 shrink-0 rounded-full bg-jury-fault" />
          <div className="flex min-w-0 flex-col gap-0.5">
            <span className="text-[12px] font-semibold uppercase tracking-wide text-jury-fault">Simulated fault active</span>
            {/* Never `truncate` — this is the one piece of text this page must
                never hide. It wraps onto a second line rather than clipping. */}
            <span className="whitespace-normal break-words text-sm font-medium leading-snug text-ink-primary">{faultValue}</span>
          </div>
        </div>
      ) : null}

      {/* No role/aria-live here: a screen reader can still read this grid
          on request (arrow-key/virtual-cursor navigation), it simply never
          triggers an AUTOMATIC re-announcement on its own — that is the sole
          job of the sr-only summary above. */}
      <div className="mission-status-fields">
        {routineFields.map((field) => (
          <div key={field.label} className="flex min-w-0 flex-col gap-0.5">
            <span className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{field.label}</span>
            <span className={clsx("whitespace-normal break-words text-sm font-semibold", fieldTone(field.tone))}>{field.value}</span>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-jury-border-subtle pt-2.5">
        <span className="text-xs leading-snug text-ink-muted sm:max-w-[420px]">
          {view.isReplay ? "Recorded human-data replay" : "Synthetic demonstrator"} · Not live astronaut monitoring
        </span>
        <DemoControlDrawer />
      </div>
    </div>
  );
}
