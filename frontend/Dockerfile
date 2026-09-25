FROM node:20-slim AS deps
WORKDIR /app
# Copy the manifest AND the committed lockfile, then install with `npm ci`.
# `npm ci` installs strictly from package-lock.json and fails the build if the
# lockfile and package.json disagree, so container dependency resolution is
# deterministic and cannot silently drift between machines. (`npm install`
# could mutate the resolution and, without the lockfile copied, produced a
# fresh, non-reproducible tree.) Both files are copied before the rest of the
# source so this layer stays cached until dependencies actually change.
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
# NEXT_PUBLIC_* variables are inlined into the client bundle at build time,
# so the backend origin must be supplied as a build arg (see docker-compose.yml),
# not just a runtime environment variable. These are PUBLIC browser
# configuration values (they end up in the shipped client bundle) — never put a
# secret in a NEXT_PUBLIC_* variable.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
# The WebSocket origin is derived from NEXT_PUBLIC_API_BASE_URL at runtime when
# left unset (see frontend/src/lib/config.ts). It is also exposed as an explicit
# build arg so a non-local deployment whose WS endpoint is not a simple
# http->ws transform of the API origin can pin it directly and unambiguously.
ARG NEXT_PUBLIC_WS_URL=
ENV NEXT_PUBLIC_WS_URL=${NEXT_PUBLIC_WS_URL}
RUN npm run build

FROM node:20-slim AS run
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=build /app/public ./public
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
EXPOSE 3000
CMD ["npm", "run", "start"]
