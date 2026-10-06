# Public presentation access

Use the public read-only frontend at `https://biological-minimalism-iac.vercel.app`. It connects to the Render Free backend at `https://biological-minimalism-api.onrender.com` and presents recorded PPG-DaLiA subject S14 data; it is not live astronaut monitoring.

## Expected startup

Render Free may sleep. On first open, leave Mission Overview or Live Signals open while the backend wakes. Do not repeatedly reload. The interface may truthfully show loading, disconnected, or awaiting confirmation before it reaches `CONNECTED`, `RECORDED REPLAY`, `PPG-DaLiA · S14`, and a model output. If it has not recovered after roughly two minutes, use Settings → Test connection, then reload once.

## Public boundary

The public site is read-only. Source, replay, speed, reset, and simulated-fault controls are intentionally absent, and the backend independently rejects mutation. No dataset, checkpoint, account, token, or installation is required for a viewer.

## Accessible use

Each principal route has one main heading, a skip link, labeled navigation, text status that does not rely on color, and concise nonvisual chart or table semantics. Settings exposes an application Reduce Motion preference; macOS Reduce Motion is also honored. Stage 9 found no announcement-storm signal in the browser accessibility tree, but exact VoiceOver speech/caption capture was not technically available, so the final VoiceOver verdict remains partial.

## Presentation recovery

Keep one tab open during the talk. If the service is cold, explain the free-tier wake-up, continue with System Brief or Experimental Research, and return to Mission Overview when the header reports connected S14 replay. Never describe the dashboard as clinical, population-validated, or live astronaut telemetry.
