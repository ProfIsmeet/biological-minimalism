"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

import { NAV_ITEMS } from "@/components/layout/navigation";

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav
      className="flex items-center justify-between gap-1 overflow-x-auto border-b border-white/5 bg-space-900/60 px-2 py-2 md:hidden"
      aria-label="Primary"
    >
      {NAV_ITEMS.map((item) => {
        const isActive = pathname?.startsWith(item.href);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            className={clsx(
              "flex shrink-0 flex-col items-center gap-1 rounded-lg px-3 py-1.5 text-[10px] font-medium",
              isActive ? "text-cyan-300" : "text-slate-500",
            )}
          >
            <Icon size={16} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
