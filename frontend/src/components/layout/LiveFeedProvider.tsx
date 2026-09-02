"use client";

import { useEffect, type ReactNode } from "react";

import { api } from "@/lib/api";
import { useLiveFeed } from "@/lib/useLiveFeed";
import { useMissionStore } from "@/store/missionStore";

export function LiveFeedProvider({ children }: { children: ReactNode }) {
  useLiveFeed();
  const liveSourceType = useMissionStore((state) => state.latest?.source.source_type);
  const setDataSourceStatus = useMissionStore((state) => state.setDataSourceStatus);

  useEffect(() => {
    let cancelled = false;
    api.getDataSourceState().then((status) => {
      if (!cancelled) setDataSourceStatus(status);
    }).catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [liveSourceType, setDataSourceStatus]);

  return <>{children}</>;
}
