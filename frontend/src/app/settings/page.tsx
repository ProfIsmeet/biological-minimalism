"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Info, Settings as SettingsIcon, XCircle } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { DataSourceControl } from "@/components/demos/DataSourceControl";
import { API_BASE_URL, WS_URL } from "@/lib/config";
import { api } from "@/lib/api";

const REDUCE_MOTION_KEY = "biomin:reduce-motion";

export default function SettingsPage() {
  const [reduceMotion, setReduceMotion] = useState(false);
  const [testState, setTestState] = useState<"idle" | "testing" | "ok" | "error">("idle");
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  useEffect(() => {
    const stored = window.localStorage.getItem(REDUCE_MOTION_KEY) === "1";
    setReduceMotion(stored);
    document.documentElement.classList.toggle("reduce-motion", stored);
  }, []);

  function toggleReduceMotion() {
    const next = !reduceMotion;
    setReduceMotion(next);
    document.documentElement.classList.toggle("reduce-motion", next);
    window.localStorage.setItem(REDUCE_MOTION_KEY, next ? "1" : "0");
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
        <Panel title="API Connection" subtitle="Backend endpoints in use" icon={<SettingsIcon size={16} />}>
          <div className="flex flex-col gap-3 text-sm">
            <div className="flex flex-col gap-1">
              <span className="text-[11px] uppercase tracking-wider text-slate-500">REST Base URL</span>
              <span className="tabular-nums-mono text-slate-300">{API_BASE_URL}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[11px] uppercase tracking-wider text-slate-500">WebSocket URL</span>
              <span className="tabular-nums-mono text-slate-300">{WS_URL}</span>
            </div>
            <button
              type="button"
              onClick={testConnection}
              disabled={testState === "testing"}
              className="mt-1 w-fit rounded-lg border border-cyan-400/30 bg-cyan-500/10 px-3.5 py-2 text-xs font-medium text-cyan-300 transition-colors hover:bg-cyan-500/20 disabled:opacity-60"
            >
              {testState === "testing" ? "Testing…" : "Test Connection"}
            </button>
            {testState === "ok" ? (
              <p className="flex items-center gap-1.5 text-xs text-signal-nominal">
                <CheckCircle2 size={14} /> Connected — {latencyMs}ms round-trip.
              </p>
            ) : null}
            {testState === "error" ? (
              <p className="flex items-center gap-1.5 text-xs text-signal-critical">
                <XCircle size={14} /> Could not reach the backend. Is `uvicorn app.main:app` running?
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
            <span className="font-medium text-slate-200">Biological Minimalism</span> — AI-driven minimal sensor architecture for
            autonomous astronaut health monitoring. Prepared for IAC 2026 (Interactive Presentation, IAF/IAA Space Life Sciences
            Symposium).
          </p>
          <p>
            Synthetic demo mode uses the mock engine. PPG-DaLiA replay mode streams previously recorded, synchronized real human channels
            with explicit dataset/subject provenance; it is not live hardware and does not run the trained heart-rate model yet. SHAP views
            apply only to the synthetic physiology scoring functions.
          </p>
          <p>See <span className="tabular-nums-mono">docs/PDD_Biological_Minimalism_IAC2026.md</span> for the full project design document.</p>
        </div>
      </Panel>
    </div>
  );
}
