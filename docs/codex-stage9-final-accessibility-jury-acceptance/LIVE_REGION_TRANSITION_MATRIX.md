# Live-region transition matrix

| Transition | UI state verified | Exact announcement |
|---|---|---|
| canonical load / awaiting first frame | PASS | PARTIAL |
| replay start | PASS | PARTIAL |
| replay pause | PASS | PARTIAL |
| source change synthetic → S14 | PASS | PARTIAL |
| PPG fault onset | PASS | PARTIAL |
| HR output withheld | PASS | PARTIAL |
| rebuilding/warm-up | PASS | PARTIAL |
| recovered fresh HR | PASS | PARTIAL |
| connection loss/recovery | NOT RUN | PARTIAL |
| genuine source error | NOT RUN | PARTIAL |

Visible states were mutually distinguishable and stale HR was not presented as current. The live-region structural verifier passed. Exact cadence/wording remains unverified.
