# Accessibility and Interaction Review

## Keyboard and focus

- Viewer is independently focusable with a descriptive accessible name.
- `1` Front; `2` Back; `3` Chest; `4` Wrist; `Home`, `Escape`, or `0` reset; `Space`/`P` toggle playback intent.
- Buttons have 44 px minimum height, `aria-pressed`, readable labels, and explicit focus-visible outlines.
- Real keyboard QA verified focus entry, visible viewer focus ring, chest selection, wrist selection, and Escape reset.
- No scroll-trapping pointer handlers or free-orbit control are used.

## Semantic alternative

The canvas is nonessential to understanding. Adjacent HTML exposes active view, active module (or “no region focus”), all modules, modalities, descriptions, and the scientific boundary. The static WebGL fallback includes an SVG with title/description and repeats current-view and limitation text.

## Accessibility tree

The real browser tree exposed the viewer region, five pressed-state view controls, playback/reset buttons, three module controls, sensor legend, active-view summary, and scientific boundary. Chest and wrist selection changed the pressed states and semantic summary correctly.

## Reduced motion

The shared OS/app OR-rule hook is used. Automatic rotation and scan movement stop; the render loop becomes demand-driven; all preset controls remain enabled. Same-tab and cross-tab behavior were exercised through the existing Settings switch. The user playback preference is not overwritten.

## Deferred

VoiceOver or another actual screen reader was not run. `ACTUAL_SCREEN_READER_STATUS: OWNER_DEFERRED`.
