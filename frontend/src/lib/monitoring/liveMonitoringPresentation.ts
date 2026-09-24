import type { TelemetryAvailability } from "@/lib/monitoring/telemetryAvailability";

export interface IdentityContextDisplay {
  label: string;
  value: string;
  retained: boolean;
}

export function deriveIdentityContextDisplay(params: {
  kind: "Dataset" | "Subject";
  telemetry: TelemetryAvailability;
  currentValue: string | null;
  retainedValue: string | null;
}): IdentityContextDisplay {
  const retained = params.telemetry !== "active";
  if (retained) {
    const contextValue = params.currentValue ?? params.retainedValue;
    return {
      label: `${params.kind} context`,
      value: contextValue
        ? `${contextValue} — retained configuration context, not current telemetry`
        : `No retained ${params.kind.toLowerCase()} configuration`,
      retained: true,
    };
  }
  return {
    label: params.kind,
    value: params.currentValue ?? (params.kind === "Dataset" ? "Dataset unavailable" : "No subject selected"),
    retained: false,
  };
}
