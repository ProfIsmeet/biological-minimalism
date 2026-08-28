"use client";

import { motion } from "framer-motion";

import { confidenceLevel } from "@/lib/format";
import type { DigitalTwinState } from "@/lib/types";

const RING_COLOR: Record<"nominal" | "warning" | "critical", string> = {
  nominal: "#33e0a1",
  warning: "#f5b942",
  critical: "#ff5c66",
};

interface DigitalTwinPanelProps {
  state: DigitalTwinState | null;
  size?: number;
}

/**
 * A CSS/SVG "holographic" rendering of the Digital Twin's four adaptation
 * systems as nested glowing rings around a pulsing core — built with layered
 * SVG + Framer Motion (no 3D engine) to read as dimensional at dashboard
 * scale, per the project's requested tech stack.
 */
export function DigitalTwinPanel({ state, size = 280 }: DigitalTwinPanelProps) {
  const systems = state?.systems ?? [];
  const center = size / 2;
  const ringGap = size / 2 / 6;

  return (
    <div className="flex flex-col items-center gap-5">
      <div className="relative" style={{ width: size, height: size }}>
        <div className="absolute inset-0 rounded-full bg-[radial-gradient(circle_at_50%_50%,rgba(79,216,232,0.16),transparent_70%)]" />

        <motion.div
          className="absolute inset-2 rounded-full border border-dashed border-cyan-400/20"
          animate={{ rotate: 360 }}
          transition={{ duration: 26, repeat: Infinity, ease: "linear" }}
        />
        <motion.div
          className="absolute inset-6 rounded-full border border-dotted border-cyan-400/15"
          animate={{ rotate: -360 }}
          transition={{ duration: 34, repeat: Infinity, ease: "linear" }}
        />

        <svg width={size} height={size} className="absolute inset-0 -rotate-90">
          {systems.map((system, index) => {
            const radius = center - 14 - index * ringGap;
            const circumference = 2 * Math.PI * radius;
            const level = confidenceLevel(system.current_score);
            const color = RING_COLOR[level];
            const offset = circumference * (1 - system.current_score / 100);
            return (
              <g key={system.system}>
                <circle cx={center} cy={center} r={radius} stroke="rgba(255,255,255,0.05)" strokeWidth={6} fill="none" />
                <motion.circle
                  cx={center}
                  cy={center}
                  r={radius}
                  stroke={color}
                  strokeWidth={6}
                  strokeLinecap="round"
                  fill="none"
                  strokeDasharray={circumference}
                  initial={false}
                  animate={{ strokeDashoffset: offset }}
                  transition={{ type: "spring", stiffness: 50, damping: 15 }}
                  style={{ filter: `drop-shadow(0 0 5px ${color}90)` }}
                />
              </g>
            );
          })}
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5">
          <motion.div
            className="h-3 w-3 rounded-full bg-cyan-300"
            animate={{ boxShadow: ["0 0 8px 2px rgba(79,216,232,0.6)", "0 0 20px 8px rgba(79,216,232,0.35)", "0 0 8px 2px rgba(79,216,232,0.6)"] }}
            transition={{ duration: 2.4, repeat: Infinity }}
          />
          <span className="tabular-nums-mono mt-2 text-3xl font-bold text-slate-100">
            {state ? state.overall_adaptation.toFixed(0) : "—"}
            <span className="text-base text-slate-500">%</span>
          </span>
          <span className="text-[11px] uppercase tracking-wider text-slate-500">Overall Adaptation</span>
        </div>
      </div>

      <div className="grid w-full grid-cols-2 gap-2">
        {systems.map((system) => {
          const level = confidenceLevel(system.current_score);
          return (
            <div key={system.system} className="flex items-center gap-2 rounded-lg border border-white/5 bg-white/[0.02] px-2.5 py-2">
              <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: RING_COLOR[level] }} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[11px] text-slate-400">{system.system}</p>
                <p className="tabular-nums-mono text-sm font-semibold text-slate-100">{system.current_score.toFixed(0)}%</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
