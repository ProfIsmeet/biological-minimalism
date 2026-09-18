// Minimal Node module-customization hook (node:module register API, already
// part of the Node 22 runtime — no new dependency). Node's ESM resolver
// requires explicit file extensions; this repo's TypeScript sources use
// extensionless relative/alias imports (moduleResolution: "bundler", the
// same convention webpack/Next.js already resolve at build time). Rather
// than rewrite production import style to suit a verification script, this
// hook retries a failed resolution with ".ts" appended — used only when
// running frontend/scripts/verify-monitoring-state.ts directly under
// `node --experimental-strip-types`.
export async function resolve(specifier, context, nextResolve) {
  try {
    return await nextResolve(specifier, context);
  } catch (error) {
    const isRelative = specifier.startsWith(".") || specifier.startsWith("/");
    if (isRelative && error?.code === "ERR_MODULE_NOT_FOUND" && !specifier.endsWith(".ts")) {
      return nextResolve(`${specifier}.ts`, context);
    }
    throw error;
  }
}
