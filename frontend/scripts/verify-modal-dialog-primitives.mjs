#!/usr/bin/env node
// ISMET Stage 2 A3 — structural guardrail proving every modal dialog in the
// app (the demonstration-controls drawer and the mobile "More" sheet) uses
// the one shared, tested focus/scroll/inert primitive instead of a private
// reimplementation that could drift out of sync (e.g. missing the Tab trap,
// missing scroll lock, or missing background inert).
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

// 1. The shared hook must implement every required behavior: Tab trap (both
// directions), Escape, scroll lock with restoration, background inert +
// aria-hidden with restoration, focus restoration to the trigger, and
// route-change-safe close.
{
  const source = read("lib/runtime/useModalDialog.ts");
  const required = [
    "export function useModalDialog",
    'event.key === "Escape"',
    'event.key !== "Tab"',
    "event.shiftKey && active === first",
    "!event.shiftKey && active === last",
    'document.body.style.overflow = "hidden"',
    'el.setAttribute("inert"',
    'el.setAttribute("aria-hidden", "true")',
    "trigger?.focus()",
    "usePathname()",
    "if (open && pathname !== previousPathnameRef.current) close()",
  ];
  for (const snippet of required) {
    if (!source.includes(snippet)) {
      violations.push({ file: "lib/runtime/useModalDialog.ts", reason: `Missing required snippet: "${snippet}"` });
    }
  }
}

// 2. Both known dialog consumers must call the shared hook, and must portal
// their overlay to document.body (the hook's background-inert step assumes
// this — it walks document.body.children to find what to make inert).
{
  const consumers = [
    "components/operations/DemoControlDrawer.tsx",
    "components/layout/MobileNav.tsx",
  ];
  for (const file of consumers) {
    const source = read(file);
    if (!source.includes("useModalDialog({")) {
      violations.push({ file, reason: "Does not call the shared useModalDialog() hook" });
    }
    if (!source.includes("createPortal(") || !source.includes("document.body")) {
      violations.push({ file, reason: "Does not portal its dialog overlay to document.body, which useModalDialog's background-inert step requires" });
    }
    if (!/role="dialog"/.test(source) || !/aria-modal="true"/.test(source)) {
      violations.push({ file, reason: "Dialog panel is missing role=\"dialog\" or aria-modal=\"true\"" });
    }
  }
}

// 3. No consumer may reimplement its own private focus trap / inert logic —
// that would be exactly the drift this shared primitive exists to prevent.
{
  const consumers = [
    "components/operations/DemoControlDrawer.tsx",
    "components/layout/MobileNav.tsx",
  ];
  for (const file of consumers) {
    const source = read(file);
    if (source.includes('setAttribute("inert"') || source.includes("addEventListener(\"keydown\"")) {
      violations.push({ file, reason: "Reimplements inert/keydown handling locally instead of using the shared useModalDialog() hook" });
    }
  }
}

console.log("verify-modal-dialog-primitives: checked the shared useModalDialog() hook and its 2 known dialog consumers.");

if (violations.length > 0) {
  console.error(`\nFAILED — ${violations.length} violation(s):\n`);
  for (const violation of violations) {
    console.error(`  - ${violation.file}: ${violation.reason}`);
  }
  process.exit(1);
}

console.log("PASSED — every dialog consumer uses the one shared, tested modal focus/scroll/inert primitive.");
process.exit(0);
