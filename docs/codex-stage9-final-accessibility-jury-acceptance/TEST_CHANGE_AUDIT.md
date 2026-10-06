# Test change audit

No test was removed and no behavior was weakened. One blanket assertion was replaced with an equally strict, more precise assertion that every unconfirmed non-paused case remains unable to issue Play. New checks distinguish the sole safe recovery case (paused replay awaiting its first frame) from already-playing and synthetic states. No retry was added. No VoiceOver claim is derived from these tests.

`git diff` was reviewed for the test change and the product implementation together.
