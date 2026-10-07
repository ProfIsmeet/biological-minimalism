#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = process.cwd();
const evidenceRoot = resolve(root, "qa-screenshots/codex-stage10-final-integration-release-freeze");
const manifest = JSON.parse(await readFile(resolve(evidenceRoot, "EVIDENCE_MANIFEST.json"), "utf8"));
const failures = [];
const requiredIds = [
  "S10-MO-1440x900", "S10-MO-1366x768", "S10-MO-1280x720", "S10-MO-1024x768", "S10-MO-768x1024", "S10-MO-390x844",
  "S10-LM-1440x900", "S10-LM-1366x768", "S10-LM-1280x720", "S10-LM-1024x768", "S10-LM-768x1024", "S10-LM-390x844",
  "S10-MOBILE-DIALOG", "S10-REDUCED-MOTION", "S10-S14-NOMINAL", "S10-S14-FAULT", "S10-S14-WITHHELD",
  "S10-S14-REBUILDING", "S10-S14-RECOVERY", "S10-DISCONNECTED", "S10-PUBLIC-SMOKE",
  "S10-JURY-MO", "S10-JURY-LM", "S10-JURY-SB", "S10-JURY-RX", "S10-JURY-DT", "S10-JURY-AI", "S10-JURY-MT", "S10-JURY-ST",
];

if (manifest.stage !== 10) failures.push("manifest stage is not 10");
if (manifest.actual_voiceover_status !== "DEFERRED_BY_OWNER_TO_POST_STAGE10") failures.push("VoiceOver status is contradictory");
if (manifest.console_errors?.length !== 0) failures.push("unexpected browser console/page errors remain");
if (!Array.isArray(manifest.artifacts) || manifest.artifacts.length !== 42) failures.push(`expected 42 artifacts, got ${manifest.artifacts?.length}`);
if (manifest.checks?.some((check) => check.result !== "PASS")) failures.push("one or more browser checks failed");
if (manifest.route_markers?.at(-1)?.route !== "COMPLETE") failures.push("jury walkthrough has no COMPLETE marker");

const ids = new Set(manifest.artifacts?.map((artifact) => artifact.artifact_id));
for (const required of requiredIds) if (!ids.has(required)) failures.push(`missing required artifact ${required}`);
if (ids.size !== manifest.artifacts?.length) failures.push("duplicate artifact id");

for (const artifact of manifest.artifacts ?? []) {
  if (artifact.visual_review !== "PASS") failures.push(`${artifact.artifact_id}: visual review not PASS`);
  if (artifact.canonical_status !== "canonical") failures.push(`${artifact.artifact_id}: not canonical`);
  if (!artifact.route || !artifact.viewport || !artifact.state || !artifact.source_identity || !artifact.timestamp || !artifact.dimensions) {
    failures.push(`${artifact.artifact_id}: required metadata missing`);
  }
  const prefix = "frontend/qa-screenshots/codex-stage10-final-integration-release-freeze/";
  if (!artifact.relative_path.startsWith(prefix)) {
    failures.push(`${artifact.artifact_id}: path escapes canonical evidence directory`);
    continue;
  }
  const bytes = await readFile(resolve(root, artifact.relative_path.slice("frontend/".length)));
  if (bytes.length !== artifact.byte_size) failures.push(`${artifact.artifact_id}: byte size mismatch`);
  if (createHash("sha256").update(bytes).digest("hex") !== artifact.sha256) failures.push(`${artifact.artifact_id}: hash mismatch`);
}

if (failures.length > 0) {
  console.error(`verify-stage10-evidence: FAIL (${failures.length})`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(`verify-stage10-evidence: PASS (${manifest.artifacts.length} artifacts, ${manifest.checks.length} browser checks, 0 ambiguous, all hashes and visual reviews verified)`);
