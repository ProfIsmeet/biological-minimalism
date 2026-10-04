# Reduced-motion review

Result: **PARTIAL**.

The application preference began off, toggled live to on, synchronized to a second same-origin tab, and synchronized back to off. The final structural verifier confirms one source of truth (persisted setting OR OS query) and coverage of Framer/WebGL consumers. Diagrams remained understandable without relying on motion.

The browser harness does not expose OS `prefers-reduced-motion` emulation, so OS-preference response is `BLOCKED_EXTERNAL`. User play/pause intent for real replay could not be exercised because the S14 source was unavailable.
