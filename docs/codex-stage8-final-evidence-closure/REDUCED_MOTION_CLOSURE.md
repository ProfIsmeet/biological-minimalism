# Reduced-motion closure

## Method

Google Chrome 154.0.8037.93 was controlled through Playwright/CDP browser media emulation for `prefers-reduced-motion: reduce`. This is standards-based media emulation; it is not a `matchMedia` monkey patch and is not described as a physical operating-system Settings toggle.

## Fourteen-scenario result

All 14 scenarios passed:

1. Initial media query was `no-preference`.
2. Application preference initially off.
3. Live CDP media transition became `reduce`.
4. OS/browser media alone activated effective reduction.
5. Digital Twin content remained readable.
6. No information was hidden.
7. Live transition returned to normal.
8. Cross-tab setting synchronization worked.
9. Persisted app preference activated reduction while OS/browser preference was normal.
10. Preference survived a route switch.
11. User play/pause intent remained represented and operable.
12. Dialog opened under reduced motion.
13. Dialog closed without restoring unwanted animation.
14. Cross-tab disable restored normal behavior when OS/browser preference was normal.

The effective contract is `OS preference OR application preference`. Charts and Digital Twin content retained meaning; no essential state depended solely on motion. Representative canonical files are `motion-normal-mo.png` and `motion-reduced-dt.png`.
