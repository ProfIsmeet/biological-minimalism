"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { Radio } from "lucide-react";

import { NAV_ITEMS } from "@/components/layout/navigation";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";

export function Sidebar() {
  const pathname = usePathname();
  const isReplay = useDatasetReplayMode();

  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-white/5 bg-space-900/60 backdrop-blur-sm md:flex">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400 shadow-glow">
          <Radio size={18} strokeWidth={2.25} />
        </div>
        <div>
          <p className="text-sm font-semibold leading-tight text-slate-100">Biological Minimalism</p>
          <p className="text-[11px] uppercase tracking-wider text-slate-500">Mission Control</p>
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
                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-cyan-500/10 text-cyan-300"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-200",
              )}
            >
              <Icon size={17} strokeWidth={2} className={isActive ? "text-cyan-400" : "text-slate-500 group-hover:text-slate-300"} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/5 px-4 py-4 text-[11px] text-slate-500">
        <p>IAC 2026 · Interactive Presentation</p>
        <p>Research demonstrator — {isReplay ? "recorded-data replay" : "synthetic demo data"}</p>
      </div>
    </aside>
  );
}
