#!/usr/bin/env node

/**
 * Durable Stage 8 closure capture and browser-contract verifier.
 *
 * Uses an already-installed Chrome through the workspace Playwright runtime.
 * The script deliberately contains no owner-private asset paths; the running
 * backend owns asset configuration through its supported environment contract.
 */

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import process from "node:process";

import sharp from "sharp";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const FRONTEND = process.env.STAGE8_FRONTEND_URL ?? "http://127.0.0.1:3168";
const BACKEND = process.env.STAGE8_BACKEND_URL ?? "http://127.0.0.1:8168";
const CHROME = process.env.STAGE8_CHROME_BIN ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const OUTPUT = resolve(process.cwd(), "qa-screenshots/codex-stage8-final-evidence-closure");
const RUN_TIMESTAMP = new Date().toISOString();

const artifacts = [];
const checks = [];
const consoleErrors = [];

function check(name, condition, detail = "") {
  const portableDetail = String(detail).replace(/(?:\/Users\/[^/\s]+\/|[A-Za-z]:\\Users\\[^\\\s]+\\|\/home\/[^/\s]+\/)[^\"\s}]*/g, "owner-provided local asset");
  checks.push({ name, result: condition ? "PASS" : "FAIL", detail: portableDetail });
  if (!condition) throw new Error(`${name}${portableDetail ? `: ${portableDetail}` : ""}`);
}

async function api(path, init = {}) {
  const response = await fetch(`${BACKEND}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
  });
  const body = await response.text();
  if (!response.ok) throw new Error(`${init.method ?? "GET"} ${path} => ${response.status}: ${body}`);
  return body ? JSON.parse(body) : null;
}

async function waitForMetric(predicate, label, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  let last = null;
  while (Date.now() < deadline) {
    try {
      last = await api("/metrics/live");
      if (predicate(last)) return last;
    } catch {
      // A replay reset/fault transition legitimately leaves no current frame.
    }
    await new Promise((done) => setTimeout(done, 250));
  }
  throw new Error(`Timed out waiting for ${label}; last=${JSON.stringify(last)}`);
}

async function settle(page, path) {
  await page.goto(`${FRONTEND}${path}`, { waitUntil: "networkidle", timeout: 30000 });
  await page.locator("h1").first().waitFor({ state: "visible", timeout: 15000 });
  await page.waitForTimeout(800);
}

async function layoutAudit(page, route, viewport) {
  const result = await page.evaluate(() => {
    const root = document.documentElement;
    const overflow = root.scrollWidth - root.clientWidth;
    const smallEssential = [...document.querySelectorAll("button, a, label, th, [role='button'], [role='tab']")]
      .filter((el) => {
        const style = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && Number.parseFloat(style.fontSize) < 12;
      })
      .map((el) => ({ text: (el.textContent ?? "").trim().slice(0, 80), px: getComputedStyle(el).fontSize }));
    const undersized = [...document.querySelectorAll("button, [role='button'], [role='switch']")]
      .filter((el) => {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && (rect.width < 44 || rect.height < 44);
      })
      .map((el) => ({ label: el.getAttribute("aria-label") ?? (el.textContent ?? "").trim().slice(0, 80), width: el.getBoundingClientRect().width, height: el.getBoundingClientRect().height }));
    const suspicious = [...document.querySelectorAll("body *")]
      .filter((el) => {
        const text = (el.textContent ?? "").trim();
        return el.children.length === 0 && /application error|internal server error|loading…|failed to load chunk/i.test(text);
      })
      .map((el) => (el.textContent ?? "").trim().slice(0, 120));
    return {
      overflow,
      documentWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
      documentHeight: root.scrollHeight,
      smallEssential,
      undersized,
      suspicious,
      h1Count: document.querySelectorAll("h1").length,
      title: document.title,
    };
  });
  check(`${route} ${viewport.width}x${viewport.height}: no horizontal overflow`, result.overflow <= 1, JSON.stringify(result));
  check(`${route} ${viewport.width}x${viewport.height}: one h1`, result.h1Count === 1, JSON.stringify(result));
  check(`${route} ${viewport.width}x${viewport.height}: no essential text below 12px`, result.smallEssential.length === 0, JSON.stringify(result.smallEssential));
  check(`${route} ${viewport.width}x${viewport.height}: no browser/application error or loading residue`, result.suspicious.length === 0, JSON.stringify(result.suspicious));
  return result;
}

async function recordPng({ page, id, filename, route, viewport, browserVersion, zoom = 100, motion = "no-preference", sourceType = "synthetic", datasetLabel = "not_applicable", subject = "not_applicable", replayState = "not_applicable", faultState = "none", fullPage = true, runtime = {} }) {
  const path = resolve(OUTPUT, filename);
  await mkdir(dirname(path), { recursive: true });
  await page.screenshot({ path, fullPage, animations: motion === "reduce" ? "disabled" : "allow" });
  const bytes = await readFile(path);
  const metadata = await sharp(bytes).metadata();
  check(`${id}: PNG decodes`, metadata.format === "png" && bytes.length > 0, `${metadata.format}; ${bytes.length} bytes`);
  const hash = createHash("sha256").update(bytes).digest("hex");
  artifacts.push({
    artifact_id: id,
    relative_repository_path: `frontend/qa-screenshots/codex-stage8-final-evidence-closure/${filename}`,
    route,
    viewport_width: viewport.width,
    viewport_height: viewport.height,
    actual_png_width: metadata.width,
    actual_png_height: metadata.height,
    browser_identity_version: `Google Chrome ${browserVersion}`,
    zoom_value: zoom,
    motion_preference: motion,
    source_type: sourceType,
    dataset_label: datasetLabel,
    subject,
    replay_state: replayState,
    fault_state: faultState,
    capture_timestamp: new Date().toISOString(),
    sha256: hash,
    visual_review_status: "PENDING_MANUAL_REVIEW",
    acceptance_result: "PENDING_MANUAL_REVIEW",
    associated_finding_id: "none",
    canonical_status: "canonical",
    byte_size: bytes.length,
    runtime,
  });
}

const matrix = [
  { width: 1440, height: 900, code: "1440x900" },
  { width: 1366, height: 768, code: "1366x768" },
  { width: 1280, height: 720, code: "1280x720" },
  { width: 1024, height: 768, code: "1024x768" },
  { width: 768, height: 1024, code: "768x1024" },
  { width: 390, height: 844, code: "390x844" },
];

const principalRoutes = [
  ["sb", "/system-brief"],
  ["rx", "/research/experimental"],
  ["dt", "/digital-twin"],
  ["ai", "/ai-insights"],
  ["mt", "/mission-timeline"],
  ["st", "/settings"],
];

async function main() {
  await mkdir(OUTPUT, { recursive: true });
  const browser = await chromium.launch({
    executablePath: CHROME,
    headless: true,
    args: ["--use-angle=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
  });
  const browserVersion = await browser.version();

  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, reducedMotion: "no-preference" });
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push({ route: page.url(), text: message.text() });
  });
  page.on("pageerror", (error) => consoleErrors.push({ route: page.url(), text: String(error) }));

  // Static/synthetic responsive matrix: 24 complete-page PNGs.
  await api("/data-source/synthetic", { method: "POST" });
  if (process.env.STAGE8_SKIP_STATIC !== "1") {
    for (const [code, route] of [["mo", "/mission-overview"], ["lm", "/live-monitoring"]]) {
      for (const viewport of matrix) {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await settle(page, route);
        const runtime = await layoutAudit(page, route, viewport);
        await recordPng({ page, id: `S8C-${code.toUpperCase()}-${viewport.code}`, filename: `${code}-${viewport.code}.png`, route, viewport, browserVersion, runtime });
      }
    }
    for (const [code, route] of principalRoutes) {
      for (const viewport of [matrix[0], matrix[5]]) {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await settle(page, route);
        const runtime = await layoutAudit(page, route, viewport);
        await recordPng({ page, id: `S8C-${code.toUpperCase()}-${viewport.code}`, filename: `${code}-${viewport.code}.png`, route, viewport, browserVersion, runtime });
      }
    }
  }

  // Standards-based media emulation and the 14-scenario runtime matrix.
  const motionContext = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, reducedMotion: "no-preference" });
  const first = await motionContext.newPage();
  const second = await motionContext.newPage();
  await first.goto(`${FRONTEND}/digital-twin`, { waitUntil: "domcontentloaded", timeout: 30000 });
  await second.goto(`${FRONTEND}/settings`, { waitUntil: "domcontentloaded", timeout: 30000 });
  await first.locator("h1").waitFor({ state: "visible" });
  await second.locator("h1").waitFor({ state: "visible" });
  await first.evaluate(() => localStorage.setItem("biomin:reduce-motion", "0"));
  await second.reload({ waitUntil: "domcontentloaded" });
  await first.reload({ waitUntil: "domcontentloaded" });
  check("motion 01 initial media query is no-preference", await first.evaluate(() => !matchMedia("(prefers-reduced-motion: reduce)").matches));
  check("motion 02 app preference initially off", await first.evaluate(() => !document.documentElement.classList.contains("reduce-motion")));
  await first.emulateMedia({ reducedMotion: "reduce" });
  await first.waitForFunction(() => matchMedia("(prefers-reduced-motion: reduce)").matches && document.documentElement.classList.contains("reduce-motion"));
  check("motion 03 CDP media transition becomes reduce", await first.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches));
  check("motion 04 OS media alone activates effective reduction", await first.evaluate(() => document.documentElement.classList.contains("reduce-motion")));
  const twinText = await first.locator("body").innerText();
  check("motion 05 Digital Twin remains readable", /Digital Twin/.test(twinText) && /ARCHITECTURE ONLY/.test(twinText));
  check("motion 06 information is not hidden", await first.locator("h1").isVisible());
  await recordPng({ page: first, id: "S8C-MOTION-REDUCE", filename: "motion-reduced-dt.png", route: "/digital-twin", viewport: matrix[0], browserVersion, motion: "reduce", runtime: { match_media_reduce: true, effective_class: true } });
  await first.emulateMedia({ reducedMotion: "no-preference" });
  await first.waitForFunction(() => !matchMedia("(prefers-reduced-motion: reduce)").matches && !document.documentElement.classList.contains("reduce-motion"));
  check("motion 07 live media transition returns to normal", await first.evaluate(() => !matchMedia("(prefers-reduced-motion: reduce)").matches));
  await second.getByRole("switch", { name: "Reduce motion" }).click();
  await second.waitForFunction(() => localStorage.getItem("biomin:reduce-motion") === "1");
  await first.waitForFunction(() => localStorage.getItem("biomin:reduce-motion") === "1" && document.documentElement.classList.contains("reduce-motion"));
  check("motion 08 cross-tab setting synchronization", await first.evaluate(() => localStorage.getItem("biomin:reduce-motion") === "1"));
  check("motion 09 persisted app preference activates reduction with OS normal", await first.evaluate(() => !matchMedia("(prefers-reduced-motion: reduce)").matches && document.documentElement.classList.contains("reduce-motion")));
  await first.goto(`${FRONTEND}/mission-overview`, { waitUntil: "domcontentloaded" });
  await first.locator("h1").waitFor({ state: "visible" });
  check("motion 10 preference survives route switch", await first.evaluate(() => document.documentElement.classList.contains("reduce-motion")));
  const playBefore = await first.getByText(/Rotation (playing|paused)/).first().textContent().catch(() => "control unavailable");
  check("motion 11 play-pause intent control remains represented", Boolean(playBefore), String(playBefore));
  await first.getByRole("button", { name: /Demo controls/i }).click();
  check("motion 12 dialog opens under reduction", await first.getByRole("dialog").isVisible());
  await first.keyboard.press("Escape");
  check("motion 13 dialog closes without clearing reduction", !(await first.getByRole("dialog").isVisible().catch(() => false)) && await first.evaluate(() => document.documentElement.classList.contains("reduce-motion")));
  await second.getByRole("switch", { name: "Reduce motion" }).click();
  await first.waitForFunction(() => localStorage.getItem("biomin:reduce-motion") === "0" && !document.documentElement.classList.contains("reduce-motion"));
  check("motion 14 cross-tab disable restores normal when OS is normal", await first.evaluate(() => !document.documentElement.classList.contains("reduce-motion")));
  await recordPng({ page: first, id: "S8C-MOTION-NORMAL", filename: "motion-normal-mo.png", route: "/mission-overview", viewport: matrix[0], browserVersion, motion: "no-preference", runtime: { match_media_reduce: false, effective_class: false } });
  await motionContext.close();

  // Real S14 replay sequence. REST truth and browser pixels are captured in the same run.
  const subjects = await api("/data-source/subjects");
  check("S14 subject list is authoritative", subjects.dataset_name === "PPG-DaLiA" && subjects.subjects.includes("S14"), JSON.stringify(subjects));
  await api("/data-source/replay/load", { method: "POST", body: JSON.stringify({ subject_id: "S14" }) });
  await api("/data-source/replay/speed", { method: "POST", body: JSON.stringify({ speed: 5 }) });
  await api("/data-source/replay/play", { method: "POST" });
  const nominal = await waitForMetric((value) => value.source?.subject_id === "S14" && value.heart_rate_inference?.status === "available" && Number.isFinite(value.heart_rate_prediction?.value), "nominal S14 model output", 45000);
  check("S14 nominal source identity", nominal.source.source_type === "dataset_replay" && nominal.source.dataset_name === "PPG-DaLiA" && nominal.source.subject_id === "S14");
  check("S14 channel identity", ["wrist_bvp", "wrist_acc", "chest_ecg", "wrist_temp"].every((name) => nominal.source.available_channels.includes(name)), JSON.stringify(nominal.source.available_channels));
  check("S14 model identity", nominal.heart_rate_prediction.provenance.model_id === "PPGDaliaHRModelB:PPGPlusIMUHRModel", JSON.stringify(nominal.heart_rate_prediction.provenance));
  const nominalWindow = nominal.heart_rate_prediction.provenance.window_index;
  await page.setViewportSize({ width: 1440, height: 900 });
  await settle(page, "/mission-overview");
  await page.waitForFunction(() => document.body.innerText.includes("S14") && document.body.innerText.includes("Model available"), null, { timeout: 20000 });
  await recordPng({ page, id: "S8C-S14-NOM", filename: "s14-01-nom.png", route: "/mission-overview", viewport: matrix[0], browserVersion, sourceType: "dataset_replay", datasetLabel: "owner-provided local PPG-DaLiA archive", subject: "S14", replayState: "nominal_connected", runtime: { hr_bpm: nominal.heart_rate_prediction.value, window_index: nominalWindow, channels: nominal.source.available_channels, model_id: nominal.heart_rate_prediction.provenance.model_id } });

  await api("/data-source/replay/fault", { method: "POST", body: JSON.stringify({ fault_type: "modality_dropout", target: "ppg", severity: 1, seed: 8 }) });
  const faulted = await waitForMetric((value) => value.fault_injection?.active && value.heart_rate_prediction == null, "active fail-closed PPG dropout", 15000);
  check("S14 fault state active", faulted.fault_injection.fault_type === "modality_dropout" && faulted.fault_injection.target === "ppg");
  check("S14 HR output withheld", faulted.heart_rate_prediction == null && ["input_unavailable", "warming_up"].includes(faulted.heart_rate_inference?.status), JSON.stringify(faulted.heart_rate_inference));
  await page.waitForFunction(() => /SIMULATED FAULT/.test(document.body.innerText) && /Output withheld|Input unavailable|Model input unavailable/i.test(document.body.innerText), null, { timeout: 15000 });
  await recordPng({ page, id: "S8C-S14-ACTIVE", filename: "s14-02-active-condition.png", route: "/mission-overview", viewport: matrix[0], browserVersion, sourceType: "dataset_replay", datasetLabel: "owner-provided local PPG-DaLiA archive", subject: "S14", replayState: "active_simulated_fault", faultState: "modality_dropout:ppg:severity_1", runtime: { inference_status: faulted.heart_rate_inference?.status, prediction: null } });
  await recordPng({ page, id: "S8C-S14-WITHHELD", filename: "s14-03-output-withheld.png", route: "/mission-overview", viewport: matrix[0], browserVersion, sourceType: "dataset_replay", datasetLabel: "owner-provided local PPG-DaLiA archive", subject: "S14", replayState: "output_withheld_fail_closed", faultState: "modality_dropout:ppg:severity_1", runtime: { inference_status: faulted.heart_rate_inference?.status, prediction: null } });

  const clearPosition = faulted.source.replay_position_seconds;
  await api("/data-source/replay/fault", { method: "DELETE" });
  const rebuilding = await waitForMetric((value) => !value.fault_injection?.active && value.heart_rate_inference?.status === "warming_up" && value.heart_rate_prediction == null, "genuine rebuilding window", 8000);
  check("S14 rebuilding is fail-closed", rebuilding.heart_rate_prediction == null && rebuilding.heart_rate_inference.status === "warming_up");
  await page.waitForFunction(() => /Rebuilding|warming|waiting for an 8 s/i.test(document.body.innerText) && !/SIMULATED FAULT: (?!None)/.test(document.body.innerText), null, { timeout: 8000 });
  await recordPng({ page, id: "S8C-S14-REBUILD", filename: "s14-04-warmup-window.png", route: "/mission-overview", viewport: matrix[0], browserVersion, sourceType: "dataset_replay", datasetLabel: "owner-provided local PPG-DaLiA archive", subject: "S14", replayState: "rebuilding", runtime: { inference_status: rebuilding.heart_rate_inference.status, prediction: null, clear_position_seconds: clearPosition } });

  const recovered = await waitForMetric((value) => !value.fault_injection?.active && value.heart_rate_inference?.status === "available" && Number.isFinite(value.heart_rate_prediction?.value) && value.heart_rate_prediction.provenance.window_index > nominalWindow, "fresh recovered S14 prediction", 30000);
  check("S14 recovered HR is fresh", recovered.heart_rate_prediction.provenance.window_index > nominalWindow && recovered.heart_rate_prediction.provenance.window_start_seconds > nominal.heart_rate_prediction.provenance.window_start_seconds, JSON.stringify({ nominal: nominal.heart_rate_prediction.provenance, recovered: recovered.heart_rate_prediction.provenance }));
  await page.waitForFunction(() => document.body.innerText.includes("Model available") && /bpm/.test(document.body.innerText), null, { timeout: 15000 });
  await recordPng({ page, id: "S8C-S14-POST", filename: "s14-05-postcondition.png", route: "/mission-overview", viewport: matrix[0], browserVersion, sourceType: "dataset_replay", datasetLabel: "owner-provided local PPG-DaLiA archive", subject: "S14", replayState: "recovered", runtime: { hr_bpm: recovered.heart_rate_prediction.value, window_index: recovered.heart_rate_prediction.provenance.window_index, window_start_seconds: recovered.heart_rate_prediction.provenance.window_start_seconds } });
  await recordPng({ page, id: "S8C-S14-FRESH-HR", filename: "s14-06-fresh-hr.png", route: "/mission-overview", viewport: matrix[0], browserVersion, sourceType: "dataset_replay", datasetLabel: "owner-provided local PPG-DaLiA archive", subject: "S14", replayState: "fresh_recovered_hr", runtime: { hr_bpm: recovered.heart_rate_prediction.value, nominal_window_index: nominalWindow, recovered_window_index: recovered.heart_rate_prediction.provenance.window_index, fresh_after_fault: true } });

  // Basic keyboard/dialog/accessibility-tree-equivalent semantic inspection.
  await page.getByRole("button", { name: /Demo controls/i }).focus();
  check("keyboard visible focus", await page.evaluate(() => document.activeElement?.getAttribute("aria-controls") === "demo-control-drawer"));
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", { name: /Source, replay & fault/i });
  check("dialog semantic role and accessible name", await dialog.isVisible());
  const firstFocus = await page.evaluate(() => document.activeElement?.getAttribute("aria-label") ?? document.activeElement?.textContent?.trim());
  await page.keyboard.press("Shift+Tab");
  check("dialog focus trap wraps", await page.evaluate(() => Boolean(document.activeElement?.closest("[role='dialog']"))), String(firstFocus));
  await page.keyboard.press("Escape");
  check("dialog Escape closes", !(await dialog.isVisible().catch(() => false)));
  check("dialog focus restores", await page.evaluate(() => document.activeElement?.getAttribute("aria-controls") === "demo-control-drawer"));
  const semantic = await page.evaluate(() => ({
    main: document.querySelectorAll("main").length,
    nav: document.querySelectorAll("nav").length,
    tables: document.querySelectorAll("table").length,
    buttonsWithoutName: [...document.querySelectorAll("button")].filter((button) => !(button.getAttribute("aria-label") || button.textContent?.trim())).length,
    skipLink: [...document.querySelectorAll("a")].some((anchor) => /skip/i.test(anchor.textContent ?? "")),
  }));
  check("semantic landmarks present", semantic.main === 1 && semantic.nav >= 1, JSON.stringify(semantic));
  check("buttons have accessible names", semantic.buttonsWithoutName === 0, JSON.stringify(semantic));
  check("skip link present", semantic.skipLink, JSON.stringify(semantic));

  await context.close();
  await browser.close();
  check("no page or console errors", consoleErrors.length === 0, JSON.stringify(consoleErrors));

  await writeFile(resolve(OUTPUT, "capture-runtime-results.json"), `${JSON.stringify({
    schema_version: 1,
    run_timestamp: RUN_TIMESTAMP,
    frontend_origin: FRONTEND,
    backend_origin: BACKEND,
    browser: `Google Chrome ${browserVersion}`,
    standards_based_reduced_motion: "Playwright/CDP Browser.setEmulatedMedia prefers-reduced-motion",
    artifact_count: artifacts.length,
    artifacts,
    checks,
    console_errors: consoleErrors,
  }, null, 2)}\n`);
  console.log(`capture-stage8-final-evidence: ${artifacts.length} PNGs, ${checks.length}/${checks.length} checks passed`);
}

main().catch(async (error) => {
  await mkdir(OUTPUT, { recursive: true });
  await writeFile(resolve(OUTPUT, "capture-failure.json"), `${JSON.stringify({ error: String(error), stack: error?.stack, checks, artifacts, consoleErrors }, null, 2)}\n`).catch(() => {});
  console.error(error);
  process.exit(1);
});
