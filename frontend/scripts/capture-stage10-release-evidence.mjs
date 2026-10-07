#!/usr/bin/env node

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { resolve } from "node:path";

import sharp from "sharp";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const MODE = process.argv[2] ?? "local";
const FRONTEND = process.env.STAGE10_FRONTEND_URL ?? "http://127.0.0.1:3160";
const BACKEND = process.env.STAGE10_BACKEND_URL ?? "http://127.0.0.1:8160";
const CHROME = process.env.STAGE10_CHROME_BIN ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const OUTPUT = resolve(process.cwd(), "qa-screenshots/codex-stage10-final-integration-release-freeze");
const MANIFEST = resolve(OUTPUT, "EVIDENCE_MANIFEST.json");
const reviewed = process.env.STAGE10_VISUAL_REVIEWED === "1";

const checks = [];
const artifacts = [];
const consoleErrors = [];
const expectedTransportErrors = [];
const routeMarkers = [];

function check(name, condition, detail = "") {
  checks.push({ name, result: condition ? "PASS" : "FAIL", detail: String(detail) });
  if (!condition) throw new Error(`${name}${detail ? `: ${detail}` : ""}`);
}

async function api(path, init = {}) {
  const response = await fetch(`${BACKEND}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`${init.method ?? "GET"} ${path} => ${response.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

async function waitForMetric(predicate, label, timeoutMs = 45_000) {
  const deadline = Date.now() + timeoutMs;
  let last = null;
  while (Date.now() < deadline) {
    try {
      last = await api("/metrics/live");
      if (predicate(last)) return last;
    } catch {
      // Transitions can intentionally leave no current frame.
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 250));
  }
  throw new Error(`Timed out waiting for ${label}; last=${JSON.stringify(last)}`);
}

async function settle(page, route, timeout = 30_000) {
  await page.goto(`${FRONTEND}${route}`, { waitUntil: "networkidle", timeout });
  await page.locator("h1").first().waitFor({ state: "visible", timeout: 15_000 });
  await page.waitForTimeout(500);
}

async function auditLayout(page, route, viewport) {
  const result = await page.evaluate(() => {
    const root = document.documentElement;
    const smallText = [...document.querySelectorAll("button, a, label, th, [role='button'], [role='tab']")]
      .filter((element) => {
        const rect = element.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && Number.parseFloat(getComputedStyle(element).fontSize) < 12;
      })
      .map((element) => ({ text: (element.textContent ?? "").trim().slice(0, 80), font: getComputedStyle(element).fontSize }));
    const unnamed = [...document.querySelectorAll("button")]
      .filter((button) => button.getBoundingClientRect().width > 0 && !(button.getAttribute("aria-label") || button.textContent?.trim()))
      .length;
    return {
      overflow: root.scrollWidth - root.clientWidth,
      clientWidth: root.clientWidth,
      scrollWidth: root.scrollWidth,
      h1Count: document.querySelectorAll("h1").length,
      smallText,
      unnamed,
      bodyText: document.body.innerText.slice(0, 500),
    };
  });
  check(`${route} ${viewport.width}x${viewport.height}: no page overflow`, result.overflow <= 1, JSON.stringify(result));
  check(`${route} ${viewport.width}x${viewport.height}: exactly one h1`, result.h1Count === 1, JSON.stringify(result));
  check(`${route} ${viewport.width}x${viewport.height}: operational text floor`, result.smallText.length === 0, JSON.stringify(result.smallText));
  check(`${route} ${viewport.width}x${viewport.height}: named buttons`, result.unnamed === 0, JSON.stringify(result));
  return result;
}

async function record(page, { id, filename, route, viewport, state, sourceIdentity, fullPage = true, runtime = {} }) {
  const file = resolve(OUTPUT, filename);
  await page.screenshot({ path: file, fullPage, animations: "disabled" });
  const bytes = await readFile(file);
  const metadata = await sharp(bytes).metadata();
  check(`${id}: durable PNG`, metadata.format === "png" && bytes.length > 0, `${metadata.format}/${bytes.length}`);
  artifacts.push({
    artifact_id: id,
    relative_path: `frontend/qa-screenshots/codex-stage10-final-integration-release-freeze/${filename}`,
    route,
    viewport: `${viewport.width}x${viewport.height}`,
    state,
    source_identity: sourceIdentity,
    timestamp: new Date().toISOString(),
    dimensions: `${metadata.width}x${metadata.height}`,
    sha256: createHash("sha256").update(bytes).digest("hex"),
    visual_review: reviewed ? "PASS" : "PENDING_MANUAL_REVIEW",
    canonical_status: "canonical",
    finding_id: "none",
    byte_size: bytes.length,
    runtime,
  });
}

function wireDiagnostics(page) {
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push({ url: page.url(), text: message.text() });
  });
  page.on("pageerror", (error) => consoleErrors.push({ url: page.url(), text: String(error) }));
}

