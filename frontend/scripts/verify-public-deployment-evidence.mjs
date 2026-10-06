import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "../..");
const reportRoot = path.join(root, "docs/codex-public-presentation-deployment");
const allowPending = process.argv.includes("--allow-pending");
const required = [
  "REVIEW_ENTRYPOINT.md", "MASTER_DEPLOYMENT_REPORT.md", "EXECUTIVE_STATUS.md",
  "SOURCE_AND_REPOSITORY_STATE.md", "DEPLOYMENT_ARCHITECTURE.md",
  "PUBLIC_MODE_SECURITY_REVIEW.md", "DATASET_CHECKPOINT_PROVISIONING.md",
  "LOCAL_ACCEPTANCE.md", "PRODUCTION_ACCEPTANCE.md", "PUBLIC_ROUTE_MATRIX.md",
  "PUBLIC_BROWSER_EVIDENCE.md", "ENDURANCE_TEST.md", "TEST_AND_VERIFICATION_LEDGER.md",
  "TEST_CHANGE_AUDIT.md", "SECRET_AND_PRIVATE_PATH_AUDIT.md", "ROLLBACK_RUNBOOK.md",
  "COST_AND_PLATFORM_LIMITATIONS.md", "MERGE_AND_STAGE9_RECOMMENDATION.md",
  "EVIDENCE_MANIFEST.json",
];

const failures = [];
for (const name of required) {
  const target = path.join(reportRoot, name);
  if (!fs.existsSync(target) || fs.statSync(target).size === 0) failures.push(`missing/empty ${name}`);
}

const manifest = JSON.parse(fs.readFileSync(path.join(reportRoot, "EVIDENCE_MANIFEST.json"), "utf8"));
if (manifest.source_sha !== "36cc9d36a9c11c47374bd6be142761d93b7cdfb5") failures.push("wrong source SHA");
if (manifest.deployment_branch !== "codex/public-presentation-deploy") failures.push("wrong branch");
if (manifest.assets?.tracked_in_git !== false) failures.push("asset tracking must be false");
if (!allowPending && !manifest.production) failures.push("production evidence is pending");

const newDocs = required.map((name) => fs.readFileSync(path.join(reportRoot, name), "utf8")).join("\n");
if (/\/Users\/[^/\s]+/.test(newDocs)) failures.push("new reports contain a private local path");

const render = fs.readFileSync(path.join(root, "render.yaml"), "utf8");
for (const token of ["BIOMIN_PUBLIC_PRESENTATION_MODE", "BIOMIN_PRESENTATION_DATASET_SHA256", "BIOMIN_ALLOWED_ORIGINS"]) {
  if (!render.includes(token)) failures.push(`render.yaml missing ${token}`);
}
if (render.includes('["*"]')) failures.push("render.yaml permits wildcard CORS");

if (failures.length) {
  console.error(`verify-public-deployment-evidence: FAIL (${failures.length})`);
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}
console.log(`verify-public-deployment-evidence: PASS (${required.length} reports, production ${allowPending ? "pending allowed" : "closed"})`);
