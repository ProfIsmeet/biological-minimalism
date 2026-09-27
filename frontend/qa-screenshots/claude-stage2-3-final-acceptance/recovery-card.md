# Recovery Card (non-technical)

Quick reference for a presenter, not an engineer, during a live jury demo.

## "It says DISCONNECTED"

This is expected and safe. The app is telling you the backend connection
dropped -- it never shows fake/stale data instead. Refresh the page once. If
it still says DISCONNECTED after a refresh, say: "The demo server needs a
moment to restart," and pause the demo. Do not keep clicking things.

## "It says the canonical/recorded demo can't load"

This is expected in this environment -- the recorded dataset is not
configured here. It is not a bug. Switch back to talking about the
synthetic demo (see `presenter-script.md` step 3 -- this is actually a good
moment to show the audience the honest failure message on purpose).

## "The 3D figure disappeared and shows a text panel instead"

This is the WebGL fallback -- expected on some browsers/graphics drivers.
There is a "Try 3D view again" button in that panel. One click normally
restores it. If it doesn't come back after one try, just keep talking over
the text panel -- it still shows the correct architecture-boundary
information, nothing is lost.

## "The 3D figure stopped rotating"

Check Settings -> Reduce motion. If it's on, that's expected -- the figure
is still fully interactive (Rotate left/right buttons), it just won't
auto-spin. Turn the toggle off if you want auto-rotation back.

## "Nothing is loading at all"

1. Refresh the page once.
2. If still broken, close and reopen the browser tab.
3. If still broken, this is a genuine infrastructure issue -- stop the demo
   and say so plainly rather than trying increasingly desperate fixes live.

## General rule

If the app is telling you something is unavailable, disconnected, or not
configured, **that is the app working correctly**, not failing. It is
designed to never show fake success. Explaining that to the audience is a
legitimate and honest part of the demo.
