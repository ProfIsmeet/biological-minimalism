# Inherited deployment reconciliation

The older `docs/codex-public-presentation-deployment` package correctly recorded a pre-authorization local-only state, but remained easy to misread after production had shipped. Stage 9 added explicit historical notes and reconciled its status, acceptance, browser, route, endurance, security, rollback, recommendation, and manifest files with the later canonical production evidence.

Reconciled facts: Vercel frontend `https://biological-minimalism-iac.vercel.app`; Render backend `https://biological-minimalism-api.onrender.com`; WSS endpoint; deployed source `08481f69649892c56cd5cf38aed2dad47d02ec37`; PPG-DaLiA S14; public read-only enforcement; real-browser WSS pass; 621-second endurance; and Render Free sleep/wake limitations. No provider or deployment configuration changed.
