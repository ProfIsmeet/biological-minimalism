#!/usr/bin/env node
// ISMET Stage 2 A4 — structural guardrail proving every 3D physiology/
// Digital Twin surface has a real fallback for unsupported WebGL, a
// renderer/render-time error, and a lost WebGL context — not just the
// up-front "unsupported" check one of the two surfaces had before this
// change (the other, ConceptualTwinStage.tsx, had none at all).
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

// 1. WebglStage must cover all three runtime failure paths: unsupported
// (detectWebgl), render-time error (WebglErrorBoundary), and context loss
// (a "webglcontextlost" listener) — plus the "retry only when technically
// possible" rule (fallback(null) for hard-unsupported, fallback(retry)
// otherwise).
{
  const source = read("components/visualization/human/WebglStage.tsx");
  const required = [
    "detectWebgl()",
    "<WebglErrorBoundary",
    '"webglcontextlost"',
    "renderFallback(null)",
    "renderFallback(retry)",
  ];
  for (const snippet of required) {
    if (!source.includes(snippet)) {
      violations.push({ file: "components/visualization/human/WebglStage.tsx", reason: `Missing required snippet: "${snippet}"` });
    }
  }
}

// 2. The error boundary must be a real React error boundary (class component
// implementing getDerivedStateFromError/componentDidCatch), not a
// try/catch-based approximation that cannot catch render errors thrown by
// descendants.
{
  const source = read("components/visualization/human/WebglErrorBoundary.tsx");
  if (!source.includes("static getDerivedStateFromError") || !source.includes("componentDidCatch")) {
    violations.push({ file: "components/visualization/human/WebglErrorBoundary.tsx", reason: "Not a real React error boundary (missing getDerivedStateFromError/componentDidCatch)" });
  }
}

// 3. Both known Canvas-rendering surfaces must go through WebglStage rather
// than rendering <Canvas> directly and unprotected.
{
  const consumers = [
    "components/visualization/human/PhysiologyAvatar3D.tsx",
    "components/visualization/human/ConceptualTwinStage.tsx",
  ];
  for (const file of consumers) {
    const source = read(file);
    if (!source.includes("<WebglStage")) {
      violations.push({ file, reason: "Does not render <WebglStage> — a <Canvas> here would have no unsupported/error/context-loss fallback" });
    }
    if (/<Canvas\b/.test(source)) {
      violations.push({ file, reason: "Still renders <Canvas> directly outside WebglStage" });
    }
  }
}

// 4. Fallback content must never fabricate a measurement, and must offer a
// retry control conditionally (only when the caller was given one), never
// unconditionally — that would violate "recovery action only when
// technically possible."
{
  const consumers = [
    { file: "components/visualization/human/StaticAvatarFallback.tsx", retryProp: "onRetry" },
    { file: "components/visualization/human/ConceptualTwinFallback.tsx", retryProp: "onRetry" },
  ];
  for (const { file, retryProp } of consumers) {
    const source = read(file);
    if (!source.includes(`${retryProp}?`) && !source.includes(`${retryProp}:`)) {
      violations.push({ file, reason: `Fallback component does not declare an optional ${retryProp} prop` });
    }
    if (!new RegExp(`${retryProp}\\s*\\?`).test(source)) {
      violations.push({ file, reason: "Retry control is not conditionally rendered on the retry prop being present" });
    }
  }
}

console.log("verify-webgl-fallback: checked WebglStage, WebglErrorBoundary, and 2 Canvas-rendering consumers for unsupported/error/context-loss coverage.");

if (violations.length > 0) {
  console.error(`\nFAILED — ${violations.length} violation(s):\n`);
  for (const violation of violations) {
    console.error(`  - ${violation.file}: ${violation.reason}`);
  }
  process.exit(1);
}

console.log("PASSED — every 3D physiology/Digital Twin surface has a real fallback for unsupported WebGL, render errors, and context loss.");
process.exit(0);
