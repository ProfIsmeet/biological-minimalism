# Accessibility scope and deferral

## Browser and keyboard acceptance

Chrome accessibility data was obtained through the DevTools Protocol `Accessibility.getFullAXTree`, not inferred only from DOM markup. Eight principal routes were checked. Result: 51 pass, 0 fail.

Every route exposed a root web area/document, one main landmark, navigation, headings, and non-empty accessible names for interactive controls. Cross-route inventory included tables with captions/rows/headers/cells, named buttons and switches, regions, alerts, status roles, figures and figure captions, lists, definitions, and disclosure controls where applicable.

Keyboard verification covered visible focus, opening the named source/replay/fault dialog with Enter, reverse-tab containment within the dialog, Escape dismissal, and restoration of focus to the trigger. The capture run also verified the skip link, shared dialog primitive, navigation, and semantic alternatives. Expandable research content and chart alternatives remained represented in the accessibility tree.

## Explicit boundary

`ACTUAL_SCREEN_READER_STATUS: DEFERRED_BY_OWNER`

No claim of VoiceOver pass or failure is made. The deferral is intentional for the final accessibility stage and is not a Stage 8 blocker.
