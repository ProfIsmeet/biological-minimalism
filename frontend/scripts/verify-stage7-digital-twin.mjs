#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => readFileSync(join(ROOT, path), "utf8");
const violations = [];
const requireText = (file, text, reason) => {
  if (!read(file).includes(text)) violations.push(`${file}: ${reason}`);
};
const rejectText = (file, text, reason) => {
  if (read(file).includes(text)) violations.push(`${file}: ${reason}`);
};

const page = "src/app/digital-twin/page.tsx";
const stage = "src/components/visualization/human/ConceptualTwinStage.tsx";
const fallback = "src/components/visualization/human/ConceptualTwinFallback.tsx";
const contacts = "src/components/visualization/human/ArchitectureSensorContacts.tsx";

for (const forbidden of ["useMissionStore", "useLiveFeed", "fetch(", "WebSocket", "getDigitalTwin", "overall_adaptation"]) {
  rejectText(stage, forbidden, `static architecture route must not own or fabricate operational/model state (${forbidden})`);
  rejectText(page, forbidden, `page must stay architecture-only (${forbidden})`);
}

for (const control of ['"front"', '"back"', '"chest"', '"wrist"', "Reset view", "Pause rotation"]) {
  requireText(stage, control, `missing required control ${control}`);
}

requireText(stage, "tabIndex={0}", "viewer itself must be keyboard focusable");
requireText(stage, "onKeyDown={onStageKeyDown}", "viewer keyboard behavior is not wired");
requireText(stage, "Semantic architecture summary", "canvas lacks a semantic companion");
requireText(stage, "FINAL_SENSOR_INVENTORY.map", "canonical sensor inventory is not rendered semantically");
requireText(stage, 'frameloop: motionActive && !reducedMotion ? "always" : "demand"', "idle/reduced rendering is not demand-driven");
requireText(stage, 'document.addEventListener("visibilitychange"', "hidden-page rendering is not explicitly paused");
requireText(stage, 'document.removeEventListener("visibilitychange"', "visibility listener is not cleaned up on unmount");
requireText(stage, "useReducedMotionPreference", "shared reduced-motion contract is not consumed");
requireText(stage, "ArchitectureSensorContacts", "canonical anatomical landmarks are not rendered");
requireText(contacts, "FINAL_SENSOR_INVENTORY.map", "3D markers do not derive from canonical inventory");
requireText(fallback, 'role="img"', "static fallback has no accessible image semantics");
requireText(fallback, "FINAL_SENSOR_INVENTORY.map", "fallback does not preserve canonical landmark topology");
requireText(page, "ARCHITECTURE ONLY · UNTRAINED · UNVALIDATED", "persistent scientific boundary is absent");

const runtime = read("src/lib/runtime/operationalRuntimeTier.ts");
if (/FULL_OPERATIONAL_ROUTES[^;]*digital-twin/s.test(runtime) || /LEGACY_LIVE_FEED_ROUTES[^;]*digital-twin/s.test(runtime)) {
  violations.push("src/lib/runtime/operationalRuntimeTier.ts: Digital Twin route must remain static and must not open monitoring ownership");
}

console.log("verify-stage7-digital-twin: checked production route, interaction controls, semantic fallback, reduced motion, and monitoring isolation.");
if (violations.length) {
  console.error(`FAILED — ${violations.length} violation(s):`);
  for (const violation of violations) console.error(`  - ${violation}`);
  process.exit(1);
}
console.log("PASSED — Stage 7 Digital Twin structural and ownership contracts hold.");
