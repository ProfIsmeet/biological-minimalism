# VoiceOver route matrix

Actual VoiceOver was on during the public review. Every principal route exposed one H1, the shared skip link/navigation, a public read-only label, and route-specific semantics in the native accessibility tree. Exact announcements were not captured, so every route's speech verdict is `PARTIAL`.

| Route | One H1 / landmarks | Nonvisual content | Exact VO speech |
|---|---|---|---|
| `/mission-overview` | PASS | PASS | PARTIAL |
| `/live-monitoring` | PASS | PASS | PARTIAL |
| `/system-brief` | PASS | PASS | PARTIAL |
| `/research/experimental` | PASS | PASS; exact tables | PARTIAL |
| `/digital-twin` | PASS | PASS; semantic architecture summary | PARTIAL |
| `/ai-insights` | PASS | PASS | PARTIAL |
| `/mission-timeline` | PASS | PASS; table | PARTIAL |
| `/settings` | PASS | PASS; named switch/button | PARTIAL |

Additional user-facing `/` and `/research` redirects are covered by rendered-route verification; their exact VoiceOver redirect announcements were not captured.
