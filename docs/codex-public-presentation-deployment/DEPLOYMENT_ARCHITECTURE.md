# Deployment architecture

```text
Browser --HTTPS--> Vercel Next.js (frontend/)
   |                    |
   +--HTTPS REST--------+
   +--WSS---------------> Render FastAPI
                              |
                              +-- private persistent disk: S14 archive
                              +-- private persistent disk: Model B checkpoint
```

Vercel production is configured to track only `codex/public-presentation-deploy`. Render uses `render.yaml`, Docker, `$PORT`, `/health`, one service instance, and Frankfurt region. Exact frontend origin is the sole allowed browser origin.
