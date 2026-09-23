"use client";

import { useEffect, type ReactNode } from "react";

import { api } from "@/lib/api";
import { useLiveFeed } from "@/lib/useLiveFeed";
import { useMissionStore } from "@/store/missionStore";

export function LiveFeedProvider({
  children,
  seedDataSourceState = true,
}: {
  children: ReactNode;
  /**
   * Prompt-4 §7/§8/§25 — request de-duplication. When true (the default, used
   * by the legacy live-feed-only routes that have no MonitoringSessionProvider)
   * this provider also polls the authoritative REST `/data-source/state` so
   * `dataSourceStatus` is populated. On the full-operational routes
   * (`/mission-overview`, `/live-monitoring`) MonitoringSessionProvider is the
   * single owner of that fetch, so the route boundary passes `false` here to
   * remove what was previously a duplicate `/data-source/state` request (and,
   * because that effect keyed on the live source type, a re-poll on every
   * source change while a replay was streaming).
   */
  seedDataSourceState?: boolean;
}) {
  useLiveFeed();
  const liveSourceType = useMissionStore((state) => state.latest?.source.source_type);
  const setDataSourceStatus = useMissionStore((state) => state.setDataSourceStatus);

  useEffect(() => {
    if (!seedDataSourceState) return;
    let cancelled = false;
    api.getDataSourceState().then((status) => {
      if (!cancelled) setDataSourceStatus(status);
    }).catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [seedDataSourceState, liveSourceType, setDataSourceStatus]);

  return <>{children}</>;
}
