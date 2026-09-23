import type { Metadata, Viewport } from "next";

import { AppHeader } from "@/components/layout/AppHeader";
import { MobileNav } from "@/components/layout/MobileNav";
import { OperationalRuntime } from "@/components/layout/OperationalRuntime";
import { Sidebar } from "@/components/layout/Sidebar";

import "./globals.css";

export const metadata: Metadata = {
  title: "Biological Minimalism — Final Sensing Architecture",
  description:
    "Jury-facing demonstration of the CORE_PLUS_CONTEXT physiological sensing architecture and its fault-aware evidence layer.",
};

export const viewport: Viewport = {
  themeColor: "#0B0F12",
};

/**
 * Prompt-4 §15 — apply the persisted reduced-motion preference synchronously,
 * before first paint, so the page never visibly animates and then stops. This
 * runs during HTML parse (before hydration and before decorative CSS/JS
 * animations start). The `/settings` toggle continues to own writes to the
 * same `biomin:reduce-motion` key and OS `prefers-reduced-motion` is honored
 * independently in globals.css.
 */
// HIGH-1: the accepted set here MUST match reduceMotionEnabledFromStorage in
// src/lib/runtime/reduceMotion.ts — "1" (what /settings writes) plus legacy
// "true". Keeping the raw string in sync is asserted by a deterministic test.
const REDUCE_MOTION_BOOT = `try{var v=localStorage.getItem('biomin:reduce-motion');if(v==='1'||v==='true'){document.documentElement.classList.add('reduce-motion')}else{document.documentElement.classList.remove('reduce-motion')}}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  // Prompt 3B §4 — document-level scrolling. The body is the primary scroll
  // container (min-h, not a fixed height trap); the sidebar and header stay
  // sticky, and `<main>` is normal-flow content with NO nested overflow, so
  // wheel/trackpad/PageDown/Space/Home/End/touch all move the document.
  //
  // Prompt 4 §7 — the operational providers no longer wrap the shell. Only the
  // routed page content passes through <OperationalRuntime>, which mounts the
  // WebSocket / replay-session provider / event watcher per route tier. The
  // shell (Sidebar/AppHeader/MobileNav) consumes none of them and stays
  // available on every route, including the fully-static ones.
  return (
    <html lang="en" className="dark">
      <body className="flex min-h-dvh flex-col bg-canvas text-ink-primary md:flex-row">
        <script dangerouslySetInnerHTML={{ __html: REDUCE_MOTION_BOOT }} />
        <a
          href="#main-content"
          className="sr-only rounded-md bg-surface-2 px-4 py-2 text-sm font-semibold text-ink-primary outline-2 outline-offset-2 outline-[#A1D2CC] focus-visible:not-sr-only focus-visible:fixed focus-visible:left-4 focus-visible:top-4 focus-visible:z-[100] focus-visible:outline"
        >
          Skip to main content
        </a>
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="sticky top-0 z-30">
            <AppHeader />
            <MobileNav />
          </div>
          <main
            id="main-content"
            tabIndex={-1}
            className="min-w-0 flex-1 px-4 py-5 outline-none sm:px-6 sm:py-6"
          >
            <OperationalRuntime>{children}</OperationalRuntime>
          </main>
        </div>
      </body>
    </html>
  );
}
