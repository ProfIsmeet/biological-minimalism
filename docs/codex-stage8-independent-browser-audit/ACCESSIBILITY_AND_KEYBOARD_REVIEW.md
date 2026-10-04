# Accessibility and keyboard review

PASS for tested keyboard and accessibility-tree behavior; actual screen-reader acceptance is **DEFERRED** by instruction.

- Skip link: first Tab, visible 2px focus outline, Enter moved focus to `main#main-content`.
- Demo Controls: Enter opened an `aria-modal=true` dialog; focus began on Close, remained trapped after 12 Tabs, Escape closed, focus returned to opener.
- Mobile More menu: same dialog semantics; focus remained trapped after 14 Tabs; Escape restored focus to More.
- Shell navigation: all eight route links activated and produced the correct URL.
- AX inspection: one H1, coherent landmarks/headings, named controls, table semantics, status text, and chart alternatives were present on representative routes.
- No hidden-behind-dialog focus was observed; structural modal and live-region verifiers pass.
- VoiceOver was not enabled. Screen-reader behavior is deferred, not passed.
