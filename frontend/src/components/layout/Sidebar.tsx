"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { Radio } from "lucide-react";

import { NAV_GROUPS, type NavGroupAccent } from "@/components/layout/navigation";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

const ACCENT_MARKER: Record<NavGroupAccent, string> = {
  final: "before:bg-final-accent",
  system: "before:bg-information",
  experimental: "before:bg-experimental",
  neutral: "before:bg-ink-muted",
};

const ACCENT_ICON: Record<NavGroupAccent, string> = {
  final: "text-final-accent",
  system: "text-information",
  experimental: "text-experimental",
  neutral: "text-ink-secondary",
};

// Master prompt 3 §4 — grouped sidebar (Operations / System / Research &
// Reference). The active operational route gets the strongest final-system
// teal marker; other groups use their own accent so nothing competes with
// Operations for visual weight.
export function Sidebar() {
  const pathname = usePathname();
  const isReplay = useDatasetReplayMode();

  return (
    <aside className="hidden w-[216px] shrink-0 flex-col border-r border-jury-border-subtle bg-jury-sidebar md:flex md:sticky md:top-0 md:h-dvh md:self-start">
      <div className="flex max-h-[72px] items-center gap-2.5 px-5 py-5">
        <Radio size={18} strokeWidth={1.75} className="shrink-0 text-final-accent" aria-hidden="true" />
        <div>
          <p className="text-sm font-semibold leading-tight text-ink-primary">Biological Minimalism</p>
          <p className="text-[11px] uppercase tracking-wider text-ink-muted">Mission systems demonstrator</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-4 overflow-y-auto px-3 py-2" aria-label="Primary">
        {NAV_GROUPS.map((group) => (
          <div key={group.id}>
            <p className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-disabled">{group.label}</p>
            <div className="flex flex-col gap-1">
              {group.items.map((item) => {
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
                        ? clsx("bg-surface-2 text-ink-primary before:absolute before:-left-3 before:top-1 before:bottom-1 before:w-0.5 before:rounded-full", ACCENT_MARKER[group.accent])
                        : "text-ink-muted hover:bg-surface-1 hover:text-ink-secondary",
                    )}
                  >
                    <Icon size={17} strokeWidth={2} className={isActive ? ACCENT_ICON[group.accent] : "text-ink-muted group-hover:text-ink-secondary"} />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-jury-border-subtle px-4 py-4 text-[11px] text-ink-muted">
        <p>IAC 2026 · Interactive Presentation</p>
        <p>Mission systems demonstrator — {isReplay ? "recorded-data replay" : "synthetic demo data"}</p>
      </div>
    </aside>
  );
}
