/**
 * Stage 8 §23 (partial) — rendered-route acceptance against a running server.
 *
 * WHAT THIS IS, AND WHAT IT IS NOT.
 *
 * The Stage 8 brief asks for browser acceptance across a viewport matrix with
 * screenshot evidence. No Chrome extension was connected in this environment,
 * so that capture could not be performed and is reported as blocked rather
 * than claimed. This script is the strongest evidence that COULD be gathered
 * honestly: it drives a real Next.js server over HTTP and asserts against the
 * HTML each route actually returns.
 *
 * It therefore proves: every route responds, renders its own title and
 * description, renders its expected content, and contains none of the §7
 * forbidden claims in its delivered markup. It CANNOT prove anything that
 * requires layout, paint, or interaction — no overflow check, no contrast
 * measurement, no focus-ring visibility, no hit-target geometry, no keyboard
 * traversal, no 200% zoom, and no screen-reader behaviour. Those remain
 * unverified, and the Stage 8 report says so explicitly.
 *
 * Usage: node scripts/verify-rendered-routes.mjs [baseUrl]
 */

const BASE = process.argv[2] ?? "http://127.0.0.1:3147";

let passed = 0;
const failures = [];

function check(name, ok, detail) {
  if (ok) {
    passed += 1;
  } else {
    failures.push(detail ? `${name} — ${detail}` : name);
  }
}

function checkIncludes(name, haystack, needle) {
  check(name, haystack.includes(needle), `missing ${JSON.stringify(needle)}`);
}

function checkExcludes(name, haystack, needle) {
  check(name, !haystack.includes(needle), `found forbidden ${JSON.stringify(needle)}`);
}

/**
 * Strip script/style and tags so copy assertions run against VISIBLE text.
 * Without this, a forbidden phrase appearing only inside the RSC payload or a
 * source comment would read as a user-facing claim, and a phrase that is
 * genuinely rendered could be missed because tags split it.
 */
