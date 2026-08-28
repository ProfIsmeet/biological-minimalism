import type { ReactNode } from "react";
import clsx from "clsx";

interface PanelProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
}

export function Panel({ title, subtitle, icon, actions, children, className, contentClassName }: PanelProps) {
  return (
    <section className={clsx("mission-panel flex flex-col", className)} aria-label={title}>
      <div className="mission-panel-header">
        <div className="flex items-center gap-2.5">
          {icon ? <span className="text-cyan-400" aria-hidden="true">{icon}</span> : null}
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-200">{title}</h2>
            {subtitle ? <p className="text-xs text-slate-500">{subtitle}</p> : null}
          </div>
        </div>
        {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
      </div>
      <div className={clsx("flex-1 p-4", contentClassName)}>{children}</div>
    </section>
  );
}
