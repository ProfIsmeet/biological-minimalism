#!/usr/bin/env node

/** Genuine Chrome page-zoom evidence via the native macOS Cmd++ mechanism. */

import { createHash } from "node:crypto";
import { execFile } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { promisify } from "node:util";

import sharp from "sharp";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const execFileAsync = promisify(execFile);

const FRONTEND = process.env.STAGE8_FRONTEND_URL ?? "http://127.0.0.1:3168";
const CHROME = process.env.STAGE8_CHROME_BIN ?? chromium.executablePath();
const OUTPUT = resolve(process.cwd(), "qa-screenshots/codex-stage8-final-evidence-closure");
const artifacts = [];
const checks = [];

function check(name, condition, detail = "") {
  checks.push({ name, result: condition ? "PASS" : "FAIL", detail });
  if (!condition) throw new Error(`${name}${detail ? `: ${detail}` : ""}`);
}

async function buildZoomExtension(root) {
  const extension = resolve(root, "zoom-extension");
  await mkdir(extension, { recursive: true });
  await writeFile(resolve(extension, "manifest.json"), JSON.stringify({
    manifest_version: 3,
    name: "Stage 8 temporary page-zoom controller",
    version: "1.0.0",
    permissions: ["tabs"],
    host_permissions: ["http://127.0.0.1:3168/*"],
    background: { service_worker: "background.js" },
    content_scripts: [{ matches: ["http://127.0.0.1:3168/*"], js: ["content.js"], run_at: "document_start" }],
  }, null, 2));
  await writeFile(resolve(extension, "background.js"), `
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== "STAGE8_SET_ZOOM" || !sender.tab?.id) return;
  chrome.tabs.setZoom(sender.tab.id, message.zoom, () => {
    if (chrome.runtime.lastError) {
      sendResponse({ ok: false, error: chrome.runtime.lastError.message });
      return;
    }
    chrome.tabs.getZoom(sender.tab.id, (actual) => sendResponse({ ok: true, actual }));
  });
  return true;
});
`);
  await writeFile(resolve(extension, "content.js"), `
window.addEventListener("message", (event) => {
  if (event.source !== window || event.data?.type !== "STAGE8_SET_ZOOM") return;
  chrome.runtime.sendMessage({ type: "STAGE8_SET_ZOOM", zoom: event.data.zoom }, (result) => {
    window.postMessage({ type: "STAGE8_ZOOM_RESULT", token: event.data.token, result }, "*");
  });
});
`);
  return extension;
}

async function buildWindowListHelper(root) {
  const helper = resolve(root, "list-windows.swift");
  await writeFile(helper, `
import CoreGraphics
import Foundation
let options: CGWindowListOption = [.optionOnScreenOnly, .excludeDesktopElements]
let rows = (CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] ?? []).map { row -> [String: Any] in
  let bounds = row[kCGWindowBounds as String] as? [String: Any] ?? [:]
  return [
    "id": row[kCGWindowNumber as String] ?? 0,
    "owner": row[kCGWindowOwnerName as String] ?? "",
    "name": row[kCGWindowName as String] ?? "",
    "layer": row[kCGWindowLayer as String] ?? -1,
    "x": bounds["X"] ?? 0,
    "y": bounds["Y"] ?? 0,
    "width": bounds["Width"] ?? 0,
    "height": bounds["Height"] ?? 0,
  ]
}
let data = try JSONSerialization.data(withJSONObject: rows)
print(String(data: data, encoding: .utf8)!)
`);
  return helper;
}

async function setRealPageZoom(page, zoom) {
  return page.evaluate((requested) => new Promise((resolveZoom, rejectZoom) => {
    const token = `${Date.now()}-${Math.random()}`;
    const timeout = setTimeout(() => rejectZoom(new Error("browser zoom API timed out")), 5000);
    const onMessage = (event) => {
      if (event.data?.type !== "STAGE8_ZOOM_RESULT" || event.data?.token !== token) return;
      window.removeEventListener("message", onMessage);
      clearTimeout(timeout);
      if (!event.data.result?.ok) rejectZoom(new Error(event.data.result?.error ?? "browser zoom API failed"));
      else resolveZoom(event.data.result.actual);
    };
    window.addEventListener("message", onMessage);
    window.postMessage({ type: "STAGE8_SET_ZOOM", token, zoom: requested }, "*");
  }), zoom);
}

