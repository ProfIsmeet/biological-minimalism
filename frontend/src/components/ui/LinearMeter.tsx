"use client";

import { motion } from "framer-motion";
import clsx from "clsx";

import type { StatusLevel } from "@/components/ui/StatusBadge";

const COLOR: Record<StatusLevel, string> = {
  nominal: "bg-signal-nominal",
  warning: "bg-signal-warning",
  critical: "bg-signal-critical",
  offline: "bg-signal-offline",
};

interface LinearMeterProps {
  label: string;
  value: number;
  max?: number;
  level?: StatusLevel;
  valueLabel?: string;
}

export function LinearMeter({ label, value, max = 100, level = "nominal", valueLabel }: LinearMeterProps) {
  const clamped = Math.max(0, Math.min(max, value));
  const pct = (clamped / max) * 100;

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="tabular-nums-mono font-medium text-slate-200">{valueLabel ?? `${clamped.toFixed(0)}`}</span>
      </div>
      <div
        className="h-1.5 w-full overflow-hidden rounded-full bg-white/5"
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={label}
      >
        <motion.div
          className={clsx("h-full rounded-full", COLOR[level])}
          initial={false}
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 90, damping: 20 }}
        />
      </div>
    </div>
  );
}
