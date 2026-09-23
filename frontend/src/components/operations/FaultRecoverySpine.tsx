"use client";

import type { OperationalEvent, OperationalEventKind } from "@/lib/monitoring/operationalEvents";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";
import { useOperationalEventStore } from "@/store/operationalEventStore";

type Tone = "fault" | "recovery" | "warmup" | "neutral";

function toneOf(kind: OperationalEventKind): Tone {
  if (kind === "fault_applied" || kind === "disconnected" || kind === "source_error" || kind === "prediction_unavailable") return "fault";
  if (kind === "fault_cleared" || kind === "prediction_recovered" || kind === "prediction_available") return "recovery";
  if (kind === "warmup_started" || kind === "replay_loaded") return "warmup";
  return "neutral";
}

const TONE_STYLE: Record<Tone, { node: string; ring: string; text: string }> = {
  fault: { node: "#D46F70", ring: "rgba(212,111,112,0.25)", text: "text-jury-fault" },
  recovery: { node: "#63BFB7", ring: "rgba(99,191,183,0.25)", text: "text-jury-success" },
  warmup: { node: "#D5A45E", ring: "rgba(213,164,94,0.22)", text: "text-jury-warning" },
  neutral: { node: "#516269", ring: "rgba(81,98,105,0.2)", text: "text-ink-secondary" },
};

function eventTime(event: OperationalEvent): string {
  return new Date(event.clientMs).toISOString().slice(11, 19);
}

/**
 * Prompt 3B §12 — Fault → Recovery Spine. A geometric spine whose nodes are
 * the ACTUAL operational events from `useOperationalEventStore` (populated only
 * by OperationalEventLogWatcher). Fault-class events sit above the spine axis,
 * recovery-class below, so an apply → clear → recover sequence reads as a
 * literal descent back to the baseline. It never fabricates a fault timeline:
 * with no session events it says so.
 */
export function FaultRecoverySpine() {
  const events = useOperationalEventStore((state) => state.events);
  const view = useOperationalViewModel();
  // Fault/recovery-relevant events only, most recent last, capped for layout.
  const relevant = events.filter((e) => toneOf(e.kind) !== "neutral").slice(-9);

  return (
    <section aria-labelledby="fault-spine-heading" className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="fault-spine-heading" className="text-sm font-semibold text-ink-primary">
          Fault &amp; recovery spine
        </h2>
        <span
          className={
            view.faultActive
              ? "rounded-[4px] border border-jury-fault/40 bg-jury-fault-soft px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-jury-fault"
              : "rounded-[4px] border border-jury-border-subtle bg-surface-2 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-ink-muted"
          }
        >
          {view.faultActive ? "Fault active" : "Nominal"}
        </span>
      </div>

      {relevant.length === 0 ? (
        <p className="text-xs text-ink-muted">
          No fault or recovery events in this interface session. Apply a simulated fault to trace the recovery path.
        </p>
      ) : (
        <ol className="relative flex items-stretch gap-0 overflow-x-auto pb-1">
          {/* Baseline spine axis. */}
          {relevant.map((event, i) => {
            const tone = toneOf(event.kind);
            const style = TONE_STYLE[tone];
            const above = tone === "fault" || tone === "warmup";
            return (
              <li key={event.id} className="flex min-w-[92px] flex-1 flex-col items-center">
                {/* Top slot (fault/warm-up rises above the axis). */}
                <div className="flex h-[46px] w-full flex-col items-center justify-end">
                  {above ? (
                    <span className={`mb-1 max-w-[90px] text-center text-[10px] font-medium leading-tight ${style.text}`}>{event.label}</span>
                  ) : null}
                </div>
                {/* Axis row with node + connector. */}
                <div className="relative flex w-full items-center justify-center">
                  {i > 0 ? <span aria-hidden="true" className="absolute left-0 top-1/2 h-px w-1/2 -translate-y-1/2 bg-jury-border-strong" /> : null}
                  {i < relevant.length - 1 ? <span aria-hidden="true" className="absolute right-0 top-1/2 h-px w-1/2 -translate-y-1/2 bg-jury-border-strong" /> : null}
                  <span
                    aria-hidden="true"
                    className="relative z-10 flex h-3.5 w-3.5 rotate-45 items-center justify-center border-2"
                    style={{ borderColor: style.node, background: style.ring }}
                  />
                </div>
                {/* Bottom slot (recovery drops below the axis). */}
                <div className="flex h-[46px] w-full flex-col items-start justify-start">
                  {!above ? (
                    <span className={`mt-1 w-full text-center text-[10px] font-medium leading-tight ${style.text}`}>{event.label}</span>
                  ) : null}
                  <span className="mt-0.5 w-full text-center font-mono text-[9px] text-ink-muted">{eventTime(event)}</span>
                </div>
              </li>
            );
          })}
        </ol>
      )}
      <p className="text-[10px] leading-snug text-ink-muted">
        Built from this session&rsquo;s recorded events only — fault-class above the axis, recovery-class below.
      </p>
    </section>
  );
}
