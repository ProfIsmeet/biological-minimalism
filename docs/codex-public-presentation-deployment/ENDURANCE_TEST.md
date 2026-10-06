# Endurance test

Status: **PASS — LOCAL AND PRODUCTION**

Harness: `backend/scripts/verify_public_endurance.py`. It validates health/state, S14 identity, public read-only status, 403 mutation rejection, strictly advancing timestamps, AI HR availability, and concurrent WebSocket delivery.

Local result: PASS on 2026-10-06. Three concurrent WebSocket clients ran for 600 seconds. Each client received 1,143 frames, advanced from timestamp `1791228845.493547` to `1791229445.665357`, and observed a real Model B prediction. No client disconnected or stalled.

Production browser endurance subsequently passed for 621 uninterrupted seconds with monotonically advancing replay state, connected S14 identity, read-only status, and Model B output. The command-line WSS runner was blocked by its local proxy, so the production WSS verdict is based on the real browser client. The earlier production-pending statement was accurate before that run.
