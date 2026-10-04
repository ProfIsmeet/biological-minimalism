# Change-scope audit

The complete `dc2039d53773ebfad763e0716f51876fb8185058..208c1b44c7c99d7b9a41e7e1807e5a0e67650645` source diff contains 106 files:

| Class | Count | Audit emphasis |
|---|---:|---|
| Stage 8 reports | 14 | Treated as claims, not proof |
| Incoming evidence manifest | 1 | Provenance and ambiguity |
| App routes/layout | 12 | metadata, server/client split, static Settings |
| Components | 72 | typography, control sizes, charts, shell, scientific semantics |
| Runtime/monitoring libraries | 2 | timeline/source truth |
| Verification scripts | 3 | guard preservation and rendered behavior |
| Package/design configuration | 2 | command wiring and tokens |

High-risk families received source and browser review: Mission Overview scientific graphics, Live Monitoring and its right rail, System Brief, Experimental Research, Digital Twin, AI Insights, Mission Timeline, Settings, shared navigation, modal primitives, reduced motion, WebGL fallback, status components, and route metadata.

The source test diff did not remove a test. Existing assertions were not loosened. The review adds 14 monitoring assertions and two deterministic backend concurrency tests. Browser conclusions were not replaced by source-string checks; structural checks only preserve browser-found fixes.
