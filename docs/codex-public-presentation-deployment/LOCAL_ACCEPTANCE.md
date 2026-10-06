# Local acceptance

- Public backend: real PPG-DaLiA S14, autoplay 5x, four expected channels, no fault, fresh Model B HR.
- Read-only: pause POST rejected 403; deterministic mutation suite passes.
- Multi-client probe: 2 clients, 20 fresh frames each over 10 seconds, prediction observed by both.
- Endurance: 3 concurrent clients for 600 seconds, 1,143 frames per client, strictly advancing timestamps, predictions observed by every client, no disconnects or stalls.
- Browser: all eight routes passed at 1440×900, 1024×768, and 390×844.
- Every tested route: correct title, no horizontal overflow, public read-only indicator, no private path, no mutation controls.
- Operational routes converged to `RECORDED REPLAY / CONNECTED`; fresh HR and trend appeared after warmup.
- Relevant console errors: zero. Existing Three.js Clock deprecation warning remains non-blocking and predates deployment work.
- Rendered route verifier: 146/146.

The full client/frame/timestamp result is recorded in `ENDURANCE_TEST.md`.
