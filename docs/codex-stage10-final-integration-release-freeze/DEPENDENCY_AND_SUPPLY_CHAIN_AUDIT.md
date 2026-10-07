# Dependency and Supply-Chain Audit

Lock/manifest agreement passed through clean `npm ci`; `pip check` reported no broken requirements. The clean run exposed three ranged scientific packages, so Stage 10 pinned its tested NumPy 2.5.3, scikit-learn 1.9.1, and SHAP 0.52.0 versions. Docker pins Torch 2.6.0 CPU. No workflow directory is present, so no GitHub Action or unpinned workflow download is in the candidate.

`npm audit`: 0 critical, 11 high, 3 moderate, 14 total registry findings. The affected trees are ESLint/Tailwind glob/watch tooling, Next-bundled PostCSS, source-map parsing, and Sharp. They process trusted repository/build artefacts; this application accepts no untrusted CSS/source maps, exposes no build tooling at runtime, and uses no `next/image` or user-supplied Sharp path. Suggested automatic fixes cross major Next/Tailwind/config boundaries. No broad dependency update was justified during freeze.

This classification is not a vulnerability-free certification. Re-evaluate supported Next/Tailwind upgrades after release. Dataset attribution and model provenance remain present; external assets are hash-identified, licensed, and not embedded.
