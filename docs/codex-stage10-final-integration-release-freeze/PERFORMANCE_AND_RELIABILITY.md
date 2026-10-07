# Performance and Reliability

Production build generated 14/14 pages. The continuous 1080p eight-route walkthrough completed in 11.479 seconds. Public WSS smoke ran 60 seconds with two coherent clients; local endurance ran 600 seconds with three.

Each local client received 1,143 frames and 1,140 predictions, ended at window 1495, and had zero cross-client window spread. RSS sampled every 30 seconds fell from the initialization peak and remained approximately 42–55 MiB thereafter; no unbounded trend was observed. The run found no duplicate socket ownership, runaway listener, repeated convergence, retained history growth, WebGL blank state, or explanation concurrency failure.

No SLA is claimed. Public cold-start timing was not independently induced; the observed public browser became usable during the normal smoke window.
