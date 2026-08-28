import type { SVGProps } from "react";

const base: SVGProps<SVGSVGElement> = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

export function IconOverview(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base} {...props}>
      <rect x="3" y="3" width="7" height="9" rx="1.5" />
      <rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" />
      <rect x="3" y="16" width="7" height="5" rx="1.5" />
    </svg>
  );
}

export function IconPulse(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base} {...props}>
      <path d="M3 12h4l2-7 4 14 2-7h6" />
    </svg>
  );
}

export function IconTwin(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="8" r="3.2" />
      <path d="M5.5 21c0-4 3-6.5 6.5-6.5s6.5 2.5 6.5 6.5" />
      <circle cx="12" cy="12" r="9" strokeDasharray="2 3" opacity="0.5" />
    </svg>
  );
}

export function IconBrain(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base} {...props}>
      <path d="M9 3.5a3 3 0 0 0-3 3v.3A3 3 0 0 0 4.5 9.3a3.2 3.2 0 0 0 0 5.4A3 3 0 0 0 6 17.2v.3a3 3 0 0 0 3 3" />
      <path d="M15 3.5a3 3 0 0 1 3 3v.3a3 3 0 0 1 1.5 2.5 3.2 3.2 0 0 1 0 5.4 3 3 0 0 1-1.5 2.5v.3a3 3 0 0 1-3 3" />
      <path d="M12 4v16" />
    </svg>
  );
}

export function IconTimeline(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base} {...props}>
      <path d="M3 12h18" />
      <circle cx="6" cy="12" r="1.8" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1.8" fill="currentColor" stroke="none" />
      <circle cx="18" cy="12" r="1.8" fill="currentColor" stroke="none" />
      <path d="M6 12V6M12 12V4M18 12v-4" opacity="0.5" />
    </svg>
  );
}

export function IconSettings(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.14.32.44.55.79.66.35.11.6.4.6.77" />
    </svg>
  );
}

export function IconSignal(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base} {...props}>
      <path d="M4 20h16" />
      <rect x="6" y="14" width="2.4" height="6" />
      <rect x="10.8" y="10" width="2.4" height="10" />
      <rect x="15.6" y="5" width="2.4" height="15" />
    </svg>
  );
}
