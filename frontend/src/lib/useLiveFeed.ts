"use client";

import { useEffect, useRef } from "react";

import { WS_URL } from "@/lib/config";
import type { LiveMetricsSnapshot } from "@/lib/types";
import { useMissionStore } from "@/store/missionStore";

/**
 * Opens `/ws/live-feed` and streams frames into the mission store, with
 * capped exponential backoff reconnection. Telemetry-only: this hook never
 * sends anything back over the socket, matching the backend's WS contract.
 */
export function useLiveFeed(): void {
  const ingest = useMissionStore((state) => state.ingest);
  const setConnectionStatus = useMissionStore((state) => state.setConnectionStatus);
  const retryDelayMs = useRef(1000);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let closedByEffect = false;
    let retryTimeout: ReturnType<typeof setTimeout> | null = null;

    function connect(): void {
      setConnectionStatus("connecting");
      socket = new WebSocket(WS_URL);

      socket.onopen = () => {
        retryDelayMs.current = 1000;
        setConnectionStatus("open");
      };

      socket.onmessage = (event: MessageEvent<string>) => {
        try {
          const snapshot = JSON.parse(event.data) as LiveMetricsSnapshot;
          ingest(snapshot);
        } catch {
          // Ignore a malformed frame rather than tearing down the socket.
        }
      };

      socket.onclose = () => {
        setConnectionStatus("closed");
        if (closedByEffect) return;
        retryTimeout = setTimeout(connect, retryDelayMs.current);
        retryDelayMs.current = Math.min(retryDelayMs.current * 1.5, 10_000);
      };

      socket.onerror = () => {
        socket?.close();
      };
    }

    connect();

    return () => {
      closedByEffect = true;
      if (retryTimeout) clearTimeout(retryTimeout);
      socket?.close();
    };
  }, [ingest, setConnectionStatus]);
}
