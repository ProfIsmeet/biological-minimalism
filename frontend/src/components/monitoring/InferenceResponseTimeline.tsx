"use client";

// Master-prompt §8.7 — inference response timeline. The frontend does not
// retain a bounded event-history buffer (missionStore keeps a rolling
// snapshot window for trend charts, not a discrete typed event log), so this
// renders the honest disclosure rather than fabricating timestamps from
// render time or reusing the trend history as if it were an event log.
export function InferenceResponseTimeline() {
  return (
    <section aria-labelledby="inference-response-heading" className="rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <h2 id="inference-response-heading" className="text-sm font-semibold text-ink-primary">
        Inference response
      </h2>
      <p className="mt-2 text-xs leading-relaxed text-ink-muted">
        Event history is not retained by the current frontend session. When authoritative source availability is active,
        the source strip, HR inference panel, and fault control reflect the confirmed current window. Otherwise they
        fail closed as unavailable; they do not reconstruct a timeline of past replay, fault, or inference events.
      </p>
    </section>
  );
}
