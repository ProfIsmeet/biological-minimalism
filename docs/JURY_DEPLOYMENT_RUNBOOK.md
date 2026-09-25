# Jury Deployment Runbook (clean machine)

Operational runbook for standing up the Biological Minimalism dashboard demo on
a clean machine for a jury demonstration. This is an operator document, not
promotional copy. It distinguishes steps that were **verified** in preparing
this runbook from steps that are **specified but not executed here**.

> **Verification status of this runbook.** The configuration facts below
> (lockfile install, `npm ci`, CORS defaults/override parsing, WS-URL
> derivation, public-copy cleanup) were verified by unit/static tests and
> executed assertions in the source tree. The end-to-end **clean-machine
> bring-up and the Docker/Compose path were NOT executed while writing this
> runbook** (Docker was unavailable in the authoring environment). Treat the
> Docker and live-connectivity sections as specified-but-unexecuted until an
> operator runs them on the target machine and confirms with
> `scripts/verify_jury_environment.py`.

## 1. Supported operating assumptions

- A single presenter/operator on one machine (macOS or Linux). No multi-user,
  authentication, or role model is provided or implied.
- Local-only jury topology: the browser, frontend, and backend run on the same
  machine (or same LAN with reachable hostnames). No reverse proxy is assumed.
- Offline after dependencies are installed: no internet is needed at demo time.

## 2. Required tool versions

Established by the repository:

- **Node 20+** (frontend container base is `node:20-slim`; README says Node 20+).
- **npm 10+** (ships with Node 20; used via `npm ci`).
- **Python 3.11+** (backend container base is `python:3.11-slim`; README says 3.11+).
- **Docker Engine + Compose v2** (`docker compose`, not `docker-compose`) for the
  container path (`docker-compose.yml`).

Confirm with `scripts/verify_jury_environment.py` (reports versions; a missing
tool is a WARN, not a hard failure, because the manual and container paths need
different subsets).

## 3. Clean clone preparation

```bash
git clone <repo-url> biological-minimalism
cd biological-minimalism
python scripts/verify_jury_environment.py --root .   # read-only preflight
```

Do not run `npm install` in `frontend/` — use `npm ci` (see §10) so the install
is reproducible from `frontend/package-lock.json`.

## 4. Dataset availability and mounts

- No dataset is bundled. The **synthetic** demo needs no dataset.
- Recorded **PPG-DaLiA replay** requires the official per-subject distribution;
  see [`docs/DATASET_REPLAY.md`](DATASET_REPLAY.md) and
  `datasets/ppg-dalia/README.md`.
- Container path: `docker-compose.yml` mounts `./datasets/ppg-dalia` read-only
  at `/data/ppg-dalia` and sets `BIOMIN_PPG_DALIA_PATH=/data/ppg-dalia`. If the
  host directory is empty, replay is simply unavailable (the UI says so; see §14).

## 5. Model checkpoint and checksum enforcement

- Replay HR inference uses the validated PPG+IMU checkpoint at
  `ml/checkpoints/model_b_ppg_plus_imu_ppg_dalia.pt`
  (`BIOMIN_PPG_DALIA_HR_CHECKPOINT_PATH`). Checkpoints are **not** committed
  (see `.gitignore`); the SHA-256 is enforced by the replay bridge.
- If the checkpoint is absent or its hash does not match, replay HR inference is
  refused rather than silently substituted (see §15). The synthetic demo does
  not need any checkpoint.

## 6. Backend environment setup

Backend variables are all prefixed `BIOMIN_` (see `backend/.env.example`). Copy
it to `backend/.env` only if you need to override defaults. These are
**operator-side** variables and must never be surfaced in the browser UI.

Relevant keys: `BIOMIN_ALLOWED_ORIGINS` (see §8), `BIOMIN_PPG_DALIA_PATH`,
`BIOMIN_PPG_DALIA_HR_CHECKPOINT_PATH`.

## 7. Frontend build-time API / WebSocket configuration

`NEXT_PUBLIC_*` values are **inlined into the client bundle at build time** and
are **public** (visible in the browser) — never put a secret in them. See
`frontend/.env.local.example`.

- `NEXT_PUBLIC_API_BASE_URL` — REST origin the browser calls (default
  `http://localhost:8000`).
- `NEXT_PUBLIC_WS_URL` — live-feed WebSocket URL. If unset/empty it is derived
  from the API URL: `http`→`ws`, `https`→`wss`, with `/ws/live-feed` appended
  (a trailing slash on the API URL is trimmed first).
