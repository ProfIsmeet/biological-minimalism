# Genuine 200 Percent Zoom Acceptance

## Method and proof

The test used a visible native Safari 26.5.2 window on macOS 26.5.2 (25F84), not device emulation, CSS zoom, injected styles, JavaScript scaling, screenshot enlargement, or a resized viewport. Safari's native View > Zoom In control was used through the native UI until its 200% step was reached. The fixed physical capture was 2880×1800 and the outer browser window remained 1440×804 points.

Independent page metrics supplied the second proof signal:

| State | innerWidth × innerHeight | scrollWidth × scrollHeight | DPR | Canvas |
| --- | --- | --- | --- | --- |
| 100% reference | 1440×714 | 1440×1402 | 2 | 1 |
| 200% acceptance | 720×357 | 720×2255 | 4 | 1 |

The exact halving of CSS viewport dimensions and doubling of DPR, with fixed physical and outer-window dimensions, is consistent with native 200% zoom and inconsistent with merely shrinking the browser window. Browser chrome is retained in every canonical screenshot. The user elected not to require an additional browser percentage-popover recapture; exactness is therefore established by the native control sequence plus recorded viewport/DPR measurements.

## Acceptance matrix

| Check | Result |
| --- | --- |
| Direct `/digital-twin` navigation and hard refresh | PASS |
| Product sidebar navigation, back, and forward | PASS |
| Default, front, back, frontal, chest, wrist views | PASS |
| Keyboard 1–4, Home/Escape, Space | PASS |
| Logical traversal and visible focus | PASS |
| Semantic non-canvas summary | PASS |
| Vertical page scrolling | PASS |
| Horizontal overflow / 2D scrolling | PASS — none; `scrollWidth == innerWidth` |
| Scientific-boundary content | PASS — readily reachable |
| Route exit and return | PASS |
| Application reduced-motion path | PASS; OS setting unchanged |
| WebGL-supported rendering | PASS |
| Canvas lifecycle | PASS — 1 mounted, 0 after exit, 1 after return |
| Static fallback | ACCEPTED from unchanged canonical evidence and automated guard |
| Console | No new product error; extension injection caused a hydration diagnostic, Three.js emitted a Clock deprecation warning, and expected backend-unavailable messages appeared on unrelated Settings when port 8000 was not running |

The responsive result became taller, as permitted, but did not become a clipped mobile/desktop hybrid. Navigation and controls remained reachable; text did not overlap; the model remained legible; and the shoulder/pelvis corrections remained coherent.

## Restoration

Safari View > Actual Size restored 100%. The restored metrics returned to 1440×714 at DPR 2. The task-created tab was closed without touching pre-existing tabs, and the port-3420 server was stopped.
