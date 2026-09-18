import Link from "next/link";

import { BIOZ_EXCLUSION_STATEMENT } from "@/lib/architecture";

// Master-prompt §7.9 — the only main-page BioZ summary. No BioZ charts here.
export function ExperimentalBoundary() {
  return (
    <section
      aria-labelledby="experimental-boundary-heading"
      className="flex flex-col gap-3 rounded-[10px] border border-experimental/30 bg-experimental-soft p-6"
    >
      <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-experimental">Separate research track</span>
      <h2 id="experimental-boundary-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
        BioZ/EIS remained experimental.
      </h2>
      <p className="max-w-2xl text-sm leading-relaxed text-ink-secondary">{BIOZ_EXCLUSION_STATEMENT}</p>
      <Link
        href="/research/experimental"
        className="mt-1 flex h-[42px] w-fit items-center justify-center rounded-[7px] border border-experimental/50 px-4 text-sm font-semibold text-experimental transition-colors duration-150 hover:bg-experimental/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A1D2CC]"
      >
        Open experimental research
      </Link>
    </section>
  );
}
