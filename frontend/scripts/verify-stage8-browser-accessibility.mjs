#!/usr/bin/env node

/** Browser accessibility-tree and keyboard-contract evidence for Stage 8. */

import { writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import process from "node:process";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const FRONTEND = process.env.STAGE8_FRONTEND_URL ?? "http://127.0.0.1:3168";
const CHROME = process.env.STAGE8_CHROME_BIN ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const OUTPUT = resolve(process.cwd(), "qa-screenshots/codex-stage8-final-evidence-closure/accessibility-runtime-results.json");
const routes = [
  "/mission-overview",
  "/live-monitoring",
  "/system-brief",
  "/research/experimental",
  "/digital-twin",
  "/ai-insights",
  "/mission-timeline",
  "/settings",
];

const checks = [];
const routeResults = [];

function check(name, condition, detail = "") {
  checks.push({ name, result: condition ? "PASS" : "FAIL", detail });
}

function valueOf(property) {
  return property?.value?.value ?? property?.value ?? "";
}

const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const browserVersion = await browser.version();
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();

for (const route of routes) {
  await page.goto(`${FRONTEND}${route}`, { waitUntil: "networkidle", timeout: 30000 });
  await page.locator("h1").first().waitFor({ state: "visible", timeout: 15000 });
  const session = await context.newCDPSession(page);
  await session.send("Accessibility.enable");
  const { nodes } = await session.send("Accessibility.getFullAXTree", { depth: -1 });
  const included = nodes.filter((node) => !node.ignored);
  const byRole = Object.groupBy(included, (node) => String(valueOf(node.role)).toLowerCase());
  const emptyNamedControls = included
    .filter((node) => ["button", "link", "switch", "tab", "checkbox", "combobox"].includes(String(valueOf(node.role)).toLowerCase()))
    .filter((node) => !String(valueOf(node.name)).trim())
    .map((node) => ({ role: valueOf(node.role), backendDOMNodeId: node.backendDOMNodeId }));
  const result = {
    route,
    total_ax_nodes: nodes.length,
    exposed_ax_nodes: included.length,
    roles: Object.fromEntries(Object.entries(byRole).map(([role, entries]) => [role, entries.length])),
    empty_named_controls: emptyNamedControls,
  };
  routeResults.push(result);
  check(`${route}: browser AX tree has document`, Boolean(byRole.document?.length || byRole.webarea?.length || byRole.rootwebarea?.length), JSON.stringify(result.roles));
  check(`${route}: browser AX tree has main landmark`, Boolean(byRole.main?.length), JSON.stringify(result.roles));
  check(`${route}: browser AX tree has navigation landmark`, Boolean(byRole.navigation?.length), JSON.stringify(result.roles));
  check(`${route}: browser AX tree has heading`, Boolean(byRole.heading?.length), JSON.stringify(result.roles));
  check(`${route}: exposed interactive controls are named`, emptyNamedControls.length === 0, JSON.stringify(emptyNamedControls));
  if (["/mission-overview", "/system-brief", "/research/experimental"].includes(route)) {
    check(`${route}: data table is represented in browser AX tree`, Boolean(byRole.table?.length), JSON.stringify(result.roles));
  }
  await session.detach();
}

check("cross-route AX inventory includes tables", routeResults.some((result) => (result.roles.table ?? 0) > 0));
check("cross-route AX inventory includes named buttons", routeResults.some((result) => (result.roles.button ?? 0) > 0));
check("cross-route AX inventory includes live status semantics", routeResults.some((result) => (result.roles.status ?? 0) > 0));

await page.goto(`${FRONTEND}/mission-overview`, { waitUntil: "networkidle", timeout: 30000 });
const trigger = page.getByRole("button", { name: /Demo controls/i });
await trigger.focus();
check("keyboard: trigger receives focus", await page.evaluate(() => document.activeElement?.getAttribute("aria-controls") === "demo-control-drawer"));
await page.keyboard.press("Enter");
const dialog = page.getByRole("dialog", { name: /Source, replay & fault/i });
check("keyboard: Enter opens named dialog", await dialog.isVisible());
await page.keyboard.press("Shift+Tab");
check("keyboard: dialog traps reverse tab", await page.evaluate(() => Boolean(document.activeElement?.closest("[role='dialog']"))));
await page.keyboard.press("Escape");
check("keyboard: Escape closes dialog", !(await dialog.isVisible().catch(() => false)));
check("keyboard: focus returns to trigger", await page.evaluate(() => document.activeElement?.getAttribute("aria-controls") === "demo-control-drawer"));

await browser.close();
const failed = checks.filter((entry) => entry.result === "FAIL");
await writeFile(OUTPUT, `${JSON.stringify({
  schema_version: 1,
  run_timestamp: new Date().toISOString(),
  browser: `Google Chrome ${browserVersion}`,
  protocol: "Chrome DevTools Protocol Accessibility.getFullAXTree",
  routes: routeResults,
  checks,
  passed: checks.length - failed.length,
  failed: failed.length,
}, null, 2)}\n`);

console.log(`verify-stage8-browser-accessibility: PASS=${checks.length - failed.length} FAIL=${failed.length} ROUTES=${routes.length}`);
if (failed.length) {
  for (const entry of failed) console.error(`FAIL: ${entry.name}${entry.detail ? ` — ${entry.detail}` : ""}`);
  process.exit(1);
}
