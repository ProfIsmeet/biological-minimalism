# Public-mode security review

- All non-GET/HEAD/OPTIONS HTTP requests return 403 before route parsing.
- Unexpected HTTP Origin returns 403. Unexpected or missing WebSocket Origin is rejected before acceptance: the ASGI close policy is 1008 and a network client observes an HTTP 403 handshake rejection.
- CORS remains an explicit non-empty, non-wildcard list.
- Dataset/checkpoint paths and hashes are server settings only.
- No admin credential exists in the browser bundle.
- Dataset/checkpoint files have no serving route.
- Asset bootstrap requires HTTPS, bounded size, atomic write, and exact SHA before startup.
- Private asset bootstrap uses a server-only bearer credential, requests binary content explicitly, strips authorization on cross-host redirects, and never returns asset URLs or bytes to clients.
- Public HTTP requests have size and 30-second limits.
- WebSocket fan-out is bounded to 100 clients and 2-second send timeout.
- Explanation work has a bounded non-blocking concurrency slot.
- Startup/log boundaries use generic errors instead of private paths.

Local wrong-origin, mutation, loop, hash, and unchanged-local-mode tests pass. A live network probe also observed 403 for both unexpected-origin and missing-origin WebSocket handshakes.
