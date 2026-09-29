# Before/after visual adjudication

All comparisons use fresh real-WebGL renders of the exact legacy builder and final builder in the same worktree, materials, camera system, and viewport. Desktop diagnostic canvas size is `832×598` from a `1440×900` browser viewport.

## Shoulders

Before, the front and back close-ups show a high triangular shoulder fin on each side. A narrow arm tube begins behind the fin, the clavicle-to-deltoid path changes direction abruptly, and dense doubled lines expose the embedded arm cap/intersection.

After, the neck flows into a gently descending clavicular bridge, an ovoid deltoid, and the upper arm. Front, back, left-oblique, and right-oblique evidence show the same continuous surface. No disc, boundary ring, pyramid, armor pad, or plugged-tube seam remains. Arm/rib negative space remains open and bilateral width is unchanged within the established camera envelope.

Verdict: **PASS** from front, back, three-quarter, left, and right views.

## Pelvis and thighs

Before, the lower torso terminates as a bright flat full-width strip. Two capped thigh tubes start below it, producing a shorts/belt block, a disconnected posterior view, and an artificial gap defined only by cylinder separation.

After, the waist expands through separate iliac/gluteal fields into the upper thighs. The outer contour is continuous in front, back, and three-quarter views; the center withdraws into a rounded crotch cleft. Both legs remain separate, symmetric, aligned, and grounded. No cap disc, full-width cutoff, belt edge, or thigh plug remains.

Verdict: **PASS** from front, back, and three-quarter views.

## Hostile review

The review tried to find a smaller residual fin, hidden posterior cap, unilateral mismatch, torso widening, arm/rib collision, fused thighs, excessive crotch gap, transition crease, flipped normals, rim magnification, floating contacts, preset clipping, mobile unreadability, or lifecycle leak. No high- or medium-severity finding remained. The lattice is denser because the continuous surface has 10,080 vertices; it remains uniformly faint and follows the surface without joint-specific rings.

The first saved evidence attempt was rejected because cleared WebGL drawing buffers produced black PNG files. Those files were overwritten after diagnostic-only buffer preservation was enabled. Every final file listed in the manifest was then opened at original resolution and visually adjudicated.
