"use client";

import { useEffect, useState } from "react";
import { Orbit } from "lucide-react";
import Link from "next/link";

import { DigitalTwinPanel } from "@/components/panels/DigitalTwinPanel";
import { Panel } from "@/components/ui/Panel";
import { api } from "@/lib/api";
import type { DigitalTwinState } from "@/lib/types";
import { useDatasetReplayMode } from "@/lib/useDataSourceMode";
import { useMissionStore } from "@/store/missionStore";

/** Mission-Overview-scale preview of the Digital Twin, pinned to the
 * current live mission day; the full interactive day slider lives on the
 * dedicated Digital Twin page. */
export function DigitalTwinPreview() {
  const missionDay = useMissionStore((state) => state.latest?.mission_day ?? 1);
  const isReplay = useDatasetReplayMode();
  const [state, setState] = useState<DigitalTwinState | null>(null);

  useEffect(() => {
    if (isReplay) {
      setState(null);
      return;
    }
    let cancelled = false;
    api
      .getDigitalTwin(Math.round(missionDay))
      .then((result) => {
        if (!cancelled) setState(result);
      })
      .catch(() => {
        if (!cancelled) setState(null);
      });
    return () => {
      cancelled = true;
    };
  }, [isReplay, missionDay]);

  return (
    <Panel
      title="Digital Twin"
      subtitle={isReplay ? "Unavailable during recorded-data replay" : (state?.milestone_label ?? "Loading adaptation state…")}
      icon={<Orbit size={16} />}
      actions={
        <Link href="/digital-twin" className="text-[11px] font-medium text-cyan-400 hover:text-cyan-300">
          Open Timeline →
        </Link>
      }
    >
      {isReplay ? (
        <p className="text-sm leading-relaxed text-slate-500">
          Digital Twin unavailable during recorded-data replay until real personalized inference is implemented.
        </p>
      ) : (
        <>
          <DigitalTwinPanel state={state} size={220} />
          <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
            Synthetic, untrained illustration — not a validated prediction.
          </p>
        </>
      )}
    </Panel>
  );
}
