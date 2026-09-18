import Link from "next/link";

import { DIGITAL_TWIN_SCOPE_LABEL, PPG_DALIA_EVIDENCE_STATEMENT, S14_SCOPE_STATEMENT } from "@/lib/architecture";

// Master-prompt §7.8 — evidence scope. Four visible rows, not tooltip-only.
export function EvidenceScope() {
  const rows: { title: string; body: string; link?: { href: string; label: string } }[] = [
    { title: "PPG-DaLiA", body: PPG_DALIA_EVIDENCE_STATEMENT },
    { title: "Robustness replay", body: "Tests inference behavior under simulated fault conditions." },
    { title: "S14 replay", body: S14_SCOPE_STATEMENT },
    { title: "Digital Twin", body: DIGITAL_TWIN_SCOPE_LABEL, link: { href: "/digital-twin", label: "Inspect model architecture" } },
  ];

  return (
    <section aria-labelledby="evidence-scope-heading" className="flex flex-col gap-4">
      <h2 id="evidence-scope-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
        Evidence scope
      </h2>
      <ul className="flex flex-col divide-y divide-jury-border-subtle rounded-[10px] border border-jury-border-subtle bg-surface-1">
        {rows.map((row) => (
          <li key={row.title} className="flex flex-col gap-1 px-5 py-4 sm:flex-row sm:items-baseline sm:gap-6">
            <span className="w-40 shrink-0 text-sm font-semibold text-ink-primary">{row.title}</span>
            <span className="flex-1 text-sm leading-relaxed text-ink-secondary">{row.body}</span>
            {row.link ? (
              <Link href={row.link.href} className="shrink-0 text-xs font-medium text-information underline underline-offset-2">
                {row.link.label}
              </Link>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
