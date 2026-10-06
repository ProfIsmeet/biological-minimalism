# Dialog and focus review

Demo Control Drawer in local Chrome: focus moved to Close; the background disappeared from the accessibility tree; Shift+Tab from the first control wrapped to the last enabled control; Escape closed; focus returned to the exact Demo controls trigger. Reopening did not duplicate the surface.

The shared modal primitive and both known consumers pass the deterministic dialog verifier. A real VoiceOver run at 390×844 for the mobile More dialog was not completed, and exact dialog-role speech was not captured. Result: keyboard/focus `PASS`, VoiceOver speech/mobile matrix `PARTIAL`.
