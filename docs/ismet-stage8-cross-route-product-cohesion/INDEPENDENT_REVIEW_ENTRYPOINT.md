# Independent review entrypoint

## Start here

This branch has one gap that only a reviewer with a browser can close:
**no rendered verification happened at all.** Everything structural is guarded
and passing; nothing about layout, paint, or interaction was observed. If you
have ten minutes, spend them on the browser matrix.

## Bring the stack up

```bash
git fetch origin
git checkout ismet/stage8-cross-route-product-cohesion

# backend
cd backend
./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8137

# frontend, in a second shell
cd frontend
npm ci
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8137 npx next dev -p 3147
```

Ports 8137 and 3147 are the ones this work used; nothing else on the machine
was touched.

## Run the gates

```bash
cd frontend
npx tsc --noEmit          # expect clean
npm run lint              # expect clean
npm run build             # expect 12 routes prerendering
npm run verify:monitoring # expect 1327/1327 and 7 passing sub-verifiers
npm run verify:rendered -- http://127.0.0.1:3147   # expect 146/146
```

Run `verify:rendered` **before** `npm run build`, or restart the dev server
after building — `build` overwrites `.next` under a running `next dev` and
produces three spurious failures on `/mission-overview`.

## The three things most likely to be wrong

This stage raised ~40 text sizes to the 12px floor and ~26 controls to a 44px
minimum. §9.1 forbids shrinking text back down to fix overflow, so if any of
these broke, the fix is to give the content room — not to revert the size.

1. **`/live-monitoring` right rail at 1024x768 and 1280x800.** Every button,
   select and number input in `ReplaySessionControl` and
   `SimulatedFaultControl` grew from ~28-32px to 44px and from 12px to 14px
   text, inside `flex-wrap` rows, in the narrowest column on the page. This is
   the highest-risk change in the branch.
2. **`SensorConstellation` hub, compact variant.** Two labels at 9px and 10px
   became one at 12px inside the same 56px circle, with the connection state
   moved to the caption below. Check it does not clip, and that the caption now
   reads "Source connected" / "Source not connected".
3. **Avatar anchor labels on `/mission-overview` and `/digital-twin`.**
   `OperationalAvatarOverlay` and `StaticAvatarFallback` labels went from 8-11px
   to 12px, positioned absolutely over the figure. Check for overlap.

## Then confirm the protected work is intact

Visually, at 1440x900:

- `/mission-overview`: five-section narrative in order; four-ring orbit with a
  fixed categorical sweep and the "Not model confidence" centre label; coverage
  radar semantics; enlarged HR trend and signal lanes; fault/rebuilding/recovery
  timeline as a major plot; **no** visible "Last confirmed frame".
- `/digital-twin`: ARCHITECTURE ONLY / UNTRAINED / UNVALIDATED badge present;
  Stage 7 geometry and joints unchanged; camera, focus and keyboard behaviour
  unchanged; WebGL fallback still reachable.
- Anywhere: **no** "% Adapted", no overall adaptation score, no success badge.

The suite asserts all of these structurally. What it cannot tell you is whether
they still *look* right.

## Accessibility spot-checks worth doing

- Tab through `/live-monitoring`. Every control should show the same accent
  focus ring. Confirm it is visible against `surface-3` and against the dark
  `#061A26` WebGL stage — those are the two surfaces most likely to swallow it.
- Open the mobile nav and the demo drawer by keyboard. Focus should trap,
  Escape should close, and focus should return to the opener. Also confirm
  neither container shows a focus ring of its own — the global rule sits in
  `@layer base` specifically so their `outline-none` still wins.
- Tab to the playback-speed buttons. The active one should be distinguishable
  with colour ignored (it carries `aria-pressed` and a heavier weight).

## What to be sceptical of in my own work

Six findings in `FINDING_LEDGER.md` are marked **self-inflicted**: guards I
wrote that passed while real violations remained, or that flagged correct code.
The most instructive is H-6 — my palette guard reported clean while 528
violations survived, because it only checked the two families my first pass had
already fixed. If you want to test whether a guard here is real, the quickest
method is the one that caught that: pick a violation the guard claims to
prevent, introduce it, and confirm the suite fails. Two guards were validated
that way deliberately (the page-title ceiling and the alpha-palette pattern);
the rest were not.

## Rollback

Every commit is independent and additive; none rewrites history.

```bash
# drop the whole stage
git checkout main

# drop one concern, e.g. the focus-ring unification
git revert 4a8a629

# drop the palette completion and control sizing
git revert b6702fe
```

The two commits that would need care are `95310c6` (deletes
`DigitalTwinPanel.tsx`) and `0737f7e` (splits `/digital-twin`): reverting
either also reverts the guards that depend on it, so revert the pair together
or expect a suite failure naming the missing file.
