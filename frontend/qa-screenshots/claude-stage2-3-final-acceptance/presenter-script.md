# Presenter Script — Biological Minimalism Jury Demo

Scope: synthetic-demo path only, since no real PPG-DaLiA dataset/checkpoint
is configured in this environment (see `JURY_DEMO_RECOMMENDATION.md`).

## 1. Open

Navigate to **Mission Overview**. Say: "This is a mission systems
demonstrator running in synthetic demo mode -- the values you see are
generated, not live astronaut telemetry, and the interface tells you that
plainly at every step."

Point at the "Live operational sensing status" panel: session, source,
connection, and simulated-fault fields, plus the session-time clock ticking
live.

## 2. Show the honest source-aware monitor

Navigate to **Live Signals**. Say: "Every modality is either confirmed
present or explicitly marked as not present in the current source -- nothing
is filled in with a fake zero or a fake 'nominal' just because it's not
available."

## 3. Show the fail-closed canonical demo path

Open the **Demo controls** drawer (bottom-right / nav icon depending on
viewport). Click **Load Canonical Jury Demo**. Say: "This is meant to
switch to a real recorded human dataset -- subject S14. Watch what it does
when that dataset isn't configured on this backend." Point at the resulting
message: "Canonical jury demo not loaded -- Recorded PPG-DaLiA replay
dataset is not configured on this backend." Say: "It never pretends to
succeed."

## 4. Show the Digital Twin boundary and reduced-motion behavior

Navigate to **Digital Twin Reference**. Point at the
"ARCHITECTURE ONLY - UNTRAINED - UNVALIDATED" badge. Say: "This figure is a
conceptual boundary, not a working personalized model."

If asked about accessibility: open **Settings**, toggle "Reduce motion", and
show the figure freeze at a stable angle immediately, with the manual
rotate controls still fully usable -- say: "Reduced motion stops decorative
animation but never blocks the operator from doing anything."

## 5. Close

Navigate back to **Mission Overview**. Say: "Everything shown today is
either live synthetic telemetry or an explicit, labeled architecture
reference -- there is no live astronaut data and no claim of clinical
validation anywhere in this build."

## If something breaks live

See `recovery-card.md` in this directory.
