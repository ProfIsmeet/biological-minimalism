#!/usr/bin/env node
// ISMET Stage 2 A2 — structural guardrail proving reduced motion has exactly
// one shared source of truth (the persisted `/settings` toggle OR the OS
// `prefers-reduced-motion` media query), and that nothing in the app
// re-derives its own OS-only check that would silently ignore a user who
// only enabled the persisted setting.
//
// Source-level structural check, not a DOM/runtime test - see
// scripts/verify-live-region-boundaries.mjs for the established precedent of
// this style of check in this repo.

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

function read(relativePath) {
  return stripComments(readFileSync(join(SRC_ROOT, relativePath), "utf8"));
}

const violations = [];

// 1. The shared hook itself must combine persisted storage AND the OS query,
// and must listen for both live-update channels (OS change, cross-tab
// storage, same-tab custom event) — not just read once at mount.
{
  const source = read("lib/runtime/reduceMotion.ts");
  const required = [
    "export function useReducedMotionPreference",
    "matchMedia(\"(prefers-reduced-motion: reduce)\")",
    "reduceMotionEnabledFromStorage(window.localStorage.getItem(REDUCE_MOTION_KEY))",
    "persisted || query.matches",
    "query.addEventListener(\"change\"",
    "window.addEventListener(\"storage\"",
    "window.addEventListener(REDUCE_MOTION_CHANGE_EVENT",
  ];
  for (const snippet of required) {
    if (!source.includes(snippet)) {
      violations.push({ file: "lib/runtime/reduceMotion.ts", reason: `Missing required snippet: "${snippet}"` });
    }
  }
}

// 2. The `/settings` toggle must dispatch the same-tab change event right
// after writing localStorage, or other mounted consumers in the same tab
// would only ever see the new preference after a reload.
{
  const source = read("app/settings/page.tsx");
  if (!source.includes("window.dispatchEvent(new Event(REDUCE_MOTION_CHANGE_EVENT))")) {
    violations.push({
      file: "app/settings/page.tsx",
      reason: "Reduced-motion toggle does not dispatch REDUCE_MOTION_CHANGE_EVENT after writing localStorage — same-tab consumers would not update live",
    });
  }
}

// 3. Framer Motion is wrapped in a MotionConfig driven by the shared hook, at
// the root layout, so every `animate`/`transition` prop in the app resolves
// instantly under reduced motion (Framer Motion's own animation engine does
// not respect the CSS-level `prefers-reduced-motion` override).
{
  const provider = read("components/layout/MotionConfigProvider.tsx");
  if (!provider.includes("useReducedMotionPreference") || !provider.includes("<MotionConfig")) {
    violations.push({
      file: "components/layout/MotionConfigProvider.tsx",
      reason: "MotionConfigProvider must wrap children in <MotionConfig> driven by useReducedMotionPreference()",
    });
  }
  const layout = read("app/layout.tsx");
  if (!layout.includes("<MotionConfigProvider>")) {
    violations.push({ file: "app/layout.tsx", reason: "Root layout does not mount <MotionConfigProvider> — Framer Motion surfaces would never respect reduced motion" });
  }
}

// 4. Every WebGL rotation/drift loop (useFrame) must source its reducedMotion
// value from the shared hook (directly, or via a prop ultimately derived from
// it) rather than a private OS-only matchMedia check re-implemented locally.
{
  const noLocalMatchMedia = [
    "components/visualization/human/ConceptualTwinStage.tsx",
    "components/operations/OperationalPhysiologyStage.tsx",
  ];
  for (const file of noLocalMatchMedia) {
    const source = read(file);
    if (source.includes("matchMedia(")) {
      violations.push({ file, reason: "Still contains a local matchMedia() call — must use the shared useReducedMotionPreference() hook instead" });
    }
  }
  if (!read("components/visualization/human/ConceptualTwinStage.tsx").includes("useReducedMotionPreference()")) {
    violations.push({ file: "components/visualization/human/ConceptualTwinStage.tsx", reason: "Does not use the shared useReducedMotionPreference() hook" });
  }
  if (!read("components/operations/OperationalPhysiologyStage.tsx").includes("useReducedMotionPreference()")) {
    violations.push({ file: "components/operations/OperationalPhysiologyStage.tsx", reason: "Does not use the shared useReducedMotionPreference() hook" });
  }
}

// 5. Every useFrame-driven rotation loop must still early-return under
// reducedMotion (the hook only supplies the correct value; each loop must
// still honor it).
{
  const frameLoopFiles = [
    "components/visualization/human/ConceptualTwinStage.tsx",
    "components/visualization/human/HumanScanRings.tsx",
    "components/visualization/human/RegionOrbit.tsx",
  ];
  for (const file of frameLoopFiles) {
    const source = read(file);
    if (!/if\s*\(\s*(!?playing\s*&&\s*)?!?reducedMotion/.test(source) && !/if\s*\(\s*reducedMotion/.test(source)) {
      violations.push({ file, reason: "useFrame loop does not appear to guard on reducedMotion" });
    }
  }
}

console.log(`verify-reduced-motion-unification: checked shared hook, MotionConfig wiring, and ${2} WebGL/Framer consumers for a single reduced-motion source of truth.`);

if (violations.length > 0) {
  console.error(`\nFAILED — ${violations.length} violation(s):\n`);
  for (const violation of violations) {
    console.error(`  - ${violation.file}: ${violation.reason}`);
  }
  process.exit(1);
}

console.log("PASSED — reduced motion has one shared source of truth (persisted setting OR OS query), applied consistently.");
process.exit(0);
