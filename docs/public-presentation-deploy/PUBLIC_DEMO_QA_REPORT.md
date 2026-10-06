# Public demo QA report

Status: **PENDING PUBLIC DEPLOYMENT**

The public build deliberately removes source, playback, reset, speed, and fault controls from visitor-facing surfaces and shows a visible `Public · read-only` state. The backend independently enforces the boundary, so bypassing or modifying the frontend cannot mutate shared demo state.

The final QA pass must cover direct URL entry, refresh, mobile navigation, keyboard use, reduced motion, 200% zoom, reconnect behavior, replay freshness, S14 provenance language, and continuous multi-client observation.
