# VoiceOver test environment

- platform: macOS
- initial/final VoiceOver: off/off
- actual VoiceOver enabled during test: yes
- Safari: public primary route and idle review
- Chrome Guest: public cross-check and local full-control interaction
- Caption Panel setting: enabled, but overlay/speech unavailable to automation capture
- microphone/system-audio recording: none
- dedicated dashboard windows: used; unrelated apps hidden
- notification previews: temporarily Never, restored to When Unlocked
- Arrow-key Quick Nav: temporarily enabled during troubleshooting, restored off
- original/final Reduce Motion: off/off

Limitation: the control surface could inspect the native browser accessibility tree while VoiceOver ran, but could not reliably inject VO-modifier/rotor commands or read transient spoken/caption output. Therefore source text and accessibility snapshots are supporting evidence only.
