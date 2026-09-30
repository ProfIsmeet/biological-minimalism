"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Info, Settings as SettingsIcon, XCircle } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { api } from "@/lib/api";
import {
  REDUCE_MOTION_CHANGE_EVENT,
  REDUCE_MOTION_KEY,
  REDUCE_MOTION_OFF,
  REDUCE_MOTION_ON,
  reduceMotionEnabledFromStorage,
} from "@/lib/runtime/reduceMotion";

export function SettingsClient() {
  const [reduceMotion, setReduceMotion] = useState(false);
  const [testState, setTestState] = useState<"idle" | "testing" | "ok" | "error">("idle");
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  useEffect(() => {
    const recomputePersistedPreference = () => {
      setReduceMotion(reduceMotionEnabledFromStorage(window.localStorage.getItem(REDUCE_MOTION_KEY)));
    };
    const onStorage = (event: StorageEvent) => {
      if (event.key === REDUCE_MOTION_KEY || event.key === null) recomputePersistedPreference();
    };
    recomputePersistedPreference();
    window.addEventListener("storage", onStorage);
    window.addEventListener(REDUCE_MOTION_CHANGE_EVENT, recomputePersistedPreference);
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener(REDUCE_MOTION_CHANGE_EVENT, recomputePersistedPreference);
    };
  }, []);

  function toggleReduceMotion() {
    const next = !reduceMotion;
    setReduceMotion(next);
    window.localStorage.setItem(REDUCE_MOTION_KEY, next ? REDUCE_MOTION_ON : REDUCE_MOTION_OFF);
    // Stage 2 A2: the native `storage` event never fires in the tab that made
    // the write, so this same-tab custom event is what lets every mounted
    // `useReducedMotionPreference()` consumer (Framer Motion via
    // MotionConfigProvider, WebGL rotation loops) react immediately instead
    // of only after a reload.
    window.dispatchEvent(new Event(REDUCE_MOTION_CHANGE_EVENT));
  }

  async function testConnection() {
    setTestState("testing");
    const start = performance.now();
    try {
      await api.getLiveMetrics();
      setLatencyMs(Math.round(performance.now() - start));
      setTestState("ok");
    } catch {
      setTestState("error");
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary sm:text-[28px]">Settings</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-ink-secondary">
          Application preferences and a user-safe service reachability check. Operational replay and fault controls live with
          the operational routes, in the Demo controls drawer on Mission Overview.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* HIGH-3: no raw REST/WS URLs, no env vars, and no shell start
            instructions in the public UI. A user-safe reachability check with
            composed product copy. */}
        <Panel title="Telemetry service" subtitle="Operational connection status" icon={<SettingsIcon size={16} />}>
          <div className="flex flex-col gap-3 text-sm">
            <p className="text-xs text-ink-muted">
              Check whether the operational telemetry service is reachable. The explanatory pages (System Brief,
              Experimental Research, Digital Twin) remain readable regardless of this status.
            </p>
            <button
              type="button"
              onClick={testConnection}
              disabled={testState === "testing"}
              className="mt-1 flex min-h-11 w-fit items-center rounded-md border border-information/40 bg-information-soft px-4 text-sm font-medium text-information transition-colors hover:border-information/60 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {testState === "testing" ? "Testing…" : "Test connection"}
            </button>
            {testState === "ok" ? (
              <p className="flex items-center gap-1.5 text-xs text-signal-nominal">
                <CheckCircle2 size={14} /> Telemetry service reachable — {latencyMs}ms round-trip.
              </p>
            ) : null}
            {testState === "error" ? (
              <p className="flex items-center gap-1.5 text-xs text-signal-critical">
                <XCircle size={14} /> The telemetry service is unavailable, so live vitals and replay will not update.
                Check the configured service and try again.
              </p>
            ) : null}
          </div>
        </Panel>

        <Panel title="Accessibility" subtitle="Display preferences" icon={<SettingsIcon size={16} />}>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm text-ink-primary">Reduce Motion</p>
              <p className="text-xs text-ink-muted">Disables gauge, waveform, and panel transition animations across the dashboard.</p>
            </div>
            {/* Stage 8 §18 — the switch was a 24px-tall hit target. It now
                occupies a 44px-tall focusable button with the 24px track
                drawn inside it, so the accessible target meets the minimum
                without changing the visual weight of the control. The track
                colour also moved off raw cyan onto the semantic accent. */}
            <button
              type="button"
              role="switch"
              aria-label="Reduce motion"
              aria-checked={reduceMotion}
              onClick={toggleReduceMotion}
              className="group flex h-11 w-11 shrink-0 items-center justify-center rounded-md outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
            >
              <span
                aria-hidden="true"
                className={`relative block h-6 w-11 rounded-full transition-colors ${reduceMotion ? "bg-final-accent" : "bg-surface-3"}`}
              >
                <span
                  className={`absolute top-0.5 h-5 w-5 rounded-full bg-ink-primary transition-transform ${reduceMotion ? "translate-x-5" : "translate-x-0.5"}`}
                />
              </span>
            </button>
          </div>
        </Panel>
      </div>

      {/* Stage 8 §15 — the operational data-source control (synthetic/replay
          source switching plus subject selection) was removed from Settings.
          It duplicated the Demo controls drawer that the operational routes
          already own, and it was the ONLY reason this preferences page
          mounted a live-feed WebSocket. Removing it lets /settings drop to
          the static runtime tier: no socket, no operational REST, nothing to
          clean up on exit. The controls themselves are unchanged and remain
          available where they belong. */}

      <Panel title="About" subtitle="Project attribution & scope" icon={<Info size={16} />}>
        <div className="flex flex-col gap-2 text-sm leading-relaxed text-ink-secondary">
          <p>
            <span className="font-medium text-ink-primary">Biological Minimalism</span> — an evidence-driven methodology for
            determining the target-specific marginal value of sensing components for autonomous astronaut health monitoring. The
            final selected wearable architecture is <span className="font-medium text-ink-primary">CORE_PLUS_CONTEXT</span>,
            a conditional evidence–burden trade-off, not a unique mathematical optimum. Prepared for IAC 2026
            (Interactive Presentation, IAF/IAA Space Life Sciences Symposium).
          </p>
          <p>
            Synthetic demo mode uses the mock engine. PPG-DaLiA replay mode streams previously recorded, synchronized real human channels
            with explicit dataset/subject provenance; it is not live hardware. Replay heart rate is a PPG + IMU heart-rate estimate
            evaluated on PPG-DaLiA, while unsupported physiology remains unavailable. SHAP views apply only to the synthetic physiology scoring functions.
          </p>
          <p>Refer to the project design document (PDD) for the full methodology and scope.</p>
        </div>
      </Panel>
    </div>
  );
}
