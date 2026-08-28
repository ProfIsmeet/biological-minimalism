"use client";

import { motion } from "framer-motion";
import clsx from "clsx";

import type { StatusLevel } from "@/components/ui/StatusBadge";

const COLOR: Record<StatusLevel, string> = {
  nominal: "#33e0a1",
  warning: "#f5b942",
  critical: "#ff5c66",
  offline: "#5a6786",
};

interface RadialGaugeProps {
  value: number;
  max?: number;
  label: string;
  level?: StatusLevel;
  size?: number;
  suffix?: string;
}

export function RadialGauge({ value, max = 100, label, level = "nominal", size = 132, suffix = "%" }: RadialGaugeProps) {
  const radius = size / 2 - 10;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(max, value));
  const progress = circumference * (1 - clamped / max);
  const color = COLOR[level];

  return (
    <div className="flex flex-col items-center gap-2" role="img" aria-label={`${label}: ${clamped.toFixed(0)}${suffix}`}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={radius} stroke="rgba(255,255,255,0.06)" strokeWidth={9} fill="none" />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={9}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={false}
            animate={{ strokeDashoffset: progress }}
            transition={{ type: "spring", stiffness: 60, damping: 16 }}
            style={{ filter: `drop-shadow(0 0 6px ${color}80)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={clsx("tabular-nums-mono text-2xl font-bold")} style={{ color }}>
            {clamped.toFixed(0)}
            <span className="text-sm">{suffix}</span>
          </span>
        </div>
      </div>
      <span className="text-center text-[11px] uppercase tracking-wider text-slate-400">{label}</span>
    </div>
  );
}
