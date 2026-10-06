import { LockKeyhole } from "lucide-react";

export function PublicPresentationNotice() {
  return (
    <section
      aria-label="Public presentation state"
      className="rounded-[10px] border border-final-accent/25 bg-final-accent/5 p-4"
    >
      <div className="flex items-start gap-2.5">
        <LockKeyhole size={16} className="mt-0.5 shrink-0 text-final-accent" aria-hidden="true" />
        <div>
          <h2 className="text-sm font-semibold text-ink-primary">Public presentation · read-only</h2>
          <p className="mt-1.5 text-xs leading-relaxed text-ink-secondary">
            Recorded PPG-DaLiA subject S14 replays automatically. Source, playback, and simulated-fault controls
            are disabled for public visitors.
          </p>
        </div>
      </div>
    </section>
  );
}
