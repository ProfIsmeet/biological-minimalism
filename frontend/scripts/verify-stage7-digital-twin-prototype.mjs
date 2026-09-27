#!/usr/bin/env node
// Stage 7 Digital Twin prototype — isolation + scientific-boundary structural
// guardrail. Deterministic source-text checks (same zero-dependency
// convention as verify-monitoring-consumers.mjs / verify-webgl-fallback.mjs),
// run manually (or via `node scripts/verify-stage7-digital-twin-prototype.mjs`)
// — NOT wired into the existing verify:monitoring chain, since that chain's
// contract is scoped to the accepted product surface and this prototype is
// deliberately outside it (per the master prompt's isolation requirements).

import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const SRC_ROOT = join(SCRIPT_DIR, "..", "src");

function stripComments(source) {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");
}

function read(relativePath) {
  return stripComments(readFileSync(join(SRC_ROOT, relativePath), "utf8"));
}

const violations = [];

// 1. The prototype route must exist, must not be imported by any existing
// product route/component, and must declare noindex/nofollow metadata.
{
  const routeFile = "app/research/stage7-digital-twin-prototype/page.tsx";
  if (!existsSync(join(SRC_ROOT, routeFile))) {
    violations.push({ file: routeFile, reason: "Prototype route file does not exist" });
  } else {
    const source = read(routeFile);
    if (!/robots:\s*\{\s*index:\s*false,\s*follow:\s*false\s*\}/.test(source)) {
      violations.push({ file: routeFile, reason: "Route metadata does not declare robots: { index: false, follow: false }" });
    }
  }
}

// 2. The prototype root component must render the exact required watermark
// text and the architecture-only/untrained/unvalidated disclosure directly
// in visible UI (not only in docs).
{
  const source = read("prototypes/stage7-digital-twin/Stage7DigitalTwinPrototype.tsx");
  if (!source.includes("ISOLATED STAGE 7 PROTOTYPE — NOT PRODUCT INTEGRATION")) {
    violations.push({ file: "prototypes/stage7-digital-twin/Stage7DigitalTwinPrototype.tsx", reason: "Missing required visible watermark text" });
  }
  for (const term of ["Untrained", "Unvalidated", "Not personalized", "Not a patient model", "Not a clinical tool"]) {
    if (!source.includes(term)) {
      violations.push({ file: "prototypes/stage7-digital-twin/Stage7DigitalTwinPrototype.tsx", reason: `Missing required scientific-boundary term: "${term}"` });
    }
  }
}

// 3. No file under prototypes/stage7-digital-twin or the prototype route may
// reference the shared missionStore, any api client, localStorage, or a
// live-feed subscription — this prototype must have zero backend/store/
// localStorage coupling.
{
  const filesToCheck = [
    "prototypes/stage7-digital-twin/Stage7DigitalTwinPrototype.tsx",
    "prototypes/stage7-digital-twin/Stage7PrototypeCanvas.tsx",
    "prototypes/stage7-digital-twin/Stage7HumanModel.tsx",
    "prototypes/stage7-digital-twin/Stage7SensorAnchors.tsx",
    "prototypes/stage7-digital-twin/Stage7RegionFocus.tsx",
    "prototypes/stage7-digital-twin/Stage7ViewControls.tsx",
    "prototypes/stage7-digital-twin/Stage7SemanticTopology.tsx",
    "prototypes/stage7-digital-twin/Stage7StaticFallback.tsx",
    "prototypes/stage7-digital-twin/stage7PrototypeModel.ts",
    "app/research/stage7-digital-twin-prototype/page.tsx",
  ];
  const forbiddenPatterns = [
    { pattern: /missionStore/, label: "shared missionStore" },
    { pattern: /from ["']@\/lib\/api["']/, label: "shared api client" },
    { pattern: /localStorage/, label: "localStorage" },
    { pattern: /useLiveFeed|LiveFeedProvider|\/ws\/live-feed/, label: "live-feed subscription" },
    { pattern: /fetch\(/, label: "a raw fetch() call" },
  ];
  for (const file of filesToCheck) {
    if (!existsSync(join(SRC_ROOT, file))) {
      violations.push({ file, reason: "Expected prototype file does not exist" });
      continue;
    }
    const source = read(file);
    for (const { pattern, label } of forbiddenPatterns) {
      if (pattern.test(source)) {
        violations.push({ file, reason: `References ${label} — the prototype must have zero backend/store coupling` });
      }
    }
  }
}

// 4. No existing product file may import from the prototype namespace (the
// prototype must never be reachable from a product route).
{
  const productFilesToScan = [
    "app/digital-twin/page.tsx",
    "app/mission-overview/page.tsx",
    "components/layout/Sidebar.tsx",
    "components/layout/MobileNav.tsx",
    "components/layout/AppHeader.tsx",
  ];
  for (const file of productFilesToScan) {
    if (!existsSync(join(SRC_ROOT, file))) continue;
    const source = read(file);
    if (source.includes("prototypes/stage7-digital-twin")) {
      violations.push({ file, reason: "Product file imports from the isolated Stage 7 prototype namespace — this must never happen" });
    }
  }
}

// 5. The prototype must import (not redeclare) the authoritative sensor
// topology from lib/architecture and humanLayout, never invent its own
// modality/region/color table.
{
  const source = read("prototypes/stage7-digital-twin/stage7PrototypeModel.ts");
  for (const requiredImport of ["FINAL_SENSOR_INVENTORY", "MODALITY_COLOR", "FINAL_MODULES", "MODALITY_ANCHOR_POSITION"]) {
    if (!source.includes(requiredImport)) {
      violations.push({ file: "prototypes/stage7-digital-twin/stage7PrototypeModel.ts", reason: `Does not import authoritative "${requiredImport}" — topology must never be reinvented` });
    }
  }
}

// 6. No autonomous animation by default — no useFrame call anywhere in the
// prototype (the design's "zero autonomous rotation by default" invariant).
{
  const filesToScan = [
    "prototypes/stage7-digital-twin/Stage7HumanModel.tsx",
    "prototypes/stage7-digital-twin/Stage7PrototypeCanvas.tsx",
    "prototypes/stage7-digital-twin/Stage7SensorAnchors.tsx",
    "prototypes/stage7-digital-twin/Stage7RegionFocus.tsx",
    "prototypes/stage7-digital-twin/Stage7Lighting.tsx",
  ];
  for (const file of filesToScan) {
    const source = read(file);
    if (/useFrame\(/.test(source)) {
      violations.push({ file, reason: "Contains a useFrame() call — the prototype must have zero autonomous per-frame animation by default" });
    }
  }
}

console.log("verify-stage7-digital-twin-prototype: checked route isolation, watermark/disclosure, zero backend coupling, no product-file imports, authoritative topology reuse, and zero autonomous animation.");

if (violations.length > 0) {
  console.error(`\nFAILED — ${violations.length} violation(s):\n`);
  for (const violation of violations) {
    console.error(`  - ${violation.file}: ${violation.reason}`);
  }
  process.exit(1);
}

console.log("PASSED — the Stage 7 prototype is fully isolated from product routes/state and its scientific boundary is visibly declared.");
process.exit(0);
