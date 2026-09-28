# WebGL Lifecycle and Performance

## Ownership

`WebglStage` remains the single Canvas owner. It performs capability detection, attaches one context-loss listener, removes the prior listener before remount, cleans it on unmount, and uses a changing key for a clean retry context. The Digital Twin creates no secondary renderer or animation loop.

## Rendering policy

- Device pixel ratio capped at 1.75 for this large viewer.
- Geometry is memoized and disposed on unmount by the accepted human figure.
- Camera changes are event-driven effects, not React state updates per frame.
- Rotation mutates only a Three group ref.
- Frameloop is `always` only for visible, default-view, user-playing, non-reduced motion.
- Paused, focused, reduced, or hidden states use `demand` rendering.
- ResizeObserver is disconnected on unmount.
- Visibility listener is removed on unmount.

## Measured build impact

Next build passed with 14/14 generated pages. It reported `/digital-twin` route JS of 3.43 kB and 106 kB first-load JS; the dynamic WebGL chunk is loaded client-side. No external GLB, texture, or network asset was added.

## Runtime console

No error was observed. One warning was observed once per mount: Three.js deprecates `THREE.Clock` in favor of `THREE.Timer`; this originates in the installed React Three Fiber dependency. It is documented rather than hidden.

## Runtime acceptance gaps

The controlled browser did not expose safe capability toggles for WebGL unsupported/context loss. Runtime loss/retry is therefore `BLOCKED_EXTERNAL`; structural checks pass but are not claimed as equivalent to runtime evidence.