- Container builds must pass these as **build args** (see `docker-compose.yml`
  `frontend.build.args`), not merely runtime env, because Next inlines them at
  build time.

## 8. CORS origin configuration

- Backend allows only **exact browser origins** via `BIOMIN_ALLOWED_ORIGINS`, a
  JSON array, e.g. `BIOMIN_ALLOWED_ORIGINS='["https://demo.example.org"]'`.
- Defaults (unset) are `http://localhost:3000` and `http://127.0.0.1:3000`.
- Wildcard `*` is rejected; a non-JSON value fails fast at startup. This is the
  allowed **browser origin** list — distinct from the frontend URL and from the
  backend bind address. `allow_credentials=True`, so origins must be exact.
- **WebSocket note (honest):** Starlette's `CORSMiddleware` governs HTTP CORS; it
  does **not** enforce an origin check on the WebSocket handshake. Do not assume
  the `/ws/live-feed` endpoint is origin-restricted by CORS. For the local jury
  topology this is acceptable (loopback only); for any exposed deployment, put
  the app behind a trusted network boundary.

## 9. Docker Compose startup (container path)

```bash
docker compose config      # validate compose (read-only; run this first)
docker compose up --build  # build images and start backend + frontend
```

- Frontend: http://localhost:3000 · Backend docs: http://localhost:8000/docs
- Ports `3000` and `8000` are the standard local demo ports.
- *Not executed while authoring this runbook — validate on the target machine.*

## 10. Manual startup (no containers)

Backend (Python 3.11+):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (Node 20+), second terminal:

```bash
cd frontend
npm ci            # reproducible install from package-lock.json (NOT `npm install`)
npm run dev       # or: npm run build && npm run start
```

## 11. Health checks

- Backend liveness: `curl -fsS http://localhost:8000/health` → JSON `{"status":"ok", ...}`.
- Compose declares a backend healthcheck against `/health`; the frontend waits
  for `service_healthy`.

## 12. Frontend / backend / WS connectivity checks

- Frontend loads at http://localhost:3000.
- REST: browser dev-tools Network tab shows calls to `NEXT_PUBLIC_API_BASE_URL`
  returning 200 with no CORS error.
- WebSocket: a `ws(s)://…/ws/live-feed` connection stays open and streams frames.
- A CORS misconfiguration shows up as blocked REST calls with a console CORS
  error (see §16).

## 13. Expected nominal route behavior

- Mission Overview shows source, state, body region, and HR inference for the
  active source (synthetic by default), and supports the
  nominal → fault → rebuilding → recovered → disconnected story.
- Static routes (System Brief, Experimental, Digital Twin) render without needing
  the live WebSocket.

## 14. Expected behavior when the dataset is absent

- Replay is unavailable; the data-source panel states that recorded replay is
  not available on this deployment (it does **not** print backend setup steps).
- The synthetic demo is unaffected and remains fully functional.

## 15. Expected behavior when the checkpoint is absent or invalid

- Replay HR inference is refused (missing-input / model-unavailable states), not
  faked. Missing data never becomes zero, nominal, or "healthy".
- The synthetic demo needs no checkpoint and is unaffected.

## 16. Expected behavior under CORS failure

- Symptom: REST calls blocked, browser console shows a CORS error; the UI cannot
  load live REST data.
- Cause/fix: `BIOMIN_ALLOWED_ORIGINS` does not include the exact browser origin
  (scheme+host+port) the page is served from. Set it to the exact origin and
  restart the backend. Never "fix" this with a wildcard.

## 17. Expected behavior under WebSocket failure

- Symptom: no live frames; the live-feed connection fails or drops.
- Cause/fix: `NEXT_PUBLIC_WS_URL` (or its derivation from the API URL) does not
  point at a reachable `/ws/live-feed`, or the backend is down. Static routes
  keep working; the demo degrades rather than crashing.

## 18. Recovery steps (no scientific-data mutation)

- Restart the affected process (backend `uvicorn` or `docker compose restart
  backend`; frontend dev server).
- Re-run `scripts/verify_jury_environment.py --root .`.
- Do **not** clear replay, apply/clear faults, change source/subject, or edit
  scientific constants as a "fix" — recovery must not mutate scientific state.

## 19. Browser and projector preflight checklist

- Use a current Chromium/Firefox/Safari.
- Confirm 1080p (or target projector) rendering; check contrast and that the
  smallest labels remain readable at the projection distance.
- Verify 200% browser zoom still lays out correctly (accessibility evidence).
- Load Mission Overview and confirm the mobile/first-view state if presenting on
  a narrow display.