const matrix = [
  { width: 1440, height: 900 },
  { width: 1366, height: 768 },
  { width: 1280, height: 720 },
  { width: 1024, height: 768 },
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
];
const routes = [
  ["mo", "/mission-overview"],
  ["lm", "/live-monitoring"],
  ["sb", "/system-brief"],
  ["rx", "/research/experimental"],
  ["dt", "/digital-twin"],
  ["ai", "/ai-insights"],
  ["mt", "/mission-timeline"],
  ["st", "/settings"],
];

async function localRun(browser) {
  await api("/data-source/synthetic", { method: "POST" });
  const context = await browser.newContext({ viewport: matrix[0], reducedMotion: "no-preference" });
  const page = await context.newPage();
  wireDiagnostics(page);

  for (const [code, route] of routes) {
    const viewports = route === "/mission-overview" || route === "/live-monitoring"
      ? matrix
      : route === "/digital-twin"
        ? [matrix[0], matrix[4], matrix[5]]
        : [matrix[0], matrix[5]];
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await settle(page, route);
      const runtime = await auditLayout(page, route, viewport);
      await record(page, {
        id: `S10-${code.toUpperCase()}-${viewport.width}x${viewport.height}`,
        filename: `${code}-${viewport.width}x${viewport.height}.png`,
        route,
        viewport,
        state: "synthetic_nominal",
        sourceIdentity: "SYNTHETIC_DEMO",
        runtime,
      });
    }
  }

  await page.setViewportSize(matrix[5]);
  await settle(page, "/mission-overview");
  await page.getByRole("button", { name: "More" }).click();
  const mobileDialog = page.getByRole("dialog");
  check("mobile More dialog opens", await mobileDialog.isVisible());
  check("mobile dialog is modal", await mobileDialog.getAttribute("aria-modal") === "true");
  check("mobile dialog owns focus", await page.evaluate(() => Boolean(document.activeElement?.closest("[role='dialog']"))));
  check("mobile background is inert", await page.evaluate(() => Boolean(document.querySelector("body > div[inert]"))));
  await record(page, { id: "S10-MOBILE-DIALOG", filename: "mobile-more-dialog.png", route: "/mission-overview", viewport: matrix[5], state: "mobile_more_dialog_open", sourceIdentity: "SYNTHETIC_DEMO" });
  await page.keyboard.press("Escape");
  check("mobile dialog Escape closes", !(await mobileDialog.isVisible().catch(() => false)));
  check("mobile dialog restores trigger", await page.evaluate(() => document.activeElement?.textContent?.trim() === "More"));

  const reduced = await browser.newContext({ viewport: matrix[0], reducedMotion: "reduce" });
  const reducedPage = await reduced.newPage();
  wireDiagnostics(reducedPage);
  await settle(reducedPage, "/digital-twin");
  check("reduced motion media active", await reducedPage.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches));
  check("reduced motion keeps semantic boundary", (await reducedPage.locator("body").innerText()).includes("ARCHITECTURE ONLY"));
  await record(reducedPage, { id: "S10-REDUCED-MOTION", filename: "dt-reduced-motion.png", route: "/digital-twin", viewport: matrix[0], state: "prefers_reduced_motion", sourceIdentity: "NOT_APPLICABLE" });
  await reduced.close();

  const subjects = await api("/data-source/subjects");
  check("real S14 is discoverable", subjects.dataset_name === "PPG-DaLiA" && subjects.subjects.includes("S14"), JSON.stringify(subjects));
  await api("/data-source/replay/load", { method: "POST", body: JSON.stringify({ subject_id: "S14" }) });
  const paused = await api("/data-source/state");
  check("S14 loads paused at zero", paused.playback_state === "paused" && paused.replay_position_seconds === 0, JSON.stringify(paused));
  await api("/data-source/replay/play", { method: "POST" });
  await api("/data-source/replay/speed", { method: "POST", body: JSON.stringify({ speed: 5 }) });
  const nominal = await waitForMetric((value) => value.source?.subject_id === "S14" && Number.isFinite(value.heart_rate_prediction?.value), "S14 nominal HR");
  const nominalWindow = nominal.heart_rate_prediction.provenance.window_index;
  await page.setViewportSize(matrix[0]);
  await settle(page, "/mission-overview");
  await page.waitForFunction(() => document.body.innerText.includes("S14") && document.body.innerText.includes("Model available"));
  await record(page, { id: "S10-S14-NOMINAL", filename: "s14-initial-replay.png", route: "/mission-overview", viewport: matrix[0], state: "recorded_replay_nominal", sourceIdentity: "PPG-DaLiA/S14", runtime: { hr_bpm: nominal.heart_rate_prediction.value, window_index: nominalWindow, model_id: nominal.heart_rate_prediction.provenance.model_id } });

  await api("/data-source/replay/fault", { method: "POST", body: JSON.stringify({ fault_type: "modality_dropout", target: "ppg", severity: 1, seed: 10 }) });
  const fault = await waitForMetric((value) => value.fault_injection?.active && value.heart_rate_prediction == null, "PPG fault");
  await page.waitForFunction(() => /SIMULATED FAULT/.test(document.body.innerText) && /Output withheld|Input unavailable|Model input unavailable/i.test(document.body.innerText));
  await record(page, { id: "S10-S14-FAULT", filename: "s14-injected-dropout.png", route: "/mission-overview", viewport: matrix[0], state: "ppg_fault_active", sourceIdentity: "PPG-DaLiA/S14", runtime: { inference_status: fault.heart_rate_inference?.status, prediction: null } });
  await record(page, { id: "S10-S14-WITHHELD", filename: "s14-output-withheld.png", route: "/mission-overview", viewport: matrix[0], state: "hr_output_withheld", sourceIdentity: "PPG-DaLiA/S14", runtime: { prediction: null } });

  await api("/data-source/replay/fault", { method: "DELETE" });
  const rebuilding = await waitForMetric((value) => !value.fault_injection?.active && value.heart_rate_inference?.status === "warming_up" && value.heart_rate_prediction == null, "rebuilding", 10_000);
  await page.waitForFunction(() => /Rebuilding|warming|waiting for an 8 s/i.test(document.body.innerText));
  await record(page, { id: "S10-S14-REBUILDING", filename: "s14-warmup.png", route: "/mission-overview", viewport: matrix[0], state: "rebuilding", sourceIdentity: "PPG-DaLiA/S14", runtime: { inference_status: rebuilding.heart_rate_inference.status, prediction: null } });
  const recovered = await waitForMetric((value) => !value.fault_injection?.active && Number.isFinite(value.heart_rate_prediction?.value) && value.heart_rate_prediction.provenance.window_index > nominalWindow, "fresh recovery");
  check("recovered HR is fresh", recovered.heart_rate_prediction.provenance.window_index > nominalWindow);
  await page.waitForFunction(() => document.body.innerText.includes("Model available") && /bpm/.test(document.body.innerText));
  await record(page, { id: "S10-S14-RECOVERY", filename: "s14-fresh-output.png", route: "/mission-overview", viewport: matrix[0], state: "fresh_recovered_hr", sourceIdentity: "PPG-DaLiA/S14", runtime: { nominal_window_index: nominalWindow, recovered_window_index: recovered.heart_rate_prediction.provenance.window_index, hr_bpm: recovered.heart_rate_prediction.value } });

  const juryViewport = { width: 1920, height: 1080 };
  await page.setViewportSize(juryViewport);
  const start = Date.now();
  for (const [code, route] of routes) {
    await settle(page, route);
    routeMarkers.push({ route, elapsed_ms: Date.now() - start, timestamp: new Date().toISOString() });
    await record(page, { id: `S10-JURY-${code.toUpperCase()}`, filename: `jury-${code}-1920x1080.png`, route, viewport: juryViewport, state: "continuous_jury_walkthrough", sourceIdentity: route === "/mission-overview" || route === "/live-monitoring" || route === "/ai-insights" || route === "/mission-timeline" ? "PPG-DaLiA/S14" : "NOT_APPLICABLE", fullPage: false });
  }
  routeMarkers.push({ route: "COMPLETE", elapsed_ms: Date.now() - start, timestamp: new Date().toISOString() });
  await context.close();
}

