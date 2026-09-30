"use client";

import { ShieldCheck } from "lucide-react";

import { LinearMeter } from "@/components/ui/LinearMeter";
import { Panel } from "@/components/ui/Panel";
import { RadialGauge } from "@/components/ui/RadialGauge";
import { titleCase } from "@/lib/format";
import { deriveConfidenceDisplay } from "@/lib/monitoring/insightDisplay";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

// Prompt-2B corrective §4.3: synthetic AI-confidence values must only ever
// come from a confirmed synthetic snapshot — a late synthetic frame must
// not populate this panel while replay is the REST-authoritative source.
export function AIConfidencePanel() {
  const isReplay = useDatasetReplayMode();
  const { snapshot: latest, isWaitingForConfirmation } = useConfirmedSnapshot();
  const confidence = isReplay ? undefined : latest?.ai_confidence;
  const overall = deriveConfidenceDisplay(confidence?.overall_confidence);

  const entries = Object.entries(confidence?.sensor_contribution ?? {}).sort((a, b) => b[1] - a[1]);

  return (
    <Panel
      title={isReplay ? "AI confidence" : "Synthetic confidence"}
      // Stage 8 §13 — a synthetic-only quantity must say so in its own
      // subtitle, not only in surrounding page copy. The former subtitle
      // ("Sensor fusion trust & contribution") read as a real fusion metric.
      subtitle={isReplay ? "Not emitted by the replay heart-rate model" : "Synthetic demo engine — not a model confidence"}
      icon={<ShieldCheck size={16} />}
    >
      {isReplay ? (
        <p className="text-sm leading-relaxed text-ink-secondary">
          Unavailable for replay inference. The PPG + IMU heart-rate estimate has no predictive confidence or uncertainty output.
        </p>
      ) : isWaitingForConfirmation ? (
        <p className="text-sm leading-relaxed text-ink-secondary">Waiting for a confirmed frame from the selected source.</p>
      ) : <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-start sm:gap-6">
        {overall.kind === "available" ? (
          <RadialGauge
            value={overall.value}
            label="Overall Confidence"
            level={overall.level}
          />
        ) : (
          <div
            role="status"
            aria-label="Overall Confidence: Unavailable"
            className="flex min-h-[132px] min-w-[132px] flex-col items-center justify-center gap-2 rounded-full border border-signal-offline/30 text-center"
          >
            <span className="text-sm font-semibold text-signal-offline">Unavailable</span>
            <span className="max-w-[104px] text-xs text-ink-muted">No confidence value reported</span>
          </div>
        )}
        <div className="flex w-full flex-1 flex-col gap-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Synthetic sensor contribution</p>
          {entries.length === 0 ? (
            <p className="text-sm text-ink-secondary">Awaiting telemetry…</p>
          ) : (
            entries.map(([sensor, value]) => (
              <LinearMeter key={sensor} label={titleCase(sensor)} value={value} level="nominal" valueLabel={`${value.toFixed(0)}%`} />
            ))
          )}
        </div>
      </div>}
    </Panel>
  );
}
