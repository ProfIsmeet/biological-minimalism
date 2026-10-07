#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(process.cwd(), "..");
const files = {
  schema: "backend/app/schemas/digital_twin.py",
  route: "backend/app/api/routes/digital_twin.py",
  engine: "backend/app/engine/mock_data_engine.py",
  timeline: "frontend/src/app/mission-timeline/MissionTimelineClient.tsx",
  api: "frontend/src/lib/api.ts",
  types: "frontend/src/lib/types.ts",
  pdd: "docs/PDD_Biological_Minimalism_IAC2026.md",
};

const contents = Object.fromEntries(
  await Promise.all(Object.entries(files).map(async ([key, path]) => [key, await readFile(resolve(root, path), "utf8")])),
);

const failures = [];
function requireMatch(key, pattern, reason) {
  if (!pattern.test(contents[key])) failures.push(`${files[key]}: ${reason}`);
}
function forbidMatch(key, pattern, reason) {
  if (pattern.test(contents[key])) failures.push(`${files[key]}: ${reason}`);
}

requireMatch("schema", /ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED/, "missing literal scientific-status contract");
for (const key of ["schema", "route", "engine"]) {
  forbidMatch(key, /overall_adaptation|baseline_score|current_score|stabilized adaptation|adaptation phase/i, "contains an unsupported adaptation score or personalized claim");
}
requireMatch("route", /architecture-only conceptual/i, "route does not identify the conceptual architecture-only contract");
requireMatch("engine", /Architecture-only reference marker/, "engine does not return the safe architecture-only narrative");
forbidMatch("timeline", /getDigitalTwin|from\s+["']@\/lib\/api["']/, "mission timeline still consumes the legacy inferred-state endpoint");
requireMatch("timeline", /ARCHITECTURE ONLY/i, "missing architecture-only disclosure");
forbidMatch("api", /getDigitalTwin|DigitalTwinState/, "legacy digital-twin client contract remains exposed");
forbidMatch("types", /DigitalTwinSystemScore|DigitalTwinState/, "legacy score/state interface remains exposed");
requireMatch("pdd", /Architecture-only anatomical reference; untrained, unvalidated, and not personalized/i, "PDD does not disclose the active scientific-status contract");

if (failures.length > 0) {
  console.error(`verify-stage10-scientific-integrity: FAIL (${failures.length})`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("verify-stage10-scientific-integrity: PASS — no fabricated adaptation score or personalized digital-twin inference remains in the active contract.");
