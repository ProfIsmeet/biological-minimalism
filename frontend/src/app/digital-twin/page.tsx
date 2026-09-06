"use client";

import { useEffect, useState } from "react";
import { Orbit } from "lucide-react";

import { DigitalTwinDaySlider } from "@/components/demos/DigitalTwinDaySlider";
import { DigitalTwinPanel } from "@/components/panels/DigitalTwinPanel";
import { Panel } from "@/components/ui/Panel";
import { confidenceLevel } from "@/lib/format";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/lib/api";
import type { DigitalTwinState } from "@/lib/types";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

export default function DigitalTwinPage() {
  const [day, setDay] = useState(1);
  const [state, setState] = useState<DigitalTwinState | null>(null);
  const [loading, setLoading] = useState(false);
  const isReplay = useDatasetReplayMode();

  useEffect(() => {
    if (isReplay) {
      setState(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    api
      .getDigitalTwin(day)
      .then((result) => {
        if (!cancelled) setState(result);
      })
      .catch(() => {
        if (!cancelled) setState(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [day, isReplay]);

  if (isReplay) {
    return (
      <div className="flex flex-col gap-5">
        <div>
          <h1 className="text-lg font-semibold text-slate-100">Digital Twin</h1>
          <p className="text-sm text-slate-500">REAL RECORDED DATA — REPLAY MODE</p>
        </div>
        <Panel title="Adaptation State" subtitle="Unavailable during recorded-data replay" icon={<Orbit size={16} />}>
          <p className="text-sm leading-relaxed text-slate-500">
            Digital Twin unavailable during recorded-data replay until real personalized inference is implemented.
          </p>
        </Panel>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Digital Twin</h1>
        <p className="text-sm text-slate-500">
          Demo — Digital Twin Evolution. A <span className="text-slate-400">synthetic, conceptual</span> illustration of a
          <em> proposed</em> personalized baseline: the model is architecture/reference code only, untrained and not validated.
          Move the slider to see the illustrative adaptation across a simulated 30-day mission.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Panel title="Adaptation State" subtitle={state?.milestone_label ?? "Loading…"} icon={<Orbit size={16} />} className="lg:col-span-2">
          <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:justify-around">
            <DigitalTwinPanel state={state} size={320} />
            <div className="flex w-full max-w-sm flex-col gap-4">
              <div className="rounded-lg border border-white/5 bg-white/[0.02] p-4">
                <p className="mb-2 text-[11px] uppercase tracking-wider text-slate-500">Twin Narrative</p>
                <p className={loading ? "text-sm text-slate-500" : "text-sm leading-relaxed text-slate-200"}>
                  {state?.narrative ?? "Loading digital twin narrative…"}
                </p>
              </div>
              {state ? (
                <StatusBadge level={confidenceLevel(state.overall_adaptation)} label={`${state.overall_adaptation.toFixed(0)}% Adapted`} />
              ) : null}
            </div>
          </div>
        </Panel>

        <Panel title="Mission Day" subtitle="Day 1 · 5 · 12 · 30 milestones" icon={<Orbit size={16} />}>
          <DigitalTwinDaySlider day={day} onChange={setDay} />
          <p className="mt-4 text-xs leading-relaxed text-slate-500">
            The Digital Twin learns a personalized baseline over the first 48–72 hours, then continuously tracks deviation across four
            physiological systems as the simulated mission progresses.
          </p>
        </Panel>
      </div>
    </div>
  );
}
