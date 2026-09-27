import type { Metadata } from "next";

import { SettingsClient } from "@/app/settings/SettingsClient";

// Stage 4 fix: see the identical note in app/mission-timeline/page.tsx — a
// client-component page.tsx cannot export `metadata`, which left this
// route's browser tab title falling back to a stale, unrelated title.
export const metadata: Metadata = {
  title: "Settings — Biological Minimalism",
};

export default function SettingsPage() {
  return <SettingsClient />;
}
