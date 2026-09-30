"use client";

import type { ReactNode } from "react";
import clsx from "clsx";

import { usePanelHeadingLevel } from "@/components/ui/PanelHeadingContext";

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
  const HeadingTag = usePanelHeadingLevel();
  return (
    <section className={clsx("mission-panel flex flex-col", className)} aria-label={title}>
      <div className="mission-panel-header">
        <div className="flex min-w-0 items-center gap-2.5">
          {icon ? <span className="text-cyan-400" aria-hidden="true">{icon}</span> : null}
          <div className="min-w-0">
            <HeadingTag className="break-words text-[15px] font-semibold uppercase tracking-wide text-ink-primary">{title}</HeadingTag>
            {subtitle ? <p className="text-[13px] leading-snug text-ink-secondary">{subtitle}</p> : null}
          </div>
        </div>
        {actions ? <div className="ml-auto flex shrink-0 items-center gap-2">{actions}</div> : null}
      </div>
      <div className={clsx("flex-1 p-4", contentClassName)}>{children}</div>
    </section>
  );
}
