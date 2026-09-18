"use client";

// Master-prompt §8.7 — inference response timeline. The frontend does not
// retain a bounded event-history buffer (missionStore keeps a rolling
// snapshot window for trend charts, not a discrete typed event log), so this
// renders the honest disclosure rather than fabricating timestamps from
// render time or reusing the trend history as if it were an event log.
export function InferenceResponseTimeline() {
  return (
    <section aria-labelledby="inference-response-heading" className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
      <h2 id="inference-response-heading" className="text-sm font-semibold text-slate-200">
        Inference response
      </h2>
      <p className="mt-2 text-xs leading-relaxed text-slate-500">
        Event history is not retained by the current frontend session. The source strip, HR inference panel, and fault
        control above always reflect the current window; they do not reconstruct a timeline of past replay, fault, or
        inference events.
      </p>
    </section>
  );
}
