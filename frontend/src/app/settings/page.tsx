"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Info, Settings as SettingsIcon, XCircle } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { DataSourceControl } from "@/components/demos/DataSourceControl";
import { api } from "@/lib/api";
import {
  REDUCE_MOTION_KEY,
  REDUCE_MOTION_OFF,
  REDUCE_MOTION_ON,
  reduceMotionEnabledFromStorage,
} from "@/lib/runtime/reduceMotion";

export default function SettingsPage() {
  const [reduceMotion, setReduceMotion] = useState(false);
  const [testState, setTestState] = useState<"idle" | "testing" | "ok" | "error">("idle");
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  useEffect(() => {
    // HIGH-1: read through the shared predicate so Settings and the boot script
    // agree on the accepted values.
    const stored = reduceMotionEnabledFromStorage(window.localStorage.getItem(REDUCE_MOTION_KEY));
    setReduceMotion(stored);
    document.documentElement.classList.toggle("reduce-motion", stored);
  }, []);

  function toggleReduceMotion() {
    const next = !reduceMotion;
    setReduceMotion(next);
    document.documentElement.classList.toggle("reduce-motion", next);
    window.localStorage.setItem(REDUCE_MOTION_KEY, next ? REDUCE_MOTION_ON : REDUCE_MOTION_OFF);
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
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Settings</h1>
        <p className="text-sm text-slate-500">Connection diagnostics, accessibility preferences, and project attribution.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* HIGH-3: no raw REST/WS URLs, no env vars, and no shell start
            instructions in the public UI. A user-safe reachability check with
            composed product copy. */}
        <Panel title="Telemetry service" subtitle="Operational connection status" icon={<SettingsIcon size={16} />}>
          <div className="flex flex-col gap-3 text-sm">
            <p className="text-xs text-slate-500">
              Check whether the operational telemetry service is reachable. The explanatory pages (System Brief,
              Experimental Research, Digital Twin) remain readable regardless of this status.
            </p>
            <button
              type="button"
              onClick={testConnection}
              disabled={testState === "testing"}
              className="mt-1 w-fit rounded-lg border border-cyan-400/30 bg-cyan-500/10 px-3.5 py-2 text-xs font-medium text-cyan-300 transition-colors hover:bg-cyan-500/20 disabled:opacity-60"
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
              <p className="text-sm text-slate-200">Reduce Motion</p>
              <p className="text-xs text-slate-500">Disables gauge, waveform, and panel transition animations across the dashboard.</p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={reduceMotion}
              onClick={toggleReduceMotion}
              className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${reduceMotion ? "bg-cyan-500" : "bg-white/10"}`}
            >
              <span
                className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${reduceMotion ? "translate-x-5" : "translate-x-0.5"}`}
              />
            </button>
          </div>
        </Panel>
      </div>

      <DataSourceControl />

      <Panel title="About" subtitle="Project attribution & scope" icon={<Info size={16} />}>
        <div className="flex flex-col gap-2 text-sm leading-relaxed text-slate-400">
          <p>
            <span className="font-medium text-slate-200">Biological Minimalism</span> — an evidence-driven methodology for
            determining the target-specific marginal value of sensing components for autonomous astronaut health monitoring. The
            final selected wearable architecture is <span className="font-medium text-slate-200">CORE_PLUS_CONTEXT</span>,
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
