import clsx from "clsx";

export type StatusLevel = "nominal" | "warning" | "critical" | "offline";

const STYLES: Record<StatusLevel, string> = {
  nominal: "bg-signal-nominal/10 text-signal-nominal border-signal-nominal/30",
  warning: "bg-signal-warning/10 text-signal-warning border-signal-warning/30",
  critical: "bg-signal-critical/10 text-signal-critical border-signal-critical/30",
  offline: "bg-signal-offline/10 text-signal-offline border-signal-offline/30",
};

const LABELS: Record<StatusLevel, string> = {
  nominal: "System Nominal",
  warning: "Warning",
  critical: "Critical",
  offline: "Offline",
};

interface StatusBadgeProps {
  level: StatusLevel;
  label?: string;
  pulse?: boolean;
  className?: string;
}

export function StatusBadge({ level, label, pulse = false, className }: StatusBadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-wide",
        STYLES[level],
        className,
      )}
    >
      <span className="relative flex h-1.5 w-1.5">
        {pulse ? (
          <span
            className={clsx("absolute inline-flex h-full w-full animate-pulse-ring rounded-full", {
              "bg-signal-nominal": level === "nominal",
              "bg-signal-warning": level === "warning",
              "bg-signal-critical": level === "critical",
              "bg-signal-offline": level === "offline",
            })}
          />
        ) : null}
        <span
          className={clsx("relative inline-flex h-1.5 w-1.5 rounded-full", {
            "bg-signal-nominal": level === "nominal",
            "bg-signal-warning": level === "warning",
            "bg-signal-critical": level === "critical",
            "bg-signal-offline": level === "offline",
          })}
        />
      </span>
      {label ?? LABELS[level]}
    </span>
  );
}