## 20. Shutdown procedure

- Manual: Ctrl-C each process; `deactivate` the venv.
- Container: `docker compose down` (add `-v` only if you intend to drop volumes;
  datasets are host-mounted read-only and unaffected).

## 21. Logs useful for diagnosis

- Backend: `uvicorn` stdout, or `docker compose logs backend`.
- Frontend: dev-server stdout / browser console; `docker compose logs frontend`.
- Health JSON at `/health` reports the active source type and inference engine.

## 22. Known local-only assumptions

- Loopback/LAN topology, single operator, no auth, no reverse proxy.
- `NEXT_PUBLIC_*` are public; the WS handshake is not CORS-restricted (§8).
- The container path uses fixed container names (`biomin-backend`,
  `biomin-frontend`) and ports 3000/8000 — do not run it alongside another
  instance using the same names/ports.

## 23. Explicit non-claims

- **Not flight-qualified. Not clinically validated.** No astronaut/microgravity
  validation. The Digital Twin is architecture-only, untrained, and unvalidated.
- Simulated faults are demo mechanisms, not scientific results. Recorded replay
  (PPG-DaLiA, single participant) is terrestrial research data, not live
  astronaut monitoring.

## 24. No secrets in browser-visible variables

`NEXT_PUBLIC_*` variables ship in the client bundle and are visible to anyone
loading the page. They must contain only public configuration (API/WS URLs).
Secrets, if any, belong only in backend/operator environment, never in
`NEXT_PUBLIC_*`.

## 25. Operator setup vs. public UI behavior

- Backend environment variables (`BIOMIN_*`), file-system paths, and shell
  commands are **operator** concerns and live here and in `docs/DATASET_REPLAY.md`.
- The public UI never instructs an end user to set backend environment variables
  or edit backend configuration; when replay is unavailable it simply says so and
  points the user to the demo administrator. Presenter Preflight is a read-only
  diagnostic surface — it reports current readiness, it does not enable replay,
  change backend configuration, or repair a missing dataset itself.

## 26. Canonical jury demo procedure

Once the environment is verified (§3, §12) and the dataset/checkpoint are
confirmed available (§4, §5, Presenter Preflight), the presenter can bring the
session to one known, reproducible starting state in a single explicit step:

1. Open the demonstration controls drawer (the control near the mission status
   bar / mobile "More" menu).
2. Check Presenter Preflight first — it is read-only diagnostics, not a fix
   action. If any of "Recorded replay dataset", "Replay subject list", or
   "S14" reads anything other than Ready, resolve that first (see §4/§14);
   the canonical demo action below will refuse to run and say exactly which
   prerequisite is missing rather than silently falling back to synthetic.
3. Click **"Load canonical demo"**. This is a separate, explicit action from
   "Reset" (which preserves whatever source/subject is already active) — it
   specifically switches to recorded PPG-DaLiA replay, subject S14, paused at
   the start, at 1× speed, with no active simulated fault.
4. The status line beneath the button reports the outcome honestly: full
   success names the subject and configuration; a blocked prerequisite names
   exactly which one; a partial failure names exactly which step(s) did not
   complete (other steps still applied); an unexpected failure says so
   without claiming completion. Never trust an absence of a message as
   success — wait for the status line.
5. The action is safe to repeat: running it again reloads the same subject
   from scratch and lands in the same canonical state. If it is invoked twice
   in quick succession (or the page navigates away mid-load), only the most
   recent invocation's result is ever applied to visible state — an
   in-flight, superseded attempt is dropped rather than allowed to overwrite
   what came after it.

This is real recorded human research data (PPG-DaLiA, participant S14) — a
single-participant robustness demonstration, never presented as astronaut or
live-sensor data. See §23 for the full explicit non-claims list.

## 27. Recovery when the canonical demo load fails

- **Blocked on a prerequisite** (dataset not configured / subject list
  unavailable / S14 not present): this is not a frontend bug — follow the
  matching guidance in §4 (dataset availability), §5 (checkpoint), or restart
  the backend and re-check Presenter Preflight before retrying.
- **Partial failure** (one or more named steps did not complete): click
  "Load canonical demo" again. Because the action always starts from a fresh
  subject load, a retry does not compound the prior partial state — it
  re-attempts the full canonical sequence from scratch.
- **Unexpected failure** with no named step: check §21 (backend/frontend
  logs) for the underlying error before retrying: a transient network issue
  is safe to just retry, but a repeated identical failure likely indicates a
  backend-side problem (e.g. a corrupted dataset file) that requires operator
  attention, not repeated retries from the UI.
