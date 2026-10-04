# Genuine 200 percent page zoom

## Method

Installed Google Chrome 153.0.8010.12 was driven through the browser-supported `chrome.tabs.setZoom` API. Playwright observed the page and window metrics. Native macOS window capture persisted the exact dedicated Chrome window, producing 2880×1618 Retina PNGs without unrelated desktop content.

No CSS transform, viewport resize, screenshot scaling, device emulation, device-scale override, operating-system display scaling, pinch emulation, `Emulation.setPageScaleFactor`, or CDP device-metrics override was used.

## Measurements

The values were identical on `/mission-overview`, `/live-monitoring`, `/digital-twin`, and `/mission-timeline`:

| Signal | 100% | 200% |
|---|---:|---:|
| Browser API zoom value | 1 | 2 |
| Outer window | 1440×809 | 1440×809 |
| CSS inner viewport | 1440×722 | 720×361 |
| `visualViewport` | 1440×722 at scale 1 | 720×361 at scale 1 |
| Device pixel ratio | 2 | 4 |
| Horizontal overflow | 0 px | 0 px |
| `min-width: 768px` | true | false |
| `min-width: 1280px` | true | false |
| Native PNG | 2880×1618 | 2880×1618 |

The unchanged outer window plus halved CSS capacity, doubled DPR, API state 2, breakpoint transition, and native PNG establish genuine page zoom with multiple independent signals. At 200%, each route reflowed to accessible navigation with no primary horizontal scrolling; controls and labels remained available. Reset returned the API to 1 and restored baseline measurements. Result: 66/66 checks passed.
