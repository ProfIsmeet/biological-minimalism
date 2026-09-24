"use client";

import { useCallback, useRef, useState } from "react";
import Link from "next/link";
import { createPortal } from "react-dom";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { Activity, LayoutDashboard, MoreHorizontal, X } from "lucide-react";

import { NAV_GROUPS } from "@/components/layout/navigation";
import { useModalDialog } from "@/lib/runtime/useModalDialog";

const PERSISTENT_ITEMS = [
  { href: "/mission-overview", label: "Mission", icon: LayoutDashboard },
  { href: "/live-monitoring", label: "Signals", icon: Activity },
];

// Master prompt 3 §4 — mobile nav shows only Mission / Signals / More; every
// other destination (System Brief, Experimental Research, Digital Twin
// Reference, AI Insights, Mission Timeline, Settings) lives in the "More"
// sheet. 44px minimum touch targets throughout.
//
// Stage 2 A3: the sheet previously had only Escape + a first-focusable-child
// focus-on-open — no Tab containment (focus could escape to the underlying
// page), no scroll lock, and no background-inert (a screen reader's virtual
// cursor and Tab could still reach page content behind the open sheet). It
// now reuses the same `useModalDialog()` primitive DemoControlDrawer already
// shipped (full Tab/Shift+Tab trap, Escape, scroll lock, background inert +
// aria-hidden with exact restoration, focus restoration to the trigger only
// if it still exists, route-change-safe cleanup) — portaled to
// `document.body` like that dialog, which the shared hook's background-inert
// step requires.
export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const moreButtonRef = useRef<HTMLButtonElement>(null);
  const sheetRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  const close = useCallback(() => {
    setOpen(false);
  }, []);

  useModalDialog({ open, onClose: close, panelRef: sheetRef, triggerRef: moreButtonRef, overlayRef });

  const moreGroups = NAV_GROUPS.map((group) => ({
    ...group,
    items: group.id === "operations" ? [] : group.items,
  })).filter((group) => group.items.length > 0);

  return (
    <>
      <nav className="flex items-stretch justify-around border-b border-jury-border-subtle bg-jury-sidebar md:hidden" aria-label="Primary">
        {PERSISTENT_ITEMS.map((item) => {
          const isActive = pathname?.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              className={clsx(
                "flex min-h-11 flex-1 flex-col items-center justify-center gap-1 py-1.5 text-[10px] font-medium",
                isActive ? "text-final-accent" : "text-ink-muted",
              )}
            >
              <Icon size={16} aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
        <button
          ref={moreButtonRef}
          type="button"
          onClick={() => setOpen(true)}
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-controls="mobile-more-sheet"
          className={clsx("flex min-h-11 flex-1 flex-col items-center justify-center gap-1 py-1.5 text-[10px] font-medium", open ? "text-final-accent" : "text-ink-muted")}
        >
          <MoreHorizontal size={16} aria-hidden="true" />
          More
        </button>
      </nav>

      {open && typeof document !== "undefined"
        ? createPortal(
            <div ref={overlayRef} className="fixed inset-0 z-50 flex items-end md:hidden">
              <button type="button" aria-label="Close menu" onClick={close} className="absolute inset-0 bg-black/50" />
              <div
                ref={sheetRef}
                id="mobile-more-sheet"
                role="dialog"
                aria-modal="true"
                aria-labelledby="mobile-more-heading"
                tabIndex={-1}
                className="relative flex max-h-[75vh] w-full flex-col gap-4 overflow-y-auto rounded-t-[14px] border-t border-jury-border-strong bg-canvas p-4 pb-6 outline-none"
              >
                <div className="flex items-center justify-between">
                  <h2 id="mobile-more-heading" className="text-sm font-semibold text-ink-primary">
                    More destinations
                  </h2>
                  <button
                    type="button"
                    onClick={close}
                    aria-label="Close menu"
                    className="flex h-11 w-11 items-center justify-center rounded-[6px] border border-jury-border-strong text-ink-secondary"
                  >
                    <X size={16} aria-hidden="true" />
                  </button>
                </div>
                {moreGroups.map((group) => (
                  <div key={group.id}>
                    <p className="px-1 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-disabled">{group.label}</p>
                    <div className="flex flex-col gap-1">
                      {group.items.map((item) => {
                        const Icon = item.icon;
                        const isActive = pathname?.startsWith(item.href);
                        return (
                          <Link
                            key={item.href}
                            href={item.href}
                            onClick={close}
                            aria-current={isActive ? "page" : undefined}
                            className={clsx(
                              "flex min-h-11 items-center gap-3 rounded-[6px] px-3 text-sm font-medium",
                              isActive ? "bg-surface-2 text-ink-primary" : "text-ink-secondary hover:bg-surface-1",
                            )}
                          >
                            <Icon size={17} aria-hidden="true" />
                            {item.label}
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>,
            document.body,
          )
        : null}
    </>
  );
}
