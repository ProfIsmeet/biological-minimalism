/**
 * Prompt-4A HIGH-1 — one canonical encoding for the persisted reduced-motion
 * preference, shared by the `/settings` toggle (which reads/writes it) and
 * mirrored by the pre-paint boot script in `app/layout.tsx` (which cannot
 * import a module because it runs during HTML parse, before any bundle loads).
 *
 * Accepted "enabled" values: "1" (the value Settings writes) and, for backward
 * compatibility, the legacy "true". Everything else — "0", "false", missing,
 * empty, or any unexpected string — means NOT enabled. The boot script uses the
 * exact same acceptance set (`v === '1' || v === 'true'`), so a preference
 * enabled in Settings is applied before first paint on every route after a
 * reload.
 */
export const REDUCE_MOTION_KEY = "biomin:reduce-motion";

/** The value Settings writes when enabling reduced motion. */
export const REDUCE_MOTION_ON = "1";
/** The value Settings writes when disabling reduced motion. */
export const REDUCE_MOTION_OFF = "0";

/**
 * Given a raw localStorage value (or null when absent), decide whether reduced
 * motion is enabled. Pure and deterministic so the accepted values are asserted
 * directly in tests rather than by string-matching the boot script.
 */
export function reduceMotionEnabledFromStorage(value: string | null | undefined): boolean {
  return value === "1" || value === "true";
}
