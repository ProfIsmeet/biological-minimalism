"use client";

import { useCallback, useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

/**
 * Stage 2 A3 — shared modal-dialog focus/scroll/inert primitive, extracted
 * from the tested behavior already shipped in DemoControlDrawer.tsx (Prompt-4
 * §10 / Prompt-4A MEDIUM-1) rather than reimplemented for the mobile "More"
 * sheet. Both consumers must portal their dialog markup to `document.body`
 * (via `react-dom`'s `createPortal`) so the background-inert step below can
 * correctly identify "every other direct child of body."
 *
 * Provides, for as long as `open` is true:
 *  - Full Tab/Shift+Tab focus containment inside `panelRef`, Escape to close.
 *  - Document scroll lock, restored to its exact prior value on close.
 *  - Every other direct child of `<body>` marked `inert` + `aria-hidden`, so
 *    background content cannot be reached by keyboard, pointer, or a screen
 *    reader's virtual cursor — restored to its exact prior state on
 *    close/unmount, so navigation or unmount can never leave the page inert.
 *  - Focus restored to `triggerRef` only after background inert is lifted
 *    (so the trigger is actually focusable again), and only if that node
 *    still exists — a stale ref simply results in a no-op focus() call.
 *  - Route-change-safe cleanup: if the route changes while still marked
 *    open (e.g. browser back/forward, not a same-component Link click that
 *    already calls the caller's `onClose`), `onClose` fires so the caller's
 *    `open` state — and therefore every effect above — unwinds instead of
 *    leaving stale scroll-lock/inert state on the new page.
 */
export const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

interface UseModalDialogOptions {
  open: boolean;
  onClose: () => void;
  panelRef: React.RefObject<HTMLElement | null>;
  triggerRef: React.RefObject<HTMLElement | null>;
  overlayRef: React.RefObject<HTMLElement | null>;
}

export function useModalDialog({ open, onClose, panelRef, triggerRef, overlayRef }: UseModalDialogOptions) {
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  const close = useCallback(() => onCloseRef.current(), []);

  // Focus containment + Escape, attached while the dialog is open.
  useEffect(() => {
    if (!open) return;
    function visibleFocusables(): HTMLElement[] {
      const panel = panelRef.current;
      if (!panel) return [];
      return Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(
        (element) => element.offsetParent !== null || element === document.activeElement,
      );
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        close();
        return;
      }
      if (event.key !== "Tab") return;
      const focusables = visibleFocusables();
      if (focusables.length === 0) {
        event.preventDefault();
        panelRef.current?.focus();
        return;
      }
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (!first || !last) return;
      const active = document.activeElement as HTMLElement | null;
      if (!panelRef.current?.contains(active)) {
        event.preventDefault();
        first.focus();
      } else if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    (panelRef.current?.querySelector<HTMLElement>(FOCUSABLE_SELECTOR) ?? panelRef.current)?.focus();
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, close, panelRef]);

  // Lock document scrolling while open, restore exactly on close.
  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  // Make the rest of the document genuinely inert while open. Every direct
  // child of <body> except the portaled overlay gets `inert` + `aria-hidden`,
  // and its exact prior state is restored on cleanup (close, route change, or
  // unmount).
  useEffect(() => {
    if (!open) return;
    const overlay = overlayRef.current;
    const trigger = triggerRef.current;
    const restores: Array<() => void> = [];
    for (const el of Array.from(document.body.children)) {
      if (overlay && (el === overlay || overlay.contains(el))) continue;
      const hadInert = el.hasAttribute("inert");
      const prevAriaHidden = el.getAttribute("aria-hidden");
      el.setAttribute("inert", "");
      el.setAttribute("aria-hidden", "true");
      restores.push(() => {
        if (!hadInert) el.removeAttribute("inert");
        if (prevAriaHidden === null) el.removeAttribute("aria-hidden");
        else el.setAttribute("aria-hidden", prevAriaHidden);
      });
    }
    return () => {
      for (const restore of restores) restore();
      // Restore focus to the trigger only after the background `inert` is
      // cleared, so a still-existing trigger is focusable again; a stale/
      // unmounted trigger ref makes this a harmless no-op.
      trigger?.focus();
    };
  }, [open, overlayRef, triggerRef]);

  // Route-change-safe cleanup: a Link click inside the dialog already calls
  // the caller's onClose synchronously before navigating, but browser back/
  // forward (or any navigation not mediated by an in-dialog Link) would
  // otherwise leave `open` stuck true on the new page, with scroll-lock and
  // background-inert state never torn down.
  const pathname = usePathname();
  const previousPathnameRef = useRef(pathname);
  useEffect(() => {
    if (open && pathname !== previousPathnameRef.current) close();
    previousPathnameRef.current = pathname;
  }, [pathname, open, close]);
}