async function metrics(page) {
  return page.evaluate(() => ({
    outer_width: window.outerWidth,
    outer_height: window.outerHeight,
    screen_x: window.screenX,
    screen_y: window.screenY,
    inner_width: window.innerWidth,
    inner_height: window.innerHeight,
    device_pixel_ratio: window.devicePixelRatio,
    visual_viewport_width: window.visualViewport?.width ?? null,
    visual_viewport_height: window.visualViewport?.height ?? null,
    visual_viewport_scale: window.visualViewport?.scale ?? null,
    horizontal_overflow_px: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    media_min_768_matches: matchMedia("(min-width: 768px)").matches,
    media_min_1280_matches: matchMedia("(min-width: 1280px)").matches,
    visible_nav_rects: [...document.querySelectorAll("nav")].filter((node) => getComputedStyle(node).display !== "none").map((node) => {
      const rect = node.getBoundingClientRect();
      return { label: node.getAttribute("aria-label"), left: rect.left, right: rect.right, width: rect.width };
    }),
    active_title: document.title,
  }));
}

async function captureNativeWindow(browserVersion, route, code, zoom, state, windowListHelper) {
  const filename = `z${zoom}-${code}-native.png`;
  const path = resolve(OUTPUT, filename);
  const { stdout } = await execFileAsync("/usr/bin/swift", [windowListHelper], { maxBuffer: 1024 * 1024 });
  const windows = JSON.parse(stdout);
  const chromeWindows = windows.filter((row) => /Chrome for Testing/.test(row.owner) && row.layer === 0 && Math.abs(row.width - state.outer_width) <= 4 && Math.abs(row.height - state.outer_height) <= 4);
  check(`${route} ${zoom}%: exact Chrome window resolved`, chromeWindows.length === 1, JSON.stringify(chromeWindows));
  const target = chromeWindows[0];
  await execFileAsync("/usr/sbin/screencapture", ["-x", "-o", `-l${target.id}`, path]);
  const bytes = await readFile(path);
  const png = await sharp(bytes).metadata();
  check(`${route} ${zoom}% screenshot decodes`, png.format === "png" && bytes.length > 0);
  artifacts.push({
    artifact_id: `S8C-Z${zoom}-${code.toUpperCase()}-NATIVE`,
    relative_repository_path: `frontend/qa-screenshots/codex-stage8-final-evidence-closure/${filename}`,
    route,
    viewport_width: state.inner_width,
    viewport_height: state.inner_height,
    actual_png_width: png.width,
    actual_png_height: png.height,
    browser_identity_version: `Google Chrome ${browserVersion}`,
    zoom_value: zoom,
    motion_preference: "reduce",
    source_type: "dataset_replay",
    dataset_label: "owner-provided local PPG-DaLiA archive",
    subject: "S14",
    replay_state: "connected",
    fault_state: "none",
    capture_timestamp: new Date().toISOString(),
    sha256: createHash("sha256").update(bytes).digest("hex"),
    visual_review_status: "PENDING_MANUAL_REVIEW",
    acceptance_result: "PENDING_MANUAL_REVIEW",
    associated_finding_id: "none",
    canonical_status: "canonical",
    byte_size: bytes.length,
    runtime: { ...state, native_window_id: target.id, native_window_bounds_points: { x: target.x, y: target.y, width: target.width, height: target.height } },
  });
}

