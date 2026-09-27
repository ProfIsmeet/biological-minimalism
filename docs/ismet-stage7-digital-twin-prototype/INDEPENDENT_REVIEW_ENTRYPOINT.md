# Stage 7 Digital Twin Prototype — Independent Review Entrypoint

## How to check out and run this prototype in isolation

```bash
git clone https://github.com/ProfIsmeet/biological-minimalism.git
cd biological-minimalism
git fetch origin ismet/stage7-digital-twin-prototype
git checkout ismet/stage7-digital-twin-prototype
cd frontend
npm ci
npm run dev
# open http://localhost:3000/research/stage7-digital-twin-prototype
```

The route requires no backend, no environment variables, and no dataset. It is fully self-contained.

## What to read first

1. `docs/ismet-stage7-digital-twin-prototype/MASTER_HANDOFF_REPORT.md` — the full technical handoff (start here).
2. `docs/ismet-stage7-digital-twin-prototype/CURRENT_SYSTEM_AUDIT.md` — what was found wrong with the existing system, with live-browser evidence.
3. `docs/ismet-stage7-digital-twin-prototype/PROTOTYPE_DESIGN_SPEC.md` — what was built and why.
4. `frontend/qa-screenshots/ismet-stage7-digital-twin-prototype/AUDIT.md` + `EVIDENCE_INDEX.json` — the visual evidence, with SHA-256 hashes for integrity verification.

## How to verify isolation independently

```bash
# Confirm zero existing product files were modified:
git diff --stat 7afe57114ad6f7537b73f17683f7ecd733606730..HEAD -- \
  frontend/src/components frontend/src/app/digital-twin frontend/src/app/mission-overview \
  frontend/package.json frontend/package-lock.json frontend/src/app/globals.css frontend/tailwind.config.ts
# (should print nothing — no output means no changes to any of those paths)

# Confirm the new route is not linked from navigation:
grep -r "stage7-digital-twin-prototype" frontend/src/components/layout/
# (should print nothing)

# Run the prototype's own isolation verifier:
cd frontend && node scripts/verify-stage7-digital-twin-prototype.mjs
```

## How to verify no regression to the existing product

```bash
cd frontend
npm run verify:monitoring   # expect 1021/1021 + 5/5 structural checks, unchanged from this branch's own base
npm run lint                # expect clean
npx tsc --noEmit            # expect clean
npm run build                # expect 15/15 static pages
```

## Scope of independent review requested

This is a prototype, not a product-integration candidate. Independent review should assess:
- Does the visual treatment genuinely improve on the audited weaknesses (silhouette readability, framing, decoration, auto-rotation)?
- Is the sensor/module topology accurately reused from the authoritative source (`lib/architecture.ts`), not reinvented?
- Are the scientific-boundary disclosures (architecture-only/untrained/unvalidated) sufficiently visible and honest?
- Is the isolation genuinely complete (no product file touched, no navigation link, no backend/store coupling)?

Independent review should NOT treat this as ready for product merge — it explicitly is not (see `MASTER_HANDOFF_REPORT.md` §1 verdict).