async function publicRun(browser) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  wireDiagnostics(page);
  const started = Date.now();
  await settle(page, "/mission-overview", 120_000);
  await page.waitForFunction(() => document.body.innerText.includes("PUBLIC") && document.body.innerText.includes("S14"), null, { timeout: 120_000 });
  const body = await page.locator("body").innerText();
  check("public page is read-only", /PUBLIC.*READ-ONLY/i.test(body));
  check("public page reports S14", body.includes("S14"));
  await record(page, { id: "S10-PUBLIC-SMOKE", filename: "public-mission-overview.png", route: "/mission-overview", viewport: { width: 1440, height: 900 }, state: "public_connected_read_only", sourceIdentity: "PPG-DaLiA/S14", runtime: { usable_after_ms: Date.now() - started } });
  await context.close();
}

async function disconnectedRun(browser) {
  const viewport = { width: 1440, height: 900 };
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  wireDiagnostics(page);
  await page.goto(`${FRONTEND}/mission-overview`, { waitUntil: "domcontentloaded", timeout: 30_000 });
  await page.locator("h1").first().waitFor({ state: "visible", timeout: 15_000 });
  await page.waitForFunction(
    () => /DISCONNECTED|Unavailable|Connection lost|reconnecting/i.test(document.body.innerText),
    null,
    { timeout: 30_000 },
  );
  const body = await page.locator("body").innerText();
  check("disconnected state is explicit", /DISCONNECTED|Unavailable|Connection lost|reconnecting/i.test(body));
  await record(page, {
    id: "S10-DISCONNECTED",
    filename: "backend-unavailable.png",
    route: "/mission-overview",
    viewport,
    state: "backend_unavailable_disconnected",
    sourceIdentity: "UNAVAILABLE",
  });
  await context.close();
}

