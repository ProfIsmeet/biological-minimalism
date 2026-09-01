"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";
import { RefreshCw, Sparkles } from "lucide-react";

import { Panel } from "@/components/ui/Panel";
import { api } from "@/lib/api";
import type { AIExplanation } from "@/lib/types";
import { useMissionStore } from "@/store/missionStore";

const DIRECTION_COLOR = {
  increased_risk: "#ff5c66",
  decreased_risk: "#33e0a1",
  neutral: "#5a6786",
} as const;

interface ExplanationPanelProps {
  target: "ai_confidence" | "fatigue_risk";
  title: string;
  subtitle: string;
  refreshIntervalMs?: number;
}

export function ExplanationPanel({ target, title, subtitle, refreshIntervalMs = 4000 }: ExplanationPanelProps) {
  const isReplay = useMissionStore((state) => state.latest?.source.source_type === "dataset_replay");
  const [explanation, setExplanation] = useState<AIExplanation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (isReplay) {
      setExplanation(null);
      setError(null);
      return;
    }
    setLoading(true);
    try {
      const result = await api.getExplanation(target);
      setExplanation(result);
      setError(null);
    } catch {
      setError("SHAP explanation unavailable — is the backend running?");
    } finally {
      setLoading(false);
    }
  }, [isReplay, target]);

  useEffect(() => {
    if (isReplay) {
      setExplanation(null);
      return;
    }
    load();
    const id = setInterval(load, refreshIntervalMs);
    return () => clearInterval(id);
  }, [isReplay, load, refreshIntervalMs]);

  const maxAbs = Math.max(1, ...(explanation?.contributions.map((c) => Math.abs(c.shap_value)) ?? [1]));

  return (
    <Panel
      title={title}
      subtitle={subtitle}
      icon={<Sparkles size={16} />}
      actions={
        <button
          type="button"
          onClick={load}
          disabled={loading}
          aria-label="Refresh explanation"
          className="rounded-md p-1.5 text-slate-500 transition-colors hover:bg-white/5 hover:text-slate-200 disabled:opacity-50"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      }
    >
      {isReplay ? (
        <p className="text-sm text-slate-500">Unavailable in replay mode — no trained-model inference is connected yet.</p>
      ) : error ? (
        <p className="text-sm text-signal-critical">{error}</p>
      ) : !explanation ? (
        <p className="text-sm text-slate-500">Computing SHAP attribution…</p>
      ) : (
        <div className="flex flex-col gap-4">
          <motion.p
            key={explanation.summary_text}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-lg border border-cyan-400/15 bg-cyan-500/5 px-3.5 py-3 text-sm leading-relaxed text-slate-200"
          >
            {explanation.summary_text}
          </motion.p>

          <div className="flex flex-col gap-2.5">
            <p className="text-[11px] uppercase tracking-wider text-slate-500">SHAP Feature Contributions</p>
            {explanation.contributions.map((contribution) => {
              const color = DIRECTION_COLOR[contribution.direction];
              const widthPct = (Math.abs(contribution.shap_value) / maxAbs) * 50;
              const isPositive = contribution.shap_value >= 0;
              return (
                <div key={contribution.feature} className="flex items-center gap-3 text-xs">
                  <span className="w-36 shrink-0 truncate text-slate-400">{contribution.feature}</span>
                  <div className="relative h-3 flex-1">
                    <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-white/10" />
                    <motion.div
                      className={clsx("absolute top-0 h-full rounded-sm")}
                      style={{ backgroundColor: color, left: isPositive ? "50%" : undefined, right: isPositive ? undefined : "50%" }}
                      initial={false}
                      animate={{ width: `${widthPct}%` }}
                      transition={{ type: "spring", stiffness: 90, damping: 20 }}
                    />
                  </div>
                  <span className="tabular-nums-mono w-14 shrink-0 text-right text-slate-500">
                    {contribution.shap_value >= 0 ? "+" : ""}
                    {contribution.shap_value.toFixed(1)}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-between border-t border-white/5 pt-3 text-[11px] text-slate-500">
            <span>Baseline (expected value): {explanation.base_value.toFixed(1)}</span>
            <span>Current: {explanation.predicted_value.toFixed(1)}</span>
          </div>
        </div>
      )}
    </Panel>
  );
}
