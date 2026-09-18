// Bootstrap for `node --experimental-strip-types scripts/run-verify-monitoring-state.mjs`.
// Registers the extension-resolution hook (see ts-extension-loader.mjs)
// before dynamically importing the actual verification script, since a
// module's own static imports resolve before any code in that module runs.
import { register } from "node:module";

register("./ts-extension-loader.mjs", import.meta.url);

await import("./verify-monitoring-state.ts");
