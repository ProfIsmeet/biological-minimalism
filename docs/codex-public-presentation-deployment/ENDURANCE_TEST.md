# Endurance test

Status: **LOCAL PASS; PRODUCTION PENDING**

Harness: `backend/scripts/verify_public_endurance.py`. It validates health/state, S14 identity, public read-only status, 403 mutation rejection, strictly advancing timestamps, AI HR availability, and concurrent WebSocket delivery.

Local result: PASS on 2026-10-06. Three concurrent WebSocket clients ran for 600 seconds. Each client received 1,143 frames, advanced from timestamp `1791228845.493547` to `1791229445.665357`, and observed a real Model B prediction. No client disconnected or stalled.

The identical 600-second/3-client command remains required against production.
