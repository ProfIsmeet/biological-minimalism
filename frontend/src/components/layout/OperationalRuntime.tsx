"use client";

import { usePathname } from "next/navigation";
import { type ReactNode } from "react";

import { LiveFeedProvider } from "@/components/layout/LiveFeedProvider";
import { MonitoringSessionProvider } from "@/components/monitoring/MonitoringSessionContext";
import { OperationalEventLogWatcher } from "@/components/operations/OperationalEventLogWatcher";
import { classifyRuntimeTier } from "@/lib/runtime/operationalRuntimeTier";

/**
 * Prompt-4 Part II (§7) — the single route-aware runtime boundary.
 *
 * The persistent application shell (Sidebar / AppHeader / MobileNav) is
 * rendered OUTSIDE this component in the root layout and consumes none of the
 * operational providers, so navigation and the shell are available on every
 * route regardless of tier. This component wraps ONLY the routed page content
 * and mounts operational providers according to the pathname's tier:
 *
 *  - full      → WebSocket + replay-session provider + event watcher.
 *  - live-feed → WebSocket only (LiveFeedProvider still seeds
 *                `/data-source/state` because there is no
 *                MonitoringSessionProvider on these routes).
 *  - static    → nothing. No WebSocket, no `/data-source/state`, no
 *                `/data-source/subjects`.
 *
 * Because `usePathname()` is available during the App-Router server render,
 * the server and client agree on the tier and there is no hydration mismatch.
 * Navigating between two `full` routes keeps the same provider instances
 * mounted (identical tree shape), so the WebSocket, confirmed snapshot, and
 * session event log all survive `/mission-overview` ↔ `/live-monitoring`
 * navigation. Navigating to a `static` route unmounts them, which is exactly
 * the cleanup Gate E requires ("a route change cleans up operational work").
 */
export function OperationalRuntime({ children }: { children: ReactNode }) {
  const tier = classifyRuntimeTier(usePathname());

  if (tier === "full") {
    return (
      <LiveFeedProvider seedDataSourceState={false}>
        <MonitoringSessionProvider>
          <OperationalEventLogWatcher />
          {children}
        </MonitoringSessionProvider>
      </LiveFeedProvider>
    );
  }

  if (tier === "live-feed") {
    return <LiveFeedProvider>{children}</LiveFeedProvider>;
  }

  return <>{children}</>;
}
