/**
 * Prompt-4 Part II (§7) — route/runtime dependency classification.
 *
 * The root layout previously mounted the operational providers
 * (LiveFeedProvider → WebSocket, MonitoringSessionProvider →
 * `/data-source/state` + `/data-source/subjects`, OperationalEventLogWatcher)
 * globally, so EVERY route — including the static/explanatory ones
 * (`/system-brief`, `/research/experimental`, `/digital-twin`) — opened an
 * operational WebSocket and issued replay-session REST requests it never
 * displayed. This module is the single, explicit, route-aware boundary that
 * decides how much operational runtime a given pathname actually needs.
 *
 * It is a PURE string classifier (no React, no browser APIs) precisely so it
 * can be asserted deterministically in scripts/verify-monitoring-state.ts —
 * the runtime-isolation guarantee is proven by test, not only by a Network
 * panel screenshot.
 *
 * Three tiers:
 *
 *  - "full"      → LiveFeed WebSocket + MonitoringSessionProvider +
 *                  OperationalEventLogWatcher. The two genuine operational
 *                  surfaces that show live/replay telemetry AND own the
 *                  replay/fault controls.
 *
 *  - "live-feed" → LiveFeed WebSocket only (no replay-session provider, no
 *                  event watcher). The legacy/reference routes that render
 *                  live vitals or a source-mode control but no replay-session
 *                  workspace. Kept in the allowlist DELIBERATELY (§7: "If a
 *                  legacy page actually requires live telemetry, include it
 *                  deliberately in the runtime allowlist and document why").
 *
 *  - "static"    → no operational network work at all. Everything else:
 *                  the explanatory/research/reference routes and redirects.
 */
export type RuntimeTier = "full" | "live-feed" | "static";

/**
 * Full operational surfaces — live telemetry + replay/fault control.
 * `/mission-overview` renders the operational mission canvas and the
 * DemoControlDrawer; `/live-monitoring` renders the source-aware
 * signal/replay/HR-inference/fault workspace.
 */
export const FULL_OPERATIONAL_ROUTES = ["/mission-overview", "/live-monitoring"] as const;

/**
 * Legacy/reference routes that read live telemetry (via `useConfirmedSnapshot`
 * / `useDatasetReplayMode`) or the source-mode control, but do NOT mount a
 * replay-session workspace and never display operational event history:
 *
 *  - `/ai-insights`     — vitals/trend/confidence panels read the confirmed
 *                          live snapshot.
 *  - `/mission-timeline`— reads the confirmed source mode via
 *                          `useDatasetReplayMode`.
 *  - `/settings`        — DataSourceControl reads the confirmed snapshot and
 *                          seeds `dataSourceStatus`.
 */
export const LEGACY_LIVE_FEED_ROUTES = ["/ai-insights", "/mission-timeline", "/settings"] as const;

function matchesRoute(pathname: string, routes: readonly string[]): boolean {
  return routes.some((route) => pathname === route || pathname.startsWith(`${route}/`));
}

/**
 * Classify a pathname into the runtime tier it is allowed to use. Unknown
 * routes fall through to "static" — the safe default is NO operational work,
 * so a new explanatory route can never accidentally open a background socket.
 */
export function classifyRuntimeTier(pathname: string | null | undefined): RuntimeTier {
  const path = pathname ?? "";
  if (matchesRoute(path, FULL_OPERATIONAL_ROUTES)) return "full";
  if (matchesRoute(path, LEGACY_LIVE_FEED_ROUTES)) return "live-feed";
  return "static";
}

/** Whether the tier keeps a live-feed WebSocket open. */
export function tierOpensWebSocket(tier: RuntimeTier): boolean {
  return tier === "full" || tier === "live-feed";
}

/** Whether the tier mounts the replay-session (MonitoringSession) provider. */
export function tierMountsMonitoringSession(tier: RuntimeTier): boolean {
  return tier === "full";
}
