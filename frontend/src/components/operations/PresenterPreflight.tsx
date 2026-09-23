"use client";

import { useState } from "react";
import { AlertTriangle, Check, ChevronDown, CircleHelp, Minus, X } from "lucide-react";

import { useMonitoringSession } from "@/components/monitoring/MonitoringSessionContext";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";
import { derivePresenterPreflight, type PreflightFact, type PreflightState } from "@/lib/monitoring/presenterOps";
import { useMissionStore } from "@/store/missionStore";

/**
 * Prompt-4 §21 — collapsible presenter preflight. Renders the ten independent
 * facts derived by `derivePresenterPreflight` (all truth decisions live there).
 * State is conveyed by BOTH an icon and an explicit text word (§14: never
 * color alone), and "Ready" is never inferred from the absence of an error —
 * the HR-model item is honestly "Unknown — not exposed by current backend
 * contract" because the backend contract does not expose it.
 */

const STATE_META: Record<PreflightState, { word: string; Icon: typeof Check; className: string }> = {
  ready: { word: "Ready", Icon: Check, className: "text-jury-success" },
  "not-ready": { word: "Not ready", Icon: AlertTriangle, className: "text-jury-warning" },
  unavailable: { word: "Unavailable", Icon: X, className: "text-jury-fault" },
  unknown: { word: "Unknown", Icon: CircleHelp, className: "text-ink-secondary" },
  "n/a": { word: "Not applicable", Icon: Minus, className: "text-ink-muted" },
};

function PreflightRow({ fact }: { fact: PreflightFact }) {
  const meta = STATE_META[fact.state];
  const Icon = meta.Icon;
  return (
    <li className="flex items-start justify-between gap-3 py-1.5">
      <div className="min-w-0">
        <p className="text-xs font-medium text-ink-primary">{fact.label}</p>
        <p className="text-[11px] leading-snug text-ink-muted">{fact.detail}</p>
      </div>
      <span className={`flex shrink-0 items-center gap-1 text-[11px] font-semibold ${meta.className}`}>
        <Icon size={12} aria-hidden="true" />
        {meta.word}
      </span>
    </li>
  );
}

export function PresenterPreflight() {
  const [open, setOpen] = useState(false);
  const session = useMonitoringSession();
  const connectionStatus = useMissionStore((state) => state.connectionStatus);
  const view = useOperationalViewModel();

  const inferenceReady =
    view.predictionAvailability === "available"
      ? true
      : view.predictionAvailability === "unavailable_no_prediction"
        ? false
        : null;

  const facts = derivePresenterPreflight({
    sourceStateStatus: session.sourceStateStatus,
    connectionStatus,
    datasetConfigured: session.datasetConfigured,
    subjectListState: session.subjectListState,
    subjects: session.subjects,
    status: session.status,
    inferenceReady,
  });

  const notReadyCount = facts.filter((fact) => fact.state === "not-ready" || fact.state === "unavailable").length;

  return (
    <section aria-labelledby="presenter-preflight-heading" className="rounded-[8px] border border-jury-border-strong bg-surface-1">
      <h3 id="presenter-preflight-heading" className="sr-only">
        Presenter preflight
      </h3>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls="presenter-preflight-body"
        className="flex w-full items-center justify-between gap-2 rounded-[8px] px-3 py-2 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
      >
        <span className="flex items-center gap-2">
          <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-experimental">Presenter preflight</span>
          <span className="text-[11px] text-ink-muted">
            {notReadyCount === 0 ? "no blocking items" : `${notReadyCount} item(s) need attention`}
          </span>
        </span>
        <ChevronDown
          size={14}
          aria-hidden="true"
          className={`shrink-0 text-ink-secondary transition-transform duration-150 ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open ? (
        <div id="presenter-preflight-body" className="border-t border-jury-border-strong px-3 pb-2 pt-1">
          <ul className="divide-y divide-jury-border-subtle/60">
            {facts.map((fact) => (
              <PreflightRow key={fact.id} fact={fact} />
            ))}
          </ul>
          <p className="mt-2 text-[10px] leading-snug text-ink-muted">
            Preflight reflects the current backend contract. Items it cannot authoritatively verify are shown as
            Unknown, never assumed Ready.
          </p>
        </div>
      ) : null}
    </section>
  );
}
