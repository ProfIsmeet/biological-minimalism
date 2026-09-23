// Public (non-secret) browser configuration for reaching the backend.
//
// These values come from NEXT_PUBLIC_* variables, which Next.js inlines into
// the client bundle at BUILD time (see frontend/.env.local.example,
// frontend/Dockerfile, docker-compose.yml, and docs/JURY_DEPLOYMENT_RUNBOOK.md).
// Because they ship in the browser bundle they are PUBLIC configuration —
// never place a secret in a NEXT_PUBLIC_* variable.
//
// An empty string is treated the same as "unset": an explicit-but-empty build
// arg (the Dockerfile always defines NEXT_PUBLIC_WS_URL, defaulting to empty)
// must fall back to the documented derivation rather than emit a malformed URL.

function firstConfiguredValue(...values: (string | undefined)[]): string | undefined {
  for (const value of values) {
    if (typeof value === "string" && value.trim() !== "") {
      return value.trim();
    }
  }
  return undefined;
}

export const API_BASE_URL =
  firstConfiguredValue(process.env.NEXT_PUBLIC_API_BASE_URL) ?? "http://localhost:8000";

/**
 * Derive the live-feed WebSocket URL from an http(s) API base URL:
 *   http://host:8000       -> ws://host:8000/ws/live-feed
 *   https://host           -> wss://host/ws/live-feed
 *   https://host/api/      -> wss://host/api/ws/live-feed  (trailing slash trimmed)
 *
 * The leading `http` -> `ws` swap also maps `https` -> `wss`. A trailing slash
 * on the API base URL is removed first so the `/ws/live-feed` suffix is never
 * doubled. An explicitly supplied NEXT_PUBLIC_WS_URL always takes precedence
 * over this derivation.
 */
export function deriveWebSocketUrl(apiBaseUrl: string): string {
  const withoutTrailingSlash = apiBaseUrl.replace(/\/+$/, "");
  return withoutTrailingSlash.replace(/^http/, "ws") + "/ws/live-feed";
}

export const WS_URL =
  firstConfiguredValue(process.env.NEXT_PUBLIC_WS_URL) ?? deriveWebSocketUrl(API_BASE_URL);