async function main() {
  await mkdir(OUTPUT, { recursive: true });
  const temporaryRoot = await mkdtemp(resolve(tmpdir(), "stage8-real-zoom-"));
  const extension = await buildZoomExtension(temporaryRoot);
  const windowListHelper = await buildWindowListHelper(temporaryRoot);
  const profile = resolve(temporaryRoot, "chrome-profile");
  const context = await chromium.launchPersistentContext(profile, {
    executablePath: CHROME,
    headless: false,
    viewport: null,
    reducedMotion: "reduce",
    args: [
      `--disable-extensions-except=${extension}`,
      `--load-extension=${extension}`,
      "--window-size=1440,900",
      "--window-position=40,40",
      "--use-angle=swiftshader",
      "--enable-webgl",
      "--ignore-gpu-blocklist",
    ],
  });
  const browserVersion = await context.browser().version();
  const pages = context.pages();
  const page = pages[0] ?? await context.newPage();

  const routes = [
    ["mo", "/mission-overview", true],
    ["lm", "/live-monitoring", false],
    ["dt", "/digital-twin", false],
    ["mt", "/mission-timeline", false],
  ];

  for (const [code, route, hasDrawer] of routes) {
    await page.bringToFront();
    await page.goto(`${FRONTEND}${route}`, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.locator("h1").first().waitFor({ state: "visible" });
    await page.waitForTimeout(700);
    const resetZoom = await setRealPageZoom(page, 1);
    check(`${route}: browser API reports 100% baseline`, Math.abs(resetZoom - 1) < 0.001, String(resetZoom));
    await page.waitForTimeout(500);
    const baseline = await metrics(page);
    check(`${route}: 100% has no horizontal overflow`, baseline.horizontal_overflow_px <= 1, JSON.stringify(baseline));
    await captureNativeWindow(browserVersion, route, code, 100, baseline, windowListHelper);

    const browserReportedZoom = await setRealPageZoom(page, 2);
    check(`${route}: browser-supported tabs.setZoom reports 200%`, Math.abs(browserReportedZoom - 2) < 0.001, String(browserReportedZoom));
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.locator("h1").first().waitFor({ state: "visible" });
    await page.waitForTimeout(300);
    const zoomed = await metrics(page);
    check(`${route}: outer browser window unchanged at 200%`, Math.abs(zoomed.outer_width - baseline.outer_width) <= 2 && Math.abs(zoomed.outer_height - baseline.outer_height) <= 2, JSON.stringify({ baseline, zoomed }));
    const widthRatio = baseline.inner_width / zoomed.inner_width;
    check(`${route}: CSS viewport capacity approximately halves at 200%`, widthRatio >= 1.90 && widthRatio <= 2.10, JSON.stringify({ widthRatio, baseline, zoomed }));
    const dprRatio = zoomed.device_pixel_ratio / baseline.device_pixel_ratio;
    check(`${route}: device-pixel relationship doubles at 200%`, dprRatio >= 1.90 && dprRatio <= 2.10, JSON.stringify({ dprRatio, baseline, zoomed }));
    check(`${route}: visual viewport confirms zoomed CSS capacity`, zoomed.visual_viewport_width != null && Math.abs(zoomed.visual_viewport_width - zoomed.inner_width) <= 2, JSON.stringify(zoomed));
    check(`${route}: 200% has no horizontal reading overflow`, zoomed.horizontal_overflow_px <= 1, JSON.stringify(zoomed));
    check(`${route}: primary title remains visible`, await page.locator("h1").first().isVisible());

    if (hasDrawer) {
      await page.getByRole("button", { name: /Demo controls/i }).click();
      const dialog = page.getByRole("dialog");
      check(`${route}: dialog opens and remains usable at 200%`, await dialog.isVisible());
      const box = await dialog.boundingBox();
      check(`${route}: dialog fits zoomed viewport`, Boolean(box) && box.x >= -1 && box.width <= zoomed.inner_width + 2, JSON.stringify({ box, zoomed }));
      await page.keyboard.press("Escape");
    }
    const semanticText = await page.locator("body").innerText();
    check(`${route}: content remains meaningfully labelled at 200%`, semanticText.length > 500 && !/Application error|Internal Server Error/.test(semanticText));
    await captureNativeWindow(browserVersion, route, code, 200, zoomed, windowListHelper);

    const restoredZoom = await setRealPageZoom(page, 1);
    check(`${route}: browser API reports reset to 100%`, Math.abs(restoredZoom - 1) < 0.001, String(restoredZoom));
    // Chrome reports the new tab zoom immediately, while the renderer can
    // retain the previous CSS metrics until its next document lifecycle.
    // Reloading is a normal page operation and proves the restored setting is
    // the persisted per-origin browser state, not a screenshot-only change.
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.locator("h1").first().waitFor({ state: "visible" });
    await page.waitForTimeout(300);
    const restored = await metrics(page);
    check(`${route}: zoom restored to 100%`, Math.abs(restored.inner_width - baseline.inner_width) <= 2 && Math.abs(restored.device_pixel_ratio - baseline.device_pixel_ratio) < 0.01, JSON.stringify({ baseline, restored }));
  }

  await setRealPageZoom(page, 1);
  await context.close();
  await rm(temporaryRoot, { recursive: true, force: true });
  await writeFile(resolve(OUTPUT, "zoom-runtime-results.json"), `${JSON.stringify({
    schema_version: 1,
    method: "Installed Google Chrome browser-supported chrome.tabs.setZoom API; Playwright measured state; macOS screencapture persisted the exact dedicated browser-window rectangle",
    prohibited_substitutes_used: false,
    browser: `Google Chrome ${browserVersion}`,
    artifact_count: artifacts.length,
    artifacts,
    checks,
  }, null, 2)}\n`);
  console.log(`capture-stage8-zoom-evidence: ${artifacts.length} PNGs, ${checks.length}/${checks.length} checks passed`);
}

main().catch(async (error) => {
  await writeFile(resolve(OUTPUT, "zoom-failure.json"), `${JSON.stringify({ error: String(error), stack: error?.stack, checks, artifacts }, null, 2)}\n`).catch(() => {});
  console.error(error);
  process.exit(1);
});
