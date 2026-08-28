"use client";

import { useEffect, useState } from "react";

export function MissionClock() {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  if (!now) {
    return <span className="tabular-nums-mono text-sm text-slate-500">--:--:-- UTC</span>;
  }

  const time = now.toISOString().slice(11, 19);
  return <span className="tabular-nums-mono text-sm text-slate-300">{time} UTC</span>;
}
