# Deployment architecture

```text
Browser --HTTPS--> Vercel Next.js (frontend/)
   |                    |
   +--HTTPS REST--------+
   +--WSS---------------> Render FastAPI
                              |
                              +-- ephemeral verified S14 bundle
                              +-- ephemeral verified Model B checkpoint
                                      ^
                                      | authenticated HTTPS on cold start
                              private GitHub release assets
```

Vercel production is configured to track only `codex/public-presentation-deploy`. Render uses `render.yaml`, Docker, `$PORT`, `/health`, one Free service instance, and Frankfurt region. Exact frontend origin is the sole allowed browser origin. The private bootstrap credential remains server-only and is never forwarded to the signed asset host.
