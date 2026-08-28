"use client";

import type { ReactNode } from "react";

import { useLiveFeed } from "@/lib/useLiveFeed";

export function LiveFeedProvider({ children }: { children: ReactNode }) {
  useLiveFeed();
  return <>{children}</>;
}
