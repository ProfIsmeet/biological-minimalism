import type { LucideIcon } from "lucide-react";
import { Activity, BookOpen, Clock, FlaskConical, LayoutDashboard, Orbit, Settings as SettingsIcon, Sparkles } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export type NavGroupAccent = "final" | "system" | "experimental" | "neutral";

export interface NavGroup {
  id: string;
  label: string;
  accent: NavGroupAccent;
  items: NavItem[];
}

// Master prompt 3 §4 — desktop sidebar groups, in this exact order. The
// active operational route gets the strongest final-system teal marker;
// Experimental Research uses ochre; Digital Twin Reference and the rest of
// Research & Reference use neutral/information coloring, never final-system
// success coloring (§4/§14).
export const NAV_GROUPS: NavGroup[] = [
  {
    id: "operations",
    label: "Operations",
    accent: "final",
    items: [
      { href: "/mission-overview", label: "Mission Overview", icon: LayoutDashboard },
      { href: "/live-monitoring", label: "Live Signals", icon: Activity },
    ],
  },
  {
    id: "system",
    label: "System",
    accent: "system",
    items: [{ href: "/system-brief", label: "System Brief", icon: BookOpen }],
  },
  {
    id: "research",
    label: "Research & Reference",
    accent: "neutral",
    items: [
      { href: "/research/experimental", label: "Experimental Research", icon: FlaskConical },
      { href: "/digital-twin", label: "Digital Twin Reference", icon: Orbit },
      { href: "/ai-insights", label: "AI Insights", icon: Sparkles },
      { href: "/mission-timeline", label: "Mission Timeline", icon: Clock },
      { href: "/settings", label: "Settings", icon: SettingsIcon },
    ],
  },
];

/** Flattened for consumers (mobile "More" sheet) that need every destination without group headers. */
export const ALL_NAV_ITEMS: NavItem[] = NAV_GROUPS.flatMap((group) => group.items);
