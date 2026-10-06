import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "../..");
const reportRoot = path.join(root, "docs/codex-stage9-final-accessibility-jury-acceptance");
const evidenceRoot = path.join(root, "frontend/qa-screenshots/codex-stage9-final-accessibility-jury-acceptance");
const required = [
  "REVIEW_ENTRYPOINT.md", "MASTER_STAGE9_REPORT.md", "EXECUTIVE_VERDICT.md",
  "SOURCE_AND_REPOSITORY_STATE.md", "INHERITED_DEPLOYMENT_RECONCILIATION.md",
  "VOICEOVER_TEST_ENVIRONMENT.md", "VOICEOVER_ROUTE_MATRIX.md",
  "ANNOUNCEMENT_STORM_AUDIT.md", "LIVE_REGION_TRANSITION_MATRIX.md",
  "DIALOG_AND_FOCUS_REVIEW.md", "VISUALIZATION_NONVISUAL_EQUIVALENCE.md",
  "REAL_OS_REDUCED_MOTION.md", "PUBLIC_COLD_START_ACCESSIBILITY.md",
  "JURY_WALKTHROUGH_REPORT.md", "FINDING_LEDGER.md",
  "CORRECTIVE_IMPLEMENTATION_LEDGER.md", "TEST_CHANGE_AUDIT.md",
  "AUTOMATED_VERIFICATION_LEDGER.md", "EVIDENCE_ADJUDICATION.md",
  "EVIDENCE_MANIFEST.json", "OS_SETTING_RESTORATION.md",
  "STAGE10_READINESS.md", "MERGE_RECOMMENDATION.md",
];

const failures = [];
for (const name of required) {
  const target = path.join(reportRoot, name);
  if (!fs.existsSync(target) || fs.statSync(target).size === 0) failures.push(`missing/empty ${name}`);
}

const manifest = JSON.parse(fs.readFileSync(path.join(reportRoot, "EVIDENCE_MANIFEST.json"), "utf8"));
if (manifest.verdict !== "PARTIAL") failures.push("verdict must remain PARTIAL while exact speech is missing");
if (manifest.actual_voiceover_enabled !== true) failures.push("actual VoiceOver run not recorded");
if (manifest.exact_voiceover_speech_captured !== false) failures.push("speech capture must not be overstated");
if (manifest.os_settings_restored !== true) failures.push("OS restoration not recorded");

const transcripts = fs.readdirSync(evidenceRoot).filter((name) => name.endsWith(".md") && name !== "README.md");
if (transcripts.length !== manifest.transcript_records) failures.push(`transcript count ${transcripts.length} != ${manifest.transcript_records}`);
for (const name of transcripts) {
  const text = fs.readFileSync(path.join(evidenceRoot, name), "utf8");
  if (!text.includes("Observed speech: NOT_CAPTURED")) failures.push(`${name} overstates or omits speech-capture status`);
}

const allText = required.map((name) => fs.readFileSync(path.join(reportRoot, name), "utf8")).join("\n");
if (/\/Users\/[^/\s]+/.test(allText)) failures.push("reports contain a private absolute path");

if (failures.length) {
  console.error(`verify-stage9-evidence: FAIL (${failures.length})`);
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}
console.log(`verify-stage9-evidence: PASS (${required.length} reports, ${transcripts.length} honest transcript records, PARTIAL verdict preserved)`);