function visibleText(html) {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&#x27;|&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&nbsp;/g, " ")
    .replace(/&middot;|&#183;/g, "·")
    .replace(/\s+/g, " ");
}

const ROUTES = [
  { path: "/mission-overview", title: "Mission", expect: [] },
  { path: "/live-monitoring", title: "Signal and Inference Monitor", expect: ["Signal and inference monitor", "not live astronaut monitoring"] },
  { path: "/system-brief", title: "System Brief", expect: ["CORE_PLUS_CONTEXT"] },
  { path: "/research/experimental", title: "Experimental Research", expect: [] },
  { path: "/ai-insights", title: "AI Insights", expect: ["AI Insights", "currently selected"] },
  { path: "/mission-timeline", title: "Mission Timeline", expect: ["Mission Timeline", "Session event chronology", "Not session data"] },
  { path: "/digital-twin", title: "Digital Twin", expect: ["ARCHITECTURE ONLY", "UNTRAINED", "UNVALIDATED"] },
  { path: "/settings", title: "Settings", expect: ["Settings", "Demo controls drawer"] },
];

/**
 * §7 truth locks, as phrases that must not appear in any route's VISIBLE
 * text. Each is a claim this product is not entitled to make.
 */
const FORBIDDEN_VISIBLE = [
  "% Adapted",
  "Overall Adaptation",
  "Adaptation Score",
  "0 bpm",
  "clinically validated",
  "spaceflight validated",
  "population validated",
  "astronaut telemetry",
];

const results = [];

for (const route of ROUTES) {
  const url = `${BASE}${route.path}`;
  let response;
  try {
    response = await fetch(url, { redirect: "follow" });
  } catch (error) {
    check(`${route.path}: responds`, false, String(error));
    continue;
  }
  const html = await response.text();
  const text = visibleText(html);
  results.push({ path: route.path, status: response.status, bytes: html.length });

  check(`${route.path}: responds 200`, response.status === 200, `got ${response.status}`);

  // Every route must own its <title>, not inherit the layout default. A route
  // with no title of its own is indistinguishable from another in a tab strip
  // or a bookmark list.
  const titleMatch = html.match(/<title>([^<]*)<\/title>/);
  check(`${route.path}: renders a <title>`, Boolean(titleMatch), "no <title> element");
  if (titleMatch) {
    check(
      `${route.path}: the title names this route ("${titleMatch[1]}")`,
      titleMatch[1].includes(route.title),
      `expected to contain ${JSON.stringify(route.title)}`,
    );
  }

  // §16 — a route without its OWN description is a route with no summary
  // anywhere it is linked from. Merely asserting the tag exists is vacuous,
  // because the root layout supplies a default for every route: that is
  // exactly how /digital-twin shipped with no metadata of its own and still
  // looked correct. The assertion is therefore that the description DIFFERS
  // from the layout default.
  const LAYOUT_DEFAULT_DESCRIPTION =
    "Jury-facing demonstration of the CORE_PLUS_CONTEXT physiological sensing architecture and its fault-aware evidence layer.";
  const descriptionMatch = html.match(/<meta name="description" content="([^"]*)"/);
  check(`${route.path}: renders a meta description`, Boolean(descriptionMatch), "no meta description");
  if (descriptionMatch) {
    check(
      `${route.path}: the description is route-specific, not the layout default`,
      descriptionMatch[1] !== LAYOUT_DEFAULT_DESCRIPTION,
      "inherited the layout default description",
    );
  }

  // Exactly one h1 per route: the §9.1 page title, and the document outline.
  const h1Count = (html.match(/<h1\b/g) ?? []).length;
  check(`${route.path}: renders exactly one h1 (found ${h1Count})`, h1Count === 1);

  for (const phrase of route.expect) {
    checkIncludes(`${route.path}: renders "${phrase}"`, text, phrase);
  }

  for (const phrase of FORBIDDEN_VISIBLE) {
    checkExcludes(`${route.path}: §7 — does not claim "${phrase}"`, text, phrase);
  }

  // The retired palettes and the sub-12px classes must be absent from the
  // DELIVERED markup, not merely from the source — this catches a stale build
  // or a dynamically composed class the source scan cannot see.
  check(
    `${route.path}: delivers no retired palette class`,
    !/class="[^"]*\b(?:bg|text|border)-(?:slate|space|cyan|amber|emerald|rose)-\d{2,3}\b/.test(html),
    "a retired palette class reached the browser",
  );
  check(
    `${route.path}: delivers no sub-12px text class`,
    !/class="[^"]*text-\[(?:[0-9]|10|11)(?:\.\d+)?px\]/.test(html),
    "a sub-12px text class reached the browser",
  );
}

// §20 — the static routes must not even reference the live-feed socket URL in
// their delivered payload, which is the server-side half of the runtime-tier
// guarantee the pure classifier asserts.
for (const path of ["/settings", "/system-brief", "/digital-twin", "/research/experimental"]) {
  const html = await (await fetch(`${BASE}${path}`)).text();
  check(
    `${path}: §20 static route delivers no live-feed socket URL`,
    !html.includes("/ws/live-feed"),
    "found /ws/live-feed in the delivered payload",
  );
}

// /research must redirect to the experimental route and preserve its query.
const redirected = await fetch(`${BASE}/research?focus=bioz`, { redirect: "follow" });
check(
  "/research: redirects to /research/experimental preserving the query",
  redirected.url.includes("/research/experimental") && redirected.url.includes("focus=bioz"),
  `landed on ${redirected.url}`,
);

console.log("\nrendered routes:");
for (const r of results) console.log(`  ${r.status}  ${r.path}  (${r.bytes} bytes)`);

const total = passed + failures.length;
console.log(`\nverify-rendered-routes: ${passed}/${total} passed, ${failures.length} failed`);
if (failures.length > 0) {
  console.error("\nFAILURES:");
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exit(1);
}
process.exit(0);
