#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const repository = resolve(process.cwd(), "..");
const reportRoot = resolve(repository, "docs/codex-stage10-final-integration-release-freeze");
const manifest = JSON.parse(await readFile(resolve(reportRoot, "RELEASE_CANDIDATE_MANIFEST.json"), "utf8"));
const failures = [];
const required = [
  "REVIEW_ENTRYPOINT.md", "MASTER_STAGE10_REPORT.md", "EXECUTIVE_VERDICT.md", "SOURCE_AND_REPOSITORY_STATE.md",
  "CANONICAL_ANCESTRY_LEDGER.md", "CROSS_STAGE_CORRECTION_PRESERVATION.md", "FINAL_FINDING_LEDGER.md",
  "CORRECTIVE_IMPLEMENTATION_LEDGER.md", "SCIENTIFIC_INTEGRITY_FINAL_REVIEW.md", "TELEMETRY_AND_SOURCE_TRUTH_FINAL_REVIEW.md",
  "ACCESSIBILITY_SCOPE_AND_VOICEOVER_DEFERRAL.md", "RESPONSIVE_BROWSER_ACCEPTANCE.md", "REAL_S14_FINAL_ACCEPTANCE.md",
  "CLEAN_CLONE_REPRODUCTION.md", "DOCKER_RUNTIME_ACCEPTANCE.md", "PUBLIC_DEPLOYMENT_SMOKE_REVIEW.md",
  "DEPENDENCY_AND_SUPPLY_CHAIN_AUDIT.md", "SECRET_PRIVACY_AND_ASSET_AUDIT.md", "PERFORMANCE_AND_RELIABILITY.md",
  "JURY_REHEARSAL.md", "FURKAN_FINAL_SCREENSHOT_GUIDE.md", "TEST_CHANGE_AUDIT.md", "AUTOMATED_VERIFICATION_LEDGER.md",
  "EVIDENCE_ADJUDICATION.md", "EVIDENCE_MANIFEST.json", "RELEASE_CANDIDATE_MANIFEST.json", "ROLLBACK_RUNBOOK.md",
  "MAIN_MERGE_PLAN.md", "PUBLIC_PROMOTION_PLAN.md", "INDEPENDENT_AUDIT_BRIEF.md", "KNOWN_LIMITATIONS.md",
  "FINAL_FREEZE_RECOMMENDATION.md",
];

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
for (const file of required) {
  try {
    if ((await readFile(resolve(reportRoot, file))).length === 0) failures.push(`${file}: empty`);
  } catch {
    failures.push(`${file}: missing`);
  }
}

const requiredFields = [
  "product_name", "candidate_version", "source_branch", "source_sha", "stage10_branch", "implementation_checkpoint_sha",
  "final_report_path", "final_report_sha", "canonical_ancestry", "route_inventory", "environment", "hashes", "model", "dataset",
  "external_asset_requirements", "evidence_directories", "test_counts", "known_limitations", "public_urls", "public_deployment_sha",
  "actual_voiceover_status", "merge_recommendation", "rollback_base", "tag_recommendation", "timestamp",
];
for (const field of requiredFields) if (manifest[field] === undefined || manifest[field] === null || manifest[field] === "") failures.push(`missing field ${field}`);

if (manifest.verdict !== "COMPLETE_RELEASE_CANDIDATE_AFTER_CORRECTIONS") failures.push("unexpected verdict");
if (manifest.source_sha !== "9ea9ef4b8f0f4a9d58344a29541faeb065037665") failures.push("source SHA contradiction");
if (manifest.rollback_base !== manifest.source_sha) failures.push("rollback base contradiction");
if (manifest.actual_voiceover_status !== "DEFERRED_BY_OWNER_TO_POST_STAGE10") failures.push("VoiceOver contradiction");
if (manifest.route_inventory?.length !== 8 || new Set(manifest.route_inventory).size !== 8) failures.push("route inventory contradiction");
if (manifest.canonical_ancestry?.some((row) => row.ancestor !== true)) failures.push("ancestry contains a non-ancestor");

const hashTargets = [
  ["frontend_package_lock_sha256", "frontend/package-lock.json"],
  ["backend_requirements_sha256", "backend/requirements.txt"],
  ["frontend_dockerfile_sha256", "frontend/Dockerfile"],
  ["backend_dockerfile_sha256", "backend/Dockerfile"],
  ["compose_sha256", "docker-compose.yml"],
];
for (const [field, path] of hashTargets) {
  const actual = sha256(await readFile(resolve(repository, path)));
  if (manifest.hashes?.[field] !== actual) failures.push(`${field}: hash mismatch`);
}
const reportHash = sha256(await readFile(resolve(repository, manifest.final_report_path)));
if (manifest.final_report_sha_kind !== "sha256" || manifest.final_report_sha !== reportHash) failures.push("final report hash mismatch");

try {
  execFileSync("git", ["merge-base", "--is-ancestor", manifest.source_sha, "HEAD"], { cwd: repository });
  execFileSync("git", ["merge-base", "--is-ancestor", manifest.implementation_checkpoint_sha, "HEAD"], { cwd: repository });
  for (const row of manifest.canonical_ancestry ?? []) execFileSync("git", ["merge-base", "--is-ancestor", row.commit, "HEAD"], { cwd: repository });
} catch {
  failures.push("one or more declared ancestry relationships are false");
}

if (failures.length > 0) {
  console.error(`verify-stage10-manifest: FAIL (${failures.length})`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
console.log(`verify-stage10-manifest: PASS (${required.length} required reports, ${manifest.canonical_ancestry.length} ancestry checkpoints, hashes and contradictions checked)`);
