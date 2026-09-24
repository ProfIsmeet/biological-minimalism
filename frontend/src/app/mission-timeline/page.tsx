"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CalendarClock } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { TrendPanel } from "@/components/panels/TrendPanel";
import { api } from "@/lib/api";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

const MILESTONE_DAYS = [1, 5, 12, 30];
const CONCEPTUAL_MARKERS = [
  "Conceptual initialization checkpoint",
  "Conceptual data-interface checkpoint",
  "Conceptual architecture-review checkpoint",
  "Conceptual evidence-planning checkpoint",
];

type TimelinePayloadState = "loading" | "available" | "unavailable" | "not_applicable";

export default function MissionTimelinePage() {
  const [payloadState, setPayloadState] = useState<TimelinePayloadState>("loading");
  const isReplay = useDatasetReplayMode();

  useEffect(() => {
    if (isReplay) {
      setPayloadState("not_applicable");
      return;
    }
    setPayloadState("loading");
    let cancelled = false;
    Promise.all(MILESTONE_DAYS.map((day) => api.getDigitalTwin(day)))
      .then(() => {
        if (!cancelled) setPayloadState("available");
      })
      .catch(() => {
        if (!cancelled) setPayloadState("unavailable");
      });
    return () => {
      cancelled = true;
    };
  }, [isReplay]);

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Mission Timeline</h1>
        <p className="text-sm text-slate-500">Circadian stability over the live session, with conceptual architecture checkpoints.</p>
      </div>

      <div role="note" className="rounded-lg border border-slate-700 bg-slate-900/60 px-4 py-3">
        <p className="text-sm font-semibold text-slate-200">Digital Twin boundary</p>
        <p className="mt-1 text-sm leading-relaxed text-slate-400">
          Architecture only · untrained · unvalidated · not personalized. These checkpoints are conceptual and do not
          report physiological change, prediction, clinical readiness, or flight qualification.
        </p>
      </div>

      <TrendPanel
        title="Circadian Timeline"
        subtitle="Circadian stability over the live session"
        icon={<CalendarClock size={16} />}
        color="#a78bfa"
        unit="/ 100"
        domain={[0, 100]}
        metric="circadian_stability"
      />

      <Panel title="Conceptual Mission Milestones" subtitle="Scenario markers · Day 1 · 5 · 12 · 30" icon={<CalendarClock size={16} />}>
        <div className="relative">
          <div className="absolute left-0 right-0 top-5 hidden h-px bg-white/10 sm:block" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            {MILESTONE_DAYS.map((day, index) => (
              <motion.div
                key={day}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.08 }}
                className="relative flex flex-col gap-2 rounded-lg border border-white/5 bg-white/[0.02] p-4"
              >
                <div className="flex items-center gap-2">
                  <span className="relative z-10 flex h-2.5 w-2.5 rounded-full bg-cyan-400" />
                  <span className="text-xs font-semibold text-slate-200">Day {day}</span>
                </div>
                <p className="text-xs font-medium text-slate-400">Conceptual marker — not a measured outcome</p>
                <p className="text-xs leading-relaxed text-slate-500">{CONCEPTUAL_MARKERS[index]}</p>
              </motion.div>
            ))}
          </div>
          <p role="status" className="mt-4 text-xs leading-relaxed text-slate-500">
            {payloadState === "loading"
              ? "Checking conceptual scenario availability…"
              : payloadState === "available"
                ? "Legacy scenario payload received; quantitative fields are intentionally suppressed because they have no defensible user-facing interpretation."
                : payloadState === "unavailable"
                  ? "Conceptual scenario data unavailable; no model state is inferred."
                  : "Recorded replay does not populate Digital Twin state; no model state is inferred."}
          </p>
        </div>
      </Panel>
    </div>
  );
}
