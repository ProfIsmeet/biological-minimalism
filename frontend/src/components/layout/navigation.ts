import type { LucideIcon } from "lucide-react";
import { Activity, BrainCircuit, History, LayoutDashboard, Orbit, Settings } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/mission-overview", label: "Mission Overview", icon: LayoutDashboard },
  { href: "/live-monitoring", label: "Live Monitoring", icon: Activity },
  { href: "/digital-twin", label: "Digital Twin", icon: Orbit },
  { href: "/ai-insights", label: "AI Insights", icon: BrainCircuit },
  { href: "/mission-timeline", label: "Mission Timeline", icon: History },
  { href: "/settings", label: "Settings", icon: Settings },
];
