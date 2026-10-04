# Browser acceptance matrix

Real Chromium (Codex in-app browser) ran against Next production on `127.0.0.1:3148` and FastAPI on `127.0.0.1:8138`, with exact CORS origin `http://127.0.0.1:3148`.

| Route | Desktop | Tablet | Mobile | Result |
|---|---|---|---|---|
| Mission Overview | 1440, 1366, 1280 | 1024, 768 | 390 | PASS after M-01/M-02/M-03 corrections |
| Live Monitoring | 1440, 1366, 1280 | 1024, 768 | 390 | PASS; connected synthetic state and replay-unavailable boundary truthful |
| System Brief | 1440 | 768 | 390 | PASS; wide table intentionally contained in a horizontal scroller |
| Experimental Research | 1440 | 768 | 390 | PASS; desktop tables and mobile card alternatives inspected |
| Digital Twin | 1440 | 768 | 390 | PASS; WebGL settled to canvas, architecture-only boundaries visible |
| AI Insights | 1440 | 768 | 390 | PASS; synthetic values explicitly not model output/measurement |
| Mission Timeline | 1440 | 768 | 390 | PASS; session versus conceptual content separated |
| Settings | 1440 | 768 | 390 | PASS; static explanatory route and preference control usable |

All inspected final pages had one route H1, correct titles, viewport-width document scroll, and no unintended page-level horizontal overflow. Local table scrollers and mobile card substitutions are intentional. Shell links were clicked through for all eight routes. Direct loads and reloads were also exercised.

Full-page Chromium stitching duplicated lazy/WebGL sections in some transient images even though the DOM contained one instance. Those stitched images were rejected as canonical proof; initial-viewport images and DOM geometry were used for adjudication.
