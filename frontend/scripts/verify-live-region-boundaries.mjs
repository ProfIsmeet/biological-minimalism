#!/usr/bin/env node
// ISMET Stage 2 A1 — structural guardrail against re-introducing a
// continuously-changing (frame-rate/clock-rate) value inside an
// `aria-live`/`role="status"` element. A screen reader re-announces an
// entire live region's text every time that text changes; embedding a
// per-second clock, per-tick replay position, or per-frame rotation angle
// inside one causes a permanent announcement storm.
//
// This is a source-level structural check, not a DOM/runtime test (this
// repo has no test runner - see scripts/verify-monitoring-state.ts for the
// established precedent of a deterministic Node script standing in for one).
// For each protected file it isolates the JSX element(s) carrying
// `role="status"`/`aria-live` and asserts the ticking identifier/label
// specific to that file is NOT referenced inside them - then, as a positive
// control, asserts the ticking value DOES still appear somewhere else in the
// file (proving the value itself was moved out, not deleted).

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const SRC_ROOT = join(SCRIPT_DIR, "..", "src");

function stripComments(source) {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:])\/\/.*$/gm, "$1");
}

/** Extracts every top-level JSX element whose opening tag contains
 * `role="status"` or an `aria-live` attribute, returning each element's
 * full source text from its opening `<` through its matching closing tag
 * (simple depth-counted same-tag-name matcher - sufficient for this
 * codebase's non-self-closing sr-only spans/paragraphs, which never nest
 * another element of the same tag name inside themselves). */
function extractLiveRegionElements(source) {
  const elements = [];
  const openTagPattern = /<(span|p|div)\b[^>]*(?:role="status"|aria-live=)[^>]*>/g;
  let match;
  while ((match = openTagPattern.exec(source)) !== null) {
    const tagName = match[1];
    const startIndex = match.index;
    const closeTag = `</${tagName}>`;
    const openTagRe = new RegExp(`<${tagName}\\b`, "g");
    openTagRe.lastIndex = match.index + 1;
    let depth = 1;
    let searchFrom = openTagPattern.lastIndex;
    let endIndex = -1;
    while (depth > 0) {
      const nextOpen = source.indexOf(`<${tagName}`, searchFrom);
      const nextClose = source.indexOf(closeTag, searchFrom);
      if (nextClose === -1) break;
      if (nextOpen !== -1 && nextOpen < nextClose) {
        depth += 1;
        searchFrom = nextOpen + 1;
      } else {
        depth -= 1;
        searchFrom = nextClose + closeTag.length;
        if (depth === 0) endIndex = searchFrom;
      }
    }
    if (endIndex !== -1) {
      elements.push(source.slice(startIndex, endIndex));
    }
  }
  return elements;
}

const CHECKS = [
  {
    file: "components/operations/MissionStatusBar.tsx",
    forbiddenInLiveRegion: ["nowMs", "formatUtcClock", "frameAge"],
    requiredInLiveRegion: ['field.label !== "Session time"', 'field.label !== "Last confirmed frame"'],
    mustStillAppearElsewhere: ["formatUtcClock(nowMs)", "frameAge"],
  },
  {
    file: "components/monitoring/MonitoringSourceStrip.tsx",
    forbiddenInLiveRegion: ["formatReplayPosition"],
    requiredInLiveRegion: ['field.label !== "Replay position"'],
    mustStillAppearElsewhere: ["formatReplayPosition(view.replayPositionSeconds"],
  },
  {
    file: "components/visualization/human/ConceptualTwinStage.tsx",
    forbiddenInLiveRegion: ["angleDeg"],
    requiredInLiveRegion: [],
    mustStillAppearElsewhere: ["Current illustrative rotation approximately"],
  },
];

const violations = [];
const checked = [];

for (const check of CHECKS) {
  const absolutePath = join(SRC_ROOT, check.file);
  let raw;
  try {
    raw = readFileSync(absolutePath, "utf8");
  } catch (error) {
    violations.push({ file: check.file, reason: `File could not be read: ${error.message}` });
    continue;
  }
  const source = stripComments(raw);
  checked.push(check.file);

  const liveElements = extractLiveRegionElements(source);
  if (liveElements.length === 0) {
    violations.push({ file: check.file, reason: "No role=\"status\"/aria-live element found at all (expected at least one)" });
    continue;
  }

  for (const forbidden of check.forbiddenInLiveRegion) {
    const hit = liveElements.find((el) => el.includes(forbidden));
    if (hit) {
      violations.push({
        file: check.file,
        reason: `Live-region element still references "${forbidden}" - a continuously-changing value inside an announced region`,
      });
    }
  }

  // The exclusion filter (e.g. `field.label !== "Replay position"`) lives in
  // the component body that BUILDS the live-region text, not inside the JSX
  // element itself - so this is checked against the whole file, proving the
  // ticking field is structurally excluded from whatever text the live
  // region renders.
  for (const required of check.requiredInLiveRegion ?? []) {
    if (!source.includes(required)) {
      violations.push({
        file: check.file,
        reason: `Expected exclusion pattern "${required}" was not found - the live-region summary must explicitly filter out the ticking field`,
      });
    }
  }

  for (const mustAppear of check.mustStillAppearElsewhere) {
    if (!source.includes(mustAppear)) {
      violations.push({
        file: check.file,
        reason: `Expected value "${mustAppear}" was not found anywhere in the file - it must be moved out of the live region, not deleted`,
      });
    }
  }
}

console.log(`verify-live-region-boundaries: checked ${checked.length} protected file(s) for ticking values inside aria-live/role="status" regions.`);

if (violations.length > 0) {
  console.error(`\nFAILED — ${violations.length} violation(s):\n`);
  for (const violation of violations) {
    console.error(`  - ${violation.file}: ${violation.reason}`);
  }
  process.exit(1);
}

console.log("PASSED — no protected file places a continuously-changing value inside an announced live region.");
process.exit(0);
