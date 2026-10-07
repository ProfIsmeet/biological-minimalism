# Real S14 Final Acceptance

PASS using external PPG-DaLiA S14 bytes and Model B checkpoint; neither was copied into Git.

Verified: discoverability, load paused at zero, Play and 5× replay, source/dataset/subject/channel/model identity, nominal finite HR, route navigation, PPG modality dropout, prediction null/withheld, warm-up, recovered finite HR, and a recovered window index greater than the nominal window. The 600-second run also demonstrated coherent multi-client state and continuing replay. Backend restart and missing-asset paths were separately exercised.

S14 remains a single-participant stress demonstration. Current-session accuracy cannot be computed because the UI/runtime has no aligned reference-HR stream.