async function reviewEvidence() {
  const manifest = JSON.parse(await readFile(MANIFEST, "utf8"));
  for (const artifact of manifest.artifacts) {
    const filename = artifact.relative_path.split("/").at(-1);
    const bytes = await readFile(resolve(OUTPUT, filename));
    const metadata = await sharp(bytes).metadata();
    if (metadata.format !== "png" || bytes.length !== artifact.byte_size) {
      throw new Error(`Evidence changed or is not a PNG: ${artifact.artifact_id}`);
    }
    if (createHash("sha256").update(bytes).digest("hex") !== artifact.sha256) {
      throw new Error(`Evidence hash changed: ${artifact.artifact_id}`);
    }
    artifact.visual_review = "PASS";
  }
  manifest.visual_reviewed_at = new Date().toISOString();
  manifest.visual_review_method = "human_review_of_contact_sheet_and_representative_full_resolution_artifacts";
  await writeFile(MANIFEST, `${JSON.stringify(manifest, null, 2)}\n`);
  console.log(`capture-stage10-release-evidence: reviewed ${manifest.artifacts.length} immutable PNGs`);
}

async function main() {
  await mkdir(OUTPUT, { recursive: true });
  if (MODE === "review") {
    await reviewEvidence();
    return;
  }
  const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: ["--use-angle=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  if (MODE === "public") await publicRun(browser);
  else if (MODE === "disconnected") await disconnectedRun(browser);
  else await localRun(browser);
  await browser.close();
  if (MODE === "disconnected") {
    expectedTransportErrors.push(...consoleErrors.splice(0));
    check("disconnected transport failure was observed", expectedTransportErrors.length > 0, JSON.stringify(expectedTransportErrors));
  }
  check("no browser console/page errors", consoleErrors.length === 0, JSON.stringify(consoleErrors));
  let previous = null;
  if (MODE !== "local") previous = JSON.parse(await readFile(MANIFEST, "utf8"));
  const manifest = {
    schema_version: 1,
    stage: 10,
    run_mode: previous ? `${previous.run_mode}+${MODE}` : MODE,
    frontend_origin: previous?.frontend_origin ?? FRONTEND,
    backend_origin: previous?.backend_origin ?? (MODE === "public" ? "public_read_only" : BACKEND),
    generated_at: new Date().toISOString(),
    actual_voiceover_status: "DEFERRED_BY_OWNER_TO_POST_STAGE10",
    supplemental_origins: [...(previous?.supplemental_origins ?? []), ...(MODE === "local" ? [] : [{ mode: MODE, frontend: FRONTEND, backend: MODE === "public" ? "public_read_only" : BACKEND }])],
    artifacts: [...(previous?.artifacts ?? []), ...artifacts],
    checks: [...(previous?.checks ?? []), ...checks],
    route_markers: [...(previous?.route_markers ?? []), ...routeMarkers],
    console_errors: [...(previous?.console_errors ?? []), ...consoleErrors],
    expected_transport_errors: [...(previous?.expected_transport_errors ?? []), ...expectedTransportErrors],
  };
  await writeFile(MANIFEST, `${JSON.stringify(manifest, null, 2)}\n`);
  console.log(`capture-stage10-release-evidence: ${artifacts.length} PNGs, ${checks.length} checks, mode=${MODE}`);
}

main().catch(async (error) => {
  await mkdir(OUTPUT, { recursive: true });
  await writeFile(resolve(OUTPUT, "capture-failure.json"), `${JSON.stringify({ error: String(error), stack: error?.stack, checks, artifacts, consoleErrors }, null, 2)}\n`).catch(() => {});
  console.error(error);
  process.exit(1);
});
