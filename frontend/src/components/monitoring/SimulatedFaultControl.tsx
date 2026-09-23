"use client";

import { useState } from "react";

import { useMonitoringSession } from "@/components/monitoring/MonitoringSessionContext";
import { formatFaultTypeLabel } from "@/lib/monitoring/formatMonitoringValue";
import { useConfirmedSnapshot } from "@/lib/monitoring/useConfirmedSnapshot";
import type { ReplayFaultTarget, ReplayFaultType } from "@/lib/types";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

const FAULT_TYPES: { value: ReplayFaultType; label: string }[] = [
  { value: "modality_dropout", label: "Modality dropout" },
  { value: "packet_loss", label: "Packet/sample loss" },
  { value: "frozen_sensor", label: "Frozen sensor" },
  { value: "additive_noise", label: "Additive noise" },
  { value: "saturation", label: "Saturation/clipping" },
];
const FAULT_TARGETS: { value: ReplayFaultTarget; label: string }[] = [
  { value: "ppg", label: "PPG" },
  { value: "imu", label: "IMU" },
  { value: "both", label: "PPG + IMU" },
];

// Master-prompt 3 §8.5 — simulated fault injection. Only the backend's own
// target/fault-type enums are exposed (ReplayFaultTarget/ReplayFaultType in
// backend/app/schemas/fault_injection.py); nothing here invents an
// unsupported combination. Disabled entirely outside recorded replay, with
// an explicit reason rather than a silently greyed-out control. No flash,
// pulse, glow, or shake motion; fault-red is reserved for an actually-active
// fault or a failed request, never for the idle control state.
export function SimulatedFaultControl() {
  const isReplay = useDatasetReplayMode();
  const { pending, requestError, configureFault, clearFault } = useMonitoringSession();
  const { snapshot: confirmedLatest, isWaitingForConfirmation } = useConfirmedSnapshot();
  const latestFault = confirmedLatest?.fault_injection;
  const [faultType, setFaultType] = useState<ReplayFaultType>("modality_dropout");
  const [target, setTarget] = useState<ReplayFaultTarget>("ppg");
  const [severity, setSeverity] = useState(1);
  const [seed, setSeed] = useState(0);
  const severityIsConfigurable = faultType === "packet_loss" || faultType === "additive_noise" || faultType === "saturation";
  const active = latestFault?.active ?? false;

  if (!isReplay) {
    return (
      <section aria-labelledby="fault-control-heading" className="rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
        <div className="flex items-center justify-between gap-2">
          <h2 id="fault-control-heading" className="text-sm font-semibold text-ink-primary">Simulated fault injection</h2>
          <span className="rounded-[4px] border border-jury-border-subtle px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-ink-muted">
            Recorded replay only
          </span>
        </div>
        <p className="mt-2 text-xs leading-relaxed text-ink-muted">
          Fault injection is available only for recorded replay because it tests the inference pipeline against
          controlled signal corruption.
        </p>
      </section>
    );
  }

  return (
    <section aria-labelledby="fault-control-heading" className="flex flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="fault-control-heading" className="text-sm font-semibold text-ink-primary">Simulated fault injection</h2>
        <span className="rounded-[4px] border border-jury-border-subtle px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-ink-muted">
          Recorded replay only
        </span>
      </div>

      {isWaitingForConfirmation ? (
        <p role="status" className="rounded-md border border-information/25 bg-information-soft px-3 py-2 text-xs text-information">
          Waiting for a confirmed frame from the selected source.
        </p>
      ) : null}

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <label className="sr-only" htmlFor="fault-type-select">Fault type</label>
        <select
          id="fault-type-select"
          name="faultType"
          value={faultType}
          onChange={(event) => {
            const value = event.target.value as ReplayFaultType;
            setFaultType(value);
            setSeverity(value === "modality_dropout" || value === "frozen_sensor" ? 1 : 0.25);
          }}
          disabled={pending !== null}
          className="rounded-[6px] border border-jury-border-strong bg-surface-2 px-3 py-2 text-xs text-ink-primary disabled:opacity-50"
        >
          {FAULT_TYPES.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
        <label className="sr-only" htmlFor="fault-target-select">Fault target</label>
        <select
          id="fault-target-select"
          name="faultTarget"
          value={target}
          onChange={(event) => setTarget(event.target.value as ReplayFaultTarget)}
          disabled={pending !== null}
          className="rounded-[6px] border border-jury-border-strong bg-surface-2 px-3 py-2 text-xs text-ink-primary disabled:opacity-50"
        >
          {FAULT_TARGETS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
        <label className="flex items-center gap-2 text-xs text-ink-secondary" htmlFor="fault-severity-input">
          Severity
          <input
            id="fault-severity-input"
            name="faultSeverity"
            type="number"
            min={0}
            max={1}
            step={0.05}
            value={severity}
            disabled={!severityIsConfigurable || pending !== null}
            onChange={(event) => setSeverity(Number(event.target.value))}
            className="w-20 rounded-[6px] border border-jury-border-strong bg-surface-2 px-2 py-1.5 text-ink-primary disabled:opacity-40"
          />
        </label>
        <label className="flex items-center gap-2 text-xs text-ink-secondary" htmlFor="fault-seed-input">
          Seed
          <input
            id="fault-seed-input"
            name="faultSeed"
            type="number"
            min={0}
            step={1}
            value={seed}
            disabled={pending !== null}
            onChange={(event) => setSeed(Number(event.target.value))}
            className="w-24 rounded-[6px] border border-jury-border-strong bg-surface-2 px-2 py-1.5 text-ink-primary disabled:opacity-40"
          />
        </label>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={pending !== null}
          onClick={() => void configureFault({ fault_type: faultType, target, severity: severityIsConfigurable ? severity : 1, seed })}
          className="rounded-[6px] border border-experimental/40 bg-experimental-soft px-3 py-1.5 text-xs font-medium text-experimental disabled:opacity-40"
        >
          Apply fault
        </button>
        <button
          type="button"
          disabled={!active || pending !== null}
          onClick={() => void clearFault()}
          className="rounded-[6px] border border-jury-border-strong px-3 py-1.5 text-xs text-ink-secondary disabled:opacity-40"
          title={!active ? "No simulated fault is active to clear." : undefined}
        >
          Clear fault
        </button>
      </div>

      <p className={active ? "text-xs font-medium text-jury-fault" : "text-xs text-ink-muted"}>
        {active
          ? `Simulated fault active — ${latestFault?.target?.toUpperCase()} · ${formatFaultTypeLabel(latestFault?.fault_type)} · severity ${latestFault?.severity}`
          : "No simulated fault is active."}
      </p>
      <p className="text-[11px] leading-relaxed text-ink-muted">
        Applies a simulated interface fault condition. It does not represent a physical sensor failure.
      </p>

      {requestError ? <p role="alert" className="text-xs text-jury-fault">{requestError}</p> : null}
    </section>
  );
}
