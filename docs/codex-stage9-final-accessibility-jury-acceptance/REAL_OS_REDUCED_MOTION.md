# Real macOS reduced-motion acceptance

Original state: off. With application preference off, real macOS Reduce Motion was enabled. Digital Twin changed to “Rotation paused,” stated that reduced motion was active, retained its presets and semantic architecture summary, and continued rendering WebGL. Focus remained stable.

OS Reduce Motion was disabled and the application preference independently produced the same effective paused behavior. This verifies `OS OR application` semantics. Both sources were restored off. Result: `PASS`.
