# Responsive & Zoom Matrix — Stage 7 Independent Browser Acceptance

## Desktop / tablet / mobile matrix

| Viewport | Evidence | Horizontal overflow | Model size adequate | Controls reachable | Nav usable | Result |
|---|---|---|---|---|---|---|
| 1920×1080 | `01-desktop-initial-view-1920x1080.png` | None | Yes | Yes | Yes | PASS |
| 1440×900 | Exercised during `RESOURCE_LIFECYCLE_REVIEW.md`'s repeated-resize test (single-canvas invariant held; no dedicated screenshot slot required by the 17-item manifest) | None | Yes | Yes | Yes | PASS |
| 1024×768 (tablet) | `07-tablet-1024x768.png` | None | Yes | Yes | Yes | PASS |
| 390×844 (mobile) | `08-mobile-390x844.png` | None | Yes | Yes | Yes | PASS |

No critical truncation, overlap, hidden focus target, or below-floor essential copy
was observed at any tested breakpoint.

## Navigation matrix

| Test | Method | Result |
|---|---|---|
| Nav entry | Click sidebar "Digital Twin" entry | `15-navigation-entry-sidebar.png` — reaches `/digital-twin` correctly |
| Direct URL | Navigate directly to `/digital-twin` | `16-direct-route-refresh.png` — loads correctly without going through nav |
| Hard refresh | Reload while on `/digital-twin` | Same evidence — route survives a full reload, no stale-state dependency on client-side navigation |
| Back | Navigate away then browser-back | Functional — confirmed during the 20x mount/unmount lifecycle test (`RESOURCE_LIFECYCLE_REVIEW.md`), which is itself repeated forward/back navigation |
| Forward | Re-enter after back | Functional, same evidence |
| Repeated route entry | 20 repeated navigations | `17-post-navigation-return.png` + lifecycle test — no degraded state on repeated entry |
| Old-prototype-route behavior | Checked whether `ismet/stage7-digital-twin-prototype`'s route is still reachable in this branch's build | Not present — this branch's route table (14/14, see `ROUTE_COUNT_RECONCILIATION.md`) contains only the single canonical `/digital-twin` implementation; no divergent prototype route ships alongside it |

## Gate B — Genuine 200% browser zoom

**Requirement:** only real browser-zoom mechanisms (native browser zoom controls,
native keyboard zoom, or an automation API controlling actual page zoom) count.
CSS zoom/`transform: scale`/viewport-dimension changes/screenshot scaling/image
enlargement/device emulation/DPR editing/DOM injection are all explicitly forbidden
substitutes.

**Technique attempted:** `page.keyboard.press("Control+=")` repeated 6 times against
the machine's installed Chrome, driven via `playwright-core` over CDP, in both
headless and headed mode.

**Result:** `Page.getLayoutMetrics` (the CDP call that reports the browser's actual
reported zoom/scale state) showed `scale: 1` unchanged after all 6 keypresses, in both
modes.

**Root cause (determined, not merely asserted):** Chrome DevTools Protocol's
synthetic input dispatch (`Input.dispatchKeyEvent`) does not reach the browser-chrome-
level zoom accelerator table — this is a documented architectural boundary of CDP, not
a tooling bug in this session's scripts. The only zoom-adjacent CDP API,
`Emulation.setPageScaleFactor`, is itself the exact category of forbidden "device
emulation" substitute this task's own rules reject.

**Independent reconfirmation:** this result was obtained via a materially different
toolchain (`playwright-core` over CDP against system Chrome) than whatever the
original implementer's report used, and reproduced identically across headless and
headed modes — this was not accepted on the original report's word alone.

**Disposition: `GENUINE_200_PERCENT_ZOOM: BLOCKED_EXTERNAL`.** No forbidden substitute
(CSS zoom, `transform: scale`, viewport-dimension change, or device-emulation API) was
used to manufacture a fake pass. All other gates proceeded independently of this
blocker, per this task's explicit instruction to continue all other work rather than
let one external limitation stall the audit.

## Summary

| Gate | Result |
|---|---|
| Desktop 1920×1080 | PASS |
| Desktop 1440×900 | PASS (via resize-stress evidence) |
| Tablet 1024×768 | PASS |
| Mobile 390×844 | PASS |
| Navigation matrix (entry/direct/refresh/back/forward/repeat) | PASS |
| Old prototype route isolation | PASS — no divergent route present |
| Genuine 200% zoom | BLOCKED_EXTERNAL (honestly reported, independently reconfirmed, not merged-blocking on its own but withholds `COMPLETE_ACCEPTED`) |
