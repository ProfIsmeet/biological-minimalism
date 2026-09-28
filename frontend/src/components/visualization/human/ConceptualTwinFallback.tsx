import { FINAL_SENSOR_INVENTORY, MODALITY_COLOR, type FinalRegion } from "@/lib/architecture";
import type { DigitalTwinViewPreset } from "@/lib/visualization/digitalTwinPresentation";

const MARKER_POSITION = {
  EEG: [113, 62],
  EOG: [127, 70],
  ECG: [120, 142],
  PPG: [181, 215],
  IMU: [174, 225],
} as const;

/** Information-preserving 2D alternative for unsupported, failed, or lost WebGL. */
export function ConceptualTwinFallback({
  onRetry,
  view,
  activeRegion,
}: {
  onRetry?: () => void;
  view: DigitalTwinViewPreset;
  activeRegion: FinalRegion | null;
}) {
  return (
    <div className="grid h-full min-h-[360px] grid-cols-1 place-items-center gap-4 rounded-[10px] bg-[#061A26] p-5 text-center sm:grid-cols-[minmax(190px,0.8fr)_minmax(220px,1fr)] sm:text-left">
      <svg viewBox="0 0 240 420" className="max-h-[390px] w-full max-w-[230px]" role="img" aria-labelledby="twin-fallback-title twin-fallback-desc">
        <title id="twin-fallback-title">Static human architecture map</title>
        <desc id="twin-fallback-desc">Front-facing human silhouette with frontal, chest, and wrist sensor landmarks. The selected view is {view.label}.</desc>
        <defs>
          <linearGradient id="static-body" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#2D788A" />
            <stop offset="1" stopColor="#123846" />
          </linearGradient>
        </defs>
        <g fill="url(#static-body)" stroke="#63BFB7" strokeWidth="2">
          <ellipse cx="120" cy="53" rx="28" ry="36" />
          <path d="M105 85 L96 99 L70 112 L51 194 L66 199 L91 132 L91 245 L72 394 L98 394 L120 266 L142 394 L168 394 L149 245 L149 132 L174 199 L189 194 L170 112 L144 99 L135 85 Z" />
        </g>
        <line x1="120" y1="22" x2="120" y2="397" stroke="#45D6E5" strokeOpacity="0.18" strokeDasharray="4 8" />
        {FINAL_SENSOR_INVENTORY.map((sensor) => {
          const [cx, cy] = MARKER_POSITION[sensor.modality];
          const selected = sensor.region === activeRegion;
          return (
            <g key={sensor.modality}>
              {selected ? <circle cx={cx} cy={cy} r="12" fill="none" stroke="#F4F7F8" strokeWidth="2" /> : null}
              <circle cx={cx} cy={cy} r={selected ? 6 : 4.5} fill={MODALITY_COLOR[sensor.modality]} stroke="#071115" strokeWidth="2" />
            </g>
          );
        })}
      </svg>

      <div className="max-w-md">
        <p className="text-sm font-semibold text-ink-primary">3D rendering unavailable</p>
        <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
          The static map preserves the anatomical landmarks and selected view. This remains an architecture-only,
          untrained, unvalidated reference; no measurement, confidence score, or personalized state is shown.
        </p>
        <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-information">Current view · {view.label}</p>
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 min-h-11 rounded-[6px] border border-jury-border-strong px-4 py-2 text-sm font-medium text-ink-primary hover:bg-surface-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
          >
            Retry 3D view
          </button>
        ) : (
          <p className="mt-4 text-xs text-ink-muted">This browser or device does not expose a usable WebGL context.</p>
        )}
      </div>
    </div>
  );
}
