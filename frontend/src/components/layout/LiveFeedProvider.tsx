"use client";

import { createContext, useCallback, useContext, useEffect, useRef, type ReactNode } from "react";

import { api } from "@/lib/api";
import {
  sourceStateRequestCoordinator,
  type SourceStateMutationRegistration,
} from "@/lib/monitoring/sourceConvergence";
import type { DataSourceStatus } from "@/lib/types";
import { useLiveFeed } from "@/lib/useLiveFeed";
import { useMissionStore } from "@/store/missionStore";

type LegacyAuthoritativeMutationStarter = (
  operation: () => Promise<DataSourceStatus>,
  onAccepted: (result: DataSourceStatus) => void,
  onError: (error: unknown) => void,
) => SourceStateMutationRegistration | null;

const LegacyAuthoritativeMutationContext = createContext<LegacyAuthoritativeMutationStarter | null>(null);

export function useLegacyAuthoritativeMutation(): LegacyAuthoritativeMutationStarter {
  const startMutation = useContext(LegacyAuthoritativeMutationContext);
  if (!startMutation) {
    throw new Error("useLegacyAuthoritativeMutation requires an active legacy LiveFeedProvider");
  }
  return startMutation;
}

export function LiveFeedProvider({
  children,
  seedDataSourceState = true,
}: {
  children: ReactNode;
  /**
   * Prompt-4 §7/§8/§25 — request de-duplication. When true (the default, used
   * by the legacy live-feed-only routes that have no MonitoringSessionProvider)
   * this provider also fetches the authoritative REST `/data-source/state` so
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
  const sourceConvergenceKey = useMissionStore((state) => state.sourceConvergenceKey);
  const setDataSourceStatus = useMissionStore((state) => state.setDataSourceStatus);
  const requestOwnerRef = useRef(Symbol("legacy-live-feed-source-state-owner"));
  const startAuthoritativeMutation = useCallback<LegacyAuthoritativeMutationStarter>(
    (operation, onAccepted, onError) => sourceStateRequestCoordinator.startAuthoritativeMutation(
      requestOwnerRef.current,
      operation,
      onAccepted,
      onError,
    ),
    [],
  );

  // One explicit owner epoch covers initial seeding and convergence. Replaying
  // this effect with the same token (including React Strict Mode) reactivates
  // the existing lifecycle; a different route owner supersedes it.
  useEffect(() => {
    if (!seedDataSourceState) return;
    const owner = requestOwnerRef.current;
    sourceStateRequestCoordinator.activateOwner(owner);
    return () => {
      sourceStateRequestCoordinator.releaseOwner(owner);
    };
  }, [seedDataSourceState]);

  // A single effect chooses either the initial seed or the current pending
  // identity. Generation checks reject stale, superseded, and unmounted-owner
  // responses independently of promise completion order.
  useEffect(() => {
    if (!seedDataSourceState) return;
    const owner = requestOwnerRef.current;
    sourceStateRequestCoordinator.activateOwner(owner);
    sourceStateRequestCoordinator.startOrAdoptRequest(
      owner,
      sourceConvergenceKey,
      api.getDataSourceState,
      setDataSourceStatus,
      () => undefined,
    );
  }, [seedDataSourceState, sourceConvergenceKey, setDataSourceStatus]);

  return (
    <LegacyAuthoritativeMutationContext.Provider value={seedDataSourceState ? startAuthoritativeMutation : null}>
      {children}
    </LegacyAuthoritativeMutationContext.Provider>
  );
}
