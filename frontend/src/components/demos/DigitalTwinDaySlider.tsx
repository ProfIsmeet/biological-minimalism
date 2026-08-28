"use client";

const MARKERS = [1, 5, 12, 30];

interface DigitalTwinDaySliderProps {
  day: number;
  onChange: (day: number) => void;
}

export function DigitalTwinDaySlider({ day, onChange }: DigitalTwinDaySliderProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>Mission Day</span>
        <span className="tabular-nums-mono text-sm font-semibold text-cyan-300">{day.toFixed(0)}</span>
      </div>
      <input
        type="range"
        min={0}
        max={30}
        step={1}
        value={day}
        onChange={(event) => onChange(Number(event.target.value))}
        className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-white/10 accent-cyan-400"
        aria-label="Mission day"
      />
      <div className="flex justify-between text-[11px] text-slate-500">
        {MARKERS.map((marker) => (
          <button
            key={marker}
            type="button"
            onClick={() => onChange(marker)}
            className="tabular-nums-mono rounded px-1.5 py-0.5 transition-colors hover:bg-white/5 hover:text-slate-200"
          >
            Day {marker}
          </button>
        ))}
      </div>
    </div>
  );
}
