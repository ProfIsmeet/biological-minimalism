"use client";

import { useCallback, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { RotateCcw, SlidersHorizontal, X } from "lucide-react";

import { ReplaySessionControl } from "@/components/monitoring/ReplaySessionControl";
import { SimulatedFaultControl } from "@/components/monitoring/SimulatedFaultControl";
import { useMonitoringSession } from "@/components/monitoring/MonitoringSessionContext";
import { PresenterPreflight } from "@/components/operations/PresenterPreflight";
import { summariseDemoReset, type DemoResetResult } from "@/lib/monitoring/presenterOps";
import { useModalDialog } from "@/lib/runtime/useModalDialog";
import { useMissionUiStore } from "@/store/missionUiStore";
import { useOperationalEventStore } from "@/store/operationalEventStore";

/**
 * Master prompt 3 §17 / Prompt-4 §10, §21, §22 / Prompt-4A MEDIUM-1, HIGH-2 —
 * demonstration controls in an accessible modal slide-over.
 *
 * Stage 2 A3: the modal isolation behavior (portal to `document.body`, full
 * Tab/Shift+Tab containment, Escape, scroll lock, background `inert` +
 * `aria-hidden` with exact restoration, focus restoration to the trigger,
 * route-change-safe cleanup) now lives once in the shared
 * `useModalDialog()` hook (lib/runtime/useModalDialog.ts) — reused verbatim
 * here and by the mobile "More" sheet (MobileNav.tsx) instead of being
 * reimplemented per dialog.
 *
 * HIGH-2 reset: `resetting` is cleared in `finally`, and the announcement is
 * derived from `summariseDemoReset`, which never claims success on an
 * unexpected failure.
 */

export function DemoControlDrawer() {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  const session = useMonitoringSession();
  const clearEventHistory = useOperationalEventStore((state) => state.clear);
  const setSelectedModality = useMissionUiStore((state) => state.setSelectedModality);
  const [resetting, setResetting] = useState(false);
  const [resetAnnouncement, setResetAnnouncement] = useState("");
  const [resetFailed, setResetFailed] = useState(false);

  // Focus is restored to the trigger by useModalDialog's inert-cleanup
  // effect, AFTER the background `inert` is removed — focusing the trigger
  // here would be a no-op because its ancestor is still inert at this instant.
  const close = useCallback(() => {
    setOpen(false);
  }, []);

  useModalDialog({ open, onClose: close, panelRef, triggerRef, overlayRef });

  // §22 / HIGH-2 — one-click demo reset. Backend steps run through the session
  // (which reports per-step failure); the non-backend parts (event log,
  // modality, scroll) run after they resolve. `resetting` is cleared in
  // `finally`, and an unexpected throw is summarised honestly (never "complete").
  const handleReset = useCallback(async () => {
    if (resetting) return;
    setResetting(true);
    setResetAnnouncement("");
    let result: DemoResetResult = { ok: false, ranSteps: [], failedSteps: [] };
    try {
      result = await session.resetDemoState();
      clearEventHistory();
      setSelectedModality("PPG");
      if (typeof window !== "undefined") window.scrollTo({ top: 0, behavior: "auto" });
    } catch {
      result = { ok: false, ranSteps: [], failedSteps: [] };
    } finally {
      setResetFailed(!result.ok);
      setResetAnnouncement(summariseDemoReset(result));
      setResetting(false);
    }
  }, [resetting, session, clearEventHistory, setSelectedModality]);

  const overlay = (
    <div ref={overlayRef} className="fixed inset-0 z-50 flex justify-end">
      <button
        type="button"
        aria-label="Close demonstration controls"
        onClick={close}
        className="absolute inset-0 bg-black/50"
      />
      <div
        ref={panelRef}
        id="demo-control-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="demo-control-drawer-heading"
        tabIndex={-1}
        className="relative flex h-full w-full max-w-sm flex-col gap-4 overflow-y-auto border-l border-jury-border-strong bg-canvas p-4 shadow-2xl outline-none sm:p-5"
      >
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.1em] text-experimental">Demonstration controls</p>
            <h2 id="demo-control-drawer-heading" className="mt-1 text-lg font-semibold text-ink-primary">
              Source, replay &amp; fault
            </h2>
            <p className="mt-1 text-xs leading-relaxed text-ink-muted">
              These controls operate the demonstration interface only. Closing this panel does not reset source or
              fault state.
            </p>
          </div>
          <button
            type="button"
            onClick={close}
            aria-label="Close demonstration controls"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[6px] border border-jury-border-strong text-ink-secondary hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
          >
            <X size={15} aria-hidden="true" />
          </button>
        </div>

        <PresenterPreflight />

        <div className="rounded-[8px] border border-jury-border-strong bg-surface-1 p-3">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs font-semibold text-ink-primary">Reset demo state</p>
              <p className="mt-0.5 text-[11px] leading-snug text-ink-muted">
                Return replay to its start at 1×, clear any active fault and the session event log, and reset the
                selected modality to PPG. Keeps the current source and subject.
              </p>
            </div>
            <button
              type="button"
              onClick={handleReset}
              disabled={resetting}
              className="flex h-9 shrink-0 items-center gap-1.5 rounded-[6px] border border-jury-border-strong px-3 text-xs font-semibold text-ink-secondary transition-colors duration-150 hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC] disabled:opacity-40"
            >
              <RotateCcw size={13} aria-hidden="true" />
              {resetting ? "Resetting…" : "Reset"}
            </button>
          </div>
          <p
            role="status"
            aria-live="polite"
            className={`mt-2 min-h-[1rem] text-[11px] ${resetFailed ? "text-jury-fault" : "text-ink-muted"}`}
          >
            {resetAnnouncement}
          </p>
        </div>

        <ReplaySessionControl />
        <SimulatedFaultControl />
      </div>
    </div>
  );

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls="demo-control-drawer"
        className="flex h-9 shrink-0 items-center gap-1.5 rounded-[6px] border border-jury-border-strong px-3 text-xs font-semibold text-ink-secondary transition-colors duration-150 hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
      >
        <SlidersHorizontal size={13} aria-hidden="true" />
        Demo controls
      </button>

      {open && typeof document !== "undefined" ? createPortal(overlay, document.body) : null}
    </>
  );
}
