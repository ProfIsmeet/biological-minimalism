"use client";

import { useEffect, useState } from "react";

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
 * Fired on `window` by the `/settings` toggle immediately after it writes
 * `REDUCE_MOTION_KEY`, so every already-mounted `useReducedMotionPreference()`
 * consumer in the SAME tab updates immediately. The native `storage` event
 * exists for this key too, but browsers never fire it in the tab that made the
 * write — only in *other* tabs/windows — so a same-tab custom event is the
 * only way to propagate without a reload.
 */
export const REDUCE_MOTION_CHANGE_EVENT = "biomin:reduce-motion-changed";

/**
 * Given a raw localStorage value (or null when absent), decide whether reduced
 * motion is enabled. Pure and deterministic so the accepted values are asserted
 * directly in tests rather than by string-matching the boot script.
 */
export function reduceMotionEnabledFromStorage(value: string | null | undefined): boolean {
  return value === "1" || value === "true";
}

/**
 * Stage 2 A2 — single shared source of truth for whether motion should be
 * reduced, combined from EITHER of the two independent inputs the rest of the
 * app must never disagree about:
 *   1. the persisted `/settings` toggle (`REDUCE_MOTION_KEY` in localStorage)
 *   2. the OS-level `prefers-reduced-motion: reduce` media query
 *
 * Either one alone is sufficient — this mirrors the CSS-layer rule in
 * globals.css, which applies the same override for `html.reduce-motion` OR
 * `@media (prefers-reduced-motion: reduce)` independently. Every JS-driven
 * animation decision in this app (Framer Motion via `MotionConfigProvider`,
 * `useFrame` WebGL rotation loops, decorative rAF/timer-driven motion) must
 * read this hook rather than re-deriving its own OS-only check, or it will
 * silently ignore a user who only enabled the persisted Settings toggle.
 *
 * SSR/hydration-safe: starts `false` (matching the server render, which never
 * knows the client's OS preference or localStorage) and resolves to the real
 * value in an effect after mount — the same pattern already used by
 * `useNowMs` in MissionStatusBar for the same reason. Listens for OS changes,
 * cross-tab `storage` events, and the same-tab `REDUCE_MOTION_CHANGE_EVENT`,
 * and cleans up all three listeners on unmount.
 */
export function useReducedMotionPreference(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");

    const recompute = () => {
      const persisted = reduceMotionEnabledFromStorage(window.localStorage.getItem(REDUCE_MOTION_KEY));
      setReduced(persisted || query.matches);
    };

    recompute();

    const onMediaChange = () => recompute();
    const onStorage = (event: StorageEvent) => {
      if (event.key === REDUCE_MOTION_KEY || event.key === null) recompute();
    };
    const onSameTabChange = () => recompute();

    query.addEventListener("change", onMediaChange);
    window.addEventListener("storage", onStorage);
    window.addEventListener(REDUCE_MOTION_CHANGE_EVENT, onSameTabChange);

    return () => {
      query.removeEventListener("change", onMediaChange);
      window.removeEventListener("storage", onStorage);
      window.removeEventListener(REDUCE_MOTION_CHANGE_EVENT, onSameTabChange);
    };
  }, []);

  return reduced;
}
