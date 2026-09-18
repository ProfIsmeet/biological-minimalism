#!/usr/bin/env node
// Prompt-2B corrective §7, extended by Prompt-2C §6 — structural guardrail
// against regressing the confirmed-source fix. Uses only Node built-ins
// (fs/path), no parser dependency: for every protected component this
// repo's own source style keeps each `useMissionStore(...)` selector on one
// line, so a per-line regex after stripping comments is an accurate,
// zero-dependency check for this codebase (documented limitation: it is not
// a general-purpose JS/TS parser and would need updating if selector style
// changed to multi-line).
//
// Protects against BOTH raw-consumer regressions: reading
// `missionStore.latest` directly (the original Prompt-2B fix, routed through
// `useConfirmedSnapshot()` instead) and reading `missionStore.history`
// directly (the Prompt-2C fix — TrendPanel.tsx was migrated to
// `useConfirmedHistory()`, since `history` is built by the same unfiltered
// `ingest()` path as `latest` and can carry the same stray cross-source
// frame — see useConfirmedSnapshot.ts).
//
// INTENTIONAL EXCEPTION: components/layout/LiveFeedProvider.tsx is NOT in
// the protected list below. It legitimately reads
// `state.latest?.source.source_type` directly, but only to detect an
// externally-changed source and trigger the authoritative REST re-poll — it
// never renders that value. See its own doc comment. lib/useDataSourceMode.ts
// and lib/monitoring/useConfirmedSnapshot.ts are excluded for the same
// reason: they are the infrastructure that *implements* the confirmed-read
// boundary, not a consumer of it.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const SRC_ROOT = join(SCRIPT_DIR, "..", "src");

const PROTECTED_FILES = [
  "components/jury/PhysiologicalView.tsx",
  "components/jury/FaultAwareInference.tsx",
  "components/jury/SourceStatusStrip.tsx",
  "components/jury/FinalSensorLedger.tsx",
  "components/layout/TopBar.tsx",
  "components/monitoring/MonitoringSourceStrip.tsx",
  "components/monitoring/FinalSignalStack.tsx",
  "components/monitoring/HrInferencePanel.tsx",
  "components/monitoring/SimulatedFaultControl.tsx",
  "components/monitoring/ReplaySessionControl.tsx",
  "components/monitoring/ScopeProvenanceFooter.tsx",
  "components/demos/DataSourceControl.tsx",
  "components/panels/PrimaryVitalsPanel.tsx",
  "components/panels/AIConfidencePanel.tsx",
  "components/panels/TrendPanel.tsx",
];

/** Strips `//` and `/* *\/` comments so an explanatory doc comment that
 * mentions the anti-pattern (for documentation purposes) is never itself
 * flagged as a violation. */
function stripComments(source) {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:])\/\/.*$/gm, "$1");
}

// Matches a `useMissionStore(...)` call whose selector body reads `.latest`
// or `.history` directly — the exact raw-consumer pattern this pass
// eliminated for both fields. Also matches the imperative
// `useMissionStore.getState().latest` / `.history` form, unused today but
// checked defensively.
const RAW_LATEST_OR_HISTORY_PATTERNS = [
  // `useMissionStore((state) => state.latest)`, `state.latest?.source`, and
  // single-arg variants (`state => state.latest`); same shape for
  // `state.history`. Deliberately does not try to match balanced parens
  // (the outer call's closing paren is irrelevant to the check) — it only
  // needs "useMissionStore(", then an arrow, then ".latest" or ".history"
  // on the same line, which matches this codebase's one-line selector
  // style.
  /useMissionStore\(.*=>.*\.(latest|history)\b/,
  /useMissionStore\.getState\(\)\s*\.\s*(latest|history)\b/,
];

const violations = [];
const checked = [];

for (const relativePath of PROTECTED_FILES) {
  const absolutePath = join(SRC_ROOT, relativePath);
  let content;
  try {
    content = readFileSync(absolutePath, "utf8");
  } catch (error) {
    violations.push({ file: relativePath, reason: `File could not be read: ${error.message}` });
    continue;
  }
  const cleaned = stripComments(content);
  const lines = cleaned.split("\n");
  const hits = [];
  lines.forEach((line, index) => {
    if (RAW_LATEST_OR_HISTORY_PATTERNS.some((pattern) => pattern.test(line))) {
      hits.push({ line: index + 1, text: line.trim() });
    }
  });
  checked.push(relativePath);
  if (hits.length > 0) {
    violations.push({ file: relativePath, reason: "Direct raw missionStore.latest or missionStore.history selector found", hits });
  }
}

// Structural proof (complements the live network-capture evidence in the
// dossier) that the source-state retry and the subject-list retry are two
// independent effects/tokens, not one merged reload path (corrective §6/§7:
// "do not retry /data-source/subjects unless the user separately retries
// the subject list").
const sessionContextPath = join(SRC_ROOT, "components/monitoring/MonitoringSessionContext.tsx");
const sessionContextSource = stripComments(readFileSync(sessionContextPath, "utf8"));
const effectBlocks = sessionContextSource.match(/useEffect\(\s*\(\)\s*=>\s*\{[\s\S]*?\},\s*\[[^\]]*\]\s*\);/g) ?? [];
const sourceStateEffect = effectBlocks.find((block) => block.includes("sourceStateReloadToken"));
const subjectListEffect = effectBlocks.find((block) => block.includes("subjectsReloadToken"));
const tokensAreIndependent = Boolean(
  sourceStateEffect
  && subjectListEffect
  && sourceStateEffect !== subjectListEffect
  && !sourceStateEffect.includes("subjectsReloadToken")
  && !subjectListEffect.includes("sourceStateReloadToken"),
);
if (!tokensAreIndependent) {
  violations.push({
    file: "components/monitoring/MonitoringSessionContext.tsx",
    reason: "sourceStateReloadToken and subjectsReloadToken must drive two independent useEffect calls, not a shared one",
  });
}

console.log(`verify-monitoring-consumers: checked ${checked.length} protected file(s) for raw missionStore.latest and missionStore.history reads.`);
console.log("Intentional infrastructure exception (not checked, raw access justified): components/layout/LiveFeedProvider.tsx");
console.log(`Source-state / subject-list retry independence: ${tokensAreIndependent ? "OK (two separate effects)" : "VIOLATION"}`);

if (violations.length > 0) {
  console.error(`\nFAILED — ${violations.length} protected file(s) reintroduced a raw missionStore.latest or missionStore.history read:\n`);
  for (const violation of violations) {
    console.error(`  - ${violation.file}: ${violation.reason}`);
    for (const hit of violation.hits ?? []) {
      console.error(`      line ${hit.line}: ${hit.text}`);
    }
  }
  console.error("\nMigrate the offending selector(s) to useConfirmedSnapshot() or useConfirmedHistory() from lib/monitoring/useConfirmedSnapshot.ts.");
  process.exit(1);
}

console.log("PASSED — no protected file reads missionStore.latest or missionStore.history directly.");
process.exit(0);
