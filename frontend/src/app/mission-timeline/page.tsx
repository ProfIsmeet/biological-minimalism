"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CalendarClock } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { TrendPanel } from "@/components/panels/TrendPanel";
import { confidenceLevel } from "@/lib/format";
import { api } from "@/lib/api";
import type { DigitalTwinState } from "@/lib/types";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

const MILESTONE_DAYS = [1, 5, 12, 30];

export default function MissionTimelinePage() {
  const [milestones, setMilestones] = useState<DigitalTwinState[]>([]);
  const isReplay = useDatasetReplayMode();

  useEffect(() => {
    if (isReplay) {
      setMilestones([]);
      return;
    }
    let cancelled = false;
    Promise.all(MILESTONE_DAYS.map((day) => api.getDigitalTwin(day)))
      .then((results) => {
        if (!cancelled) setMilestones(results);
      })
      .catch(() => {
        if (!cancelled) setMilestones([]);
      });
    return () => {
      cancelled = true;
    };
  }, [isReplay]);

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Mission Timeline</h1>
        <p className="text-sm text-slate-500">Circadian stability over the live session, and the Digital Twin&apos;s key adaptation milestones.</p>
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

      <Panel title="Adaptation Milestones" subtitle="Day 1 · 5 · 12 · 30" icon={<CalendarClock size={16} />}>
        {isReplay ? (
          <p className="text-sm leading-relaxed text-slate-500">
            Digital Twin unavailable during recorded-data replay until real personalized inference is implemented.
          </p>
        ) : (
        <div className="relative">
          <div className="absolute left-0 right-0 top-5 hidden h-px bg-white/10 sm:block" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            {(milestones.length ? milestones : MILESTONE_DAYS.map(() => null)).map((milestone, index) => (
              <motion.div
                key={MILESTONE_DAYS[index]}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.08 }}
                className="relative flex flex-col gap-2 rounded-lg border border-white/5 bg-white/[0.02] p-4"
              >
                <div className="flex items-center gap-2">
                  <span className="relative z-10 flex h-2.5 w-2.5 rounded-full bg-cyan-400" />
                  <span className="text-xs font-semibold text-slate-200">Day {MILESTONE_DAYS[index]}</span>
                </div>
                {milestone ? (
                  <>
                    <StatusBadge level={confidenceLevel(milestone.overall_adaptation)} label={`${milestone.overall_adaptation.toFixed(0)}% Adapted`} />
                    <p className="text-xs leading-relaxed text-slate-500">{milestone.narrative}</p>
                  </>
                ) : (
                  <p className="text-xs text-slate-600">Loading…</p>
                )}
              </motion.div>
            ))}
          </div>
        </div>
        )}
      </Panel>
    </div>
  );
}
