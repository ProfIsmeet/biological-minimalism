#!/usr/bin/env node

/** Fail-closed verifier for the Stage 8 final closure manifest and PNG set. */

import { createHash } from "node:crypto";
import { readdir, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import process from "node:process";

import sharp from "sharp";

const ROOT = resolve(process.cwd(), "..");
const MANIFEST_PATH = resolve(ROOT, "docs/codex-stage8-final-evidence-closure/EVIDENCE_MANIFEST.json");
const EVIDENCE_DIRECTORY = resolve(ROOT, "frontend/qa-screenshots/codex-stage8-final-evidence-closure");
const failures = [];
let passed = 0;

function check(name, condition, detail = "") {
  if (condition) passed += 1;
  else failures.push(`${name}${detail ? ` — ${detail}` : ""}`);
}

function hasPrivatePath(value) {
  return /(?:\/Users\/[^/\s]+\/|[A-Za-z]:\\Users\\[^\\\s]+\\|\/home\/[^/\s]+\/)/.test(value);
}

const manifestText = await readFile(MANIFEST_PATH, "utf8");
check("manifest contains no private absolute path", !hasPrivatePath(manifestText));
const manifest = JSON.parse(manifestText);
check("schema version is 1", manifest.schema_version === 1);
check("manifest verdict is complete", manifest.final_stage8_verdict === "COMPLETE_ACCEPTED_AFTER_CORRECTIONS");
check("minimum 30 canonical artifacts", manifest.artifacts?.length >= 30, String(manifest.artifacts?.length));

const ids = new Set();
const slots = new Map();
const paths = new Set();
for (const artifact of manifest.artifacts ?? []) {
  check(`${artifact.artifact_id}: stable unique artifact ID`, typeof artifact.artifact_id === "string" && artifact.artifact_id.length > 0 && !ids.has(artifact.artifact_id));
  ids.add(artifact.artifact_id);
  check(`${artifact.artifact_id}: unique coverage slot`, typeof artifact.coverage_slot === "string" && artifact.coverage_slot.length > 0 && !slots.has(artifact.coverage_slot), slots.has(artifact.coverage_slot) ? `also ${slots.get(artifact.coverage_slot)}` : "");
  slots.set(artifact.coverage_slot, artifact.artifact_id);
  check(`${artifact.artifact_id}: canonical and not superseded`, artifact.canonical_status === "canonical" && artifact.superseded !== true);
  check(`${artifact.artifact_id}: visual review decision present`, artifact.visual_review_status === "PASS");
  check(`${artifact.artifact_id}: acceptance decision present`, artifact.acceptance_result === "PASS");
  check(`${artifact.artifact_id}: required fields present`, [
    "relative_repository_path", "route", "viewport_width", "viewport_height",
    "actual_png_width", "actual_png_height", "browser_identity_version",
    "zoom_value", "motion_preference", "source_type", "dataset_label",
    "subject", "replay_state", "fault_state", "capture_timestamp", "sha256",
    "associated_finding_id",
  ].every((field) => artifact[field] !== undefined && artifact[field] !== null && artifact[field] !== ""));
  check(`${artifact.artifact_id}: relative PNG path`, /^frontend\/qa-screenshots\/codex-stage8-final-evidence-closure\/[A-Za-z0-9._-]+\.png$/.test(artifact.relative_repository_path));
  check(`${artifact.artifact_id}: path is unique`, !paths.has(artifact.relative_repository_path));
  paths.add(artifact.relative_repository_path);
  check(`${artifact.artifact_id}: metadata contains no private path`, !hasPrivatePath(JSON.stringify(artifact)));

  const absolute = resolve(ROOT, artifact.relative_repository_path);
  let bytes;
  try {
    bytes = await readFile(absolute);
    check(`${artifact.artifact_id}: file is non-empty`, bytes.length > 0);
  } catch (error) {
    check(`${artifact.artifact_id}: file exists`, false, String(error));
    continue;
  }
  const actualHash = createHash("sha256").update(bytes).digest("hex");
  check(`${artifact.artifact_id}: SHA-256 matches`, actualHash === artifact.sha256, `${actualHash} != ${artifact.sha256}`);
  try {
    const image = sharp(bytes, { failOn: "error" });
    const metadata = await image.metadata();
    await image.ensureAlpha().raw().toBuffer();
    check(`${artifact.artifact_id}: decodes as PNG`, metadata.format === "png");
    check(`${artifact.artifact_id}: dimensions match`, metadata.width === artifact.actual_png_width && metadata.height === artifact.actual_png_height, `${metadata.width}x${metadata.height} != ${artifact.actual_png_width}x${artifact.actual_png_height}`);
  } catch (error) {
    check(`${artifact.artifact_id}: PNG decode succeeds`, false, String(error));
  }
}

const expectedPngs = new Set((await readdir(EVIDENCE_DIRECTORY)).filter((name) => name.endsWith(".png")).map((name) => `frontend/qa-screenshots/codex-stage8-final-evidence-closure/${name}`));
check("every evidence-directory PNG is manifested", expectedPngs.size === paths.size && [...expectedPngs].every((path) => paths.has(path)), JSON.stringify({ directory: [...expectedPngs].sort(), manifest: [...paths].sort() }));

const requiredSlots = [];
for (const route of ["mission-overview", "live-monitoring"])
  for (const viewport of ["1440x900", "1366x768", "1280x720", "1024x768", "768x1024", "390x844"])
    requiredSlots.push(`route:${route}:viewport:${viewport}`);
for (const route of ["system-brief", "research-experimental", "digital-twin", "ai-insights", "mission-timeline", "settings"])
  for (const viewport of ["1440x900", "390x844"])
    requiredSlots.push(`route:${route}:viewport:${viewport}`);
for (const state of ["nominal_connected", "active_simulated_fault", "output_withheld_fail_closed", "rebuilding", "recovered", "fresh_recovered_hr"])
  requiredSlots.push(`s14:${state}`);
for (const route of ["mission-overview", "live-monitoring", "digital-twin", "mission-timeline"])
  for (const zoom of [100, 200])
    requiredSlots.push(`zoom:${route}:${zoom}`);
for (const motion of ["no-preference", "reduce"])
  requiredSlots.push(`motion:${motion}`);
for (const slot of requiredSlots) check(`required coverage ${slot}`, slots.has(slot));

const ambiguousEvidenceCount = failures.filter((failure) => /unique coverage slot|path is unique/.test(failure)).length;
console.log(`verify-stage8-closure-evidence: PASS=${passed} FAIL=${failures.length} ARTIFACTS=${manifest.artifacts?.length ?? 0} REQUIRED_SLOTS=${requiredSlots.length} AMBIGUOUS=${ambiguousEvidenceCount}`);
if (failures.length) {
  for (const failure of failures) console.error(`FAIL: ${failure}`);
  process.exit(1);
}
