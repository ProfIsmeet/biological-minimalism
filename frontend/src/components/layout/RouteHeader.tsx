import type { ReactNode } from "react";
import clsx from "clsx";

/**
 * Stage 8 §16/§17 — the single page-header treatment for a standard route.
 *
 * Before this existed, five routes rendered a page header five slightly
 * different ways: /live-monitoring and /digital-twin at 28px rising to 34px,
 * /ai-insights, /mission-timeline and /settings at 24px rising to 28px, with
 * different tracking, different lede sizes, and different eyebrow colours
 * chosen per route rather than per meaning. That is not a cosmetic
 * inconsistency — §9.1 puts a page title at 24-30px, so the 34px variant was
 * out of band, and a reader moving between routes had no stable signal for
 * "this is the top of a page". Centralising it means the scale cannot drift
 * again route by route.
 *
 * Deliberately NOT used by the two display heroes, JuryHero (/system-brief)
 * and ExperimentalHero (/research/experimental). Those are presentation
 * openings for a walkthrough rather than page headers for a workspace: they
 * carry their own larger display type, their own scope labels, and in
 * JuryHero's case a numeric identity block. Forcing them into this primitive
 * would flatten a real distinction rather than remove a real inconsistency,
 * which §17 explicitly warns against.
 */

/**
 * The eyebrow's tone carries meaning and is chosen by what the route IS, not
 * by variety: `accent` for the operational surfaces, `information` for system
 * reference, `experimental` for anything scoped as experimental evidence.
 */
export type RouteHeaderTone = "accent" | "information" | "experimental";

const TONE_CLASS: Record<RouteHeaderTone, string> = {
  accent: "text-final-accent",
  information: "text-information",
  experimental: "text-experimental",
};

interface RouteHeaderProps {
  /** Short scope line above the title. Omit when the title alone is the scope. */
  eyebrow?: string;
  eyebrowTone?: RouteHeaderTone;
  title: string;
  /** One or two sentences saying what the route shows. */
  lede?: ReactNode;
  /**
   * A quieter line for a scope limit that must travel with the title —
   * e.g. that replay and synthetic data are not live astronaut monitoring.
   * Kept visually secondary to the lede but never below the 12px floor.
   */
  caveat?: ReactNode;
  /** A status or boundary pill rendered under the text block. */
  badge?: ReactNode;
  className?: string;
}

export function RouteHeader({
  eyebrow,
  eyebrowTone = "accent",
  title,
  lede,
  caveat,
  badge,
  className,
}: RouteHeaderProps) {
  return (
    <header className={clsx("flex max-w-3xl flex-col gap-2", className)}>
      {eyebrow ? (
        <span className={clsx("text-xs font-semibold uppercase tracking-[0.1em]", TONE_CLASS[eyebrowTone])}>
          {eyebrow}
        </span>
      ) : null}

      {/* §9.1 page title: 24px, rising to 28px at sm — inside the 24-30px band
          at every width, so no breakpoint pushes it out. */}
      <h1 className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary sm:text-[28px]">
        {title}
      </h1>

      {lede ? <p className="text-sm leading-relaxed text-ink-secondary">{lede}</p> : null}
      {caveat ? <p className="text-xs leading-relaxed text-ink-muted">{caveat}</p> : null}
      {badge ? <div className="mt-1">{badge}</div> : null}
    </header>
  );
}
