// Minimal Node module-customization hook (node:module register API, already
// part of the Node 22 runtime — no new dependency). Node's ESM resolver
// requires explicit file extensions; this repo's TypeScript sources use
// extensionless relative/alias imports (moduleResolution: "bundler", the
// same convention webpack/Next.js already resolve at build time). Rather
// than rewrite production import style to suit a verification script, this
// hook retries a failed resolution with ".ts" appended — used only when
// running frontend/scripts/verify-monitoring-state.ts directly under
// `node --experimental-strip-types`.
//
// It also rewrites the `@/*` alias to `src/*`, mirroring tsconfig.json's own
// `"paths": {"@/*": ["./src/*"]}`. Most `@/...` imports encountered by the
// verify script are `import type`-only and get erased before resolution
// ever runs, but a pure module can legitimately need a real (non-type)
// value from another `@/...` module — Node has no native knowledge of the
// alias, so without this rewrite that import fails outright.
import { pathToFileURL } from "node:url";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "src");

export async function resolve(specifier, context, nextResolve) {
  if (specifier.startsWith("@/")) {
    const rewritten = pathToFileURL(join(SRC_ROOT, specifier.slice(2))).href;
    return resolve(rewritten, context, nextResolve);
  }
  try {
    return await nextResolve(specifier, context);
  } catch (error) {
    const isRelative = specifier.startsWith(".") || specifier.startsWith("/") || specifier.startsWith("file://");
    if (isRelative && error?.code === "ERR_MODULE_NOT_FOUND" && !specifier.endsWith(".ts")) {
      return nextResolve(`${specifier}.ts`, context);
    }
    throw error;
  }
}
