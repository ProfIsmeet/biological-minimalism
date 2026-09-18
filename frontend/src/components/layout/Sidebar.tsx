"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { Radio } from "lucide-react";

import { NAV_ITEMS, SECONDARY_NAV_ITEMS } from "@/components/layout/navigation";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

export function Sidebar() {
  const pathname = usePathname();
  const isReplay = useDatasetReplayMode();

  return (
    <aside className="hidden w-56 shrink-0 flex-col border-r border-jury-border-subtle bg-jury-sidebar md:flex">
      <div className="flex max-h-[72px] items-center gap-2.5 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-final-accent-soft text-final-accent">
          <Radio size={18} strokeWidth={2.25} />
        </div>
        <div>
          <p className="text-sm font-semibold leading-tight text-ink-primary">Biological Minimalism</p>
          <p className="text-[11px] uppercase tracking-wider text-ink-muted">Final Sensing Architecture</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3 py-2" aria-label="Primary">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname?.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              className={clsx(
                "group relative flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition-colors duration-150",
                isActive
                  ? "bg-surface-2 text-ink-primary before:absolute before:-left-3 before:top-1 before:bottom-1 before:w-0.5 before:rounded-full before:bg-final-accent"
                  : "text-ink-muted hover:bg-surface-1 hover:text-ink-secondary",
              )}
            >
              <Icon size={17} strokeWidth={2} className={isActive ? "text-final-accent" : "text-ink-muted group-hover:text-ink-secondary"} />
              {item.label}
            </Link>
          );
        })}

        <div className="mt-4 border-t border-jury-border-subtle pt-3">
          <p className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-disabled">Reference</p>
          {SECONDARY_NAV_ITEMS.map((item) => {
            const isActive = pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={clsx(
                  "flex h-8 items-center rounded-md px-3 text-xs transition-colors duration-150",
                  isActive ? "text-ink-secondary" : "text-ink-disabled hover:text-ink-muted",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>

      <div className="border-t border-jury-border-subtle px-4 py-4 text-[11px] text-ink-muted">
        <p>IAC 2026 · Interactive Presentation</p>
        <p>Research demonstrator — {isReplay ? "recorded-data replay" : "synthetic demo data"}</p>
      </div>
    </aside>
  );
}
