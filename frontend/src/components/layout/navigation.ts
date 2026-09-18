import type { LucideIcon } from "lucide-react";
import { Activity, FlaskConical, LayoutDashboard } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

// Master-prompt §5: primary navigation contains exactly these three
// destinations, in this order. Digital Twin, AI Insights, Mission Timeline,
// Settings, and Research Mode remain reachable by direct link (§4.7) but are
// intentionally excluded here so they never compete with the three demo
// destinations.
export const NAV_ITEMS: NavItem[] = [
  { href: "/mission-overview", label: "Overview", icon: LayoutDashboard },
  { href: "/live-monitoring", label: "Live Signals", icon: Activity },
  { href: "/research/experimental", label: "Experimental Research", icon: FlaskConical },
];

export interface SecondaryNavItem {
  href: string;
  label: string;
}

// Secondary/subordinate links (§4.6, §4.7) — not part of primary navigation,
// rendered in a visually subordinate footer/overflow area only.
export const SECONDARY_NAV_ITEMS: SecondaryNavItem[] = [
  { href: "/digital-twin", label: "Digital Twin (reference)" },
  { href: "/ai-insights", label: "AI Insights" },
  { href: "/mission-timeline", label: "Mission Timeline" },
  { href: "/settings", label: "Settings" },
];
