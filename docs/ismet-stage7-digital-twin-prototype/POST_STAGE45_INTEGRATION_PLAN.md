# Stage 7 Digital Twin Prototype — Post-Stage-4/5 Integration Plan

This plan is written for a future controlled port, once the parallel Stage 4-5 visual-command-deck correction branch is independently accepted. **This plan is not executed by this branch.** No integration, no navigation wiring, and no product-route change is performed here.

## 1. Files that can be cherry-picked largely unchanged

- `stage7PrototypeModel.ts`, `stage7PrototypeCamera.ts` — pure logic with zero styling dependency. Port as-is; these already import only the authoritative `lib/architecture`/`humanLayout`/`humanGeometry` modules.
- `Stage7HumanModel.tsx`, `Stage7SensorAnchors.tsx`, `Stage7RegionFocus.tsx`, `Stage7Lighting.tsx` — pure Three.js/R3F components with no Tailwind/CSS class dependency. Port as-is, or fold their material/lighting improvements directly into the accepted `humanMaterials.ts` if the design owner decides the brightness/contrast fix should become the product default (see §3).
- `Stage7PrototypeCanvas.tsx` — the `WebglStage` reuse pattern and camera-rig logic transfer directly; only the outer `className="stage7-canvas-frame"` needs remapping to whatever container class the accepted Stage 4-5 layout uses.

## 2. Files that must be adapted to the accepted shared design tokens

- `stage7Prototype.css` — this is deliberately a plain, namespaced CSS file with hand-picked colors (`#0A1114`, `#F2C265`, etc.) rather than the product's Tailwind utility classes / shared design tokens, precisely so it could be built without touching `globals.css` or `tailwind.config.*` during this isolated phase. Before product integration, every color/spacing value in this file should be re-expressed using whatever shared tokens Stage 4-5 establishes (a CSS custom-property palette, Tailwind theme extension, etc.), and the plain-CSS approach should likely be replaced with Tailwind utility classes matching the rest of the product for consistency — this file's win here was the visual language it proves (opaque matte silhouette, restrained decoration, deterministic views), not its literal implementation as CSS.
- `Stage7ViewControls.tsx`, `Stage7SemanticTopology.tsx`, `Stage7StaticFallback.tsx`, `Stage7DigitalTwinPrototype.tsx` — all use plain string classNames tied to `stage7Prototype.css`; these need their JSX className props remapped to the accepted product's actual button/list/panel component patterns (e.g. reusing whatever `Panel`/`Button` primitives the accepted Stage 4-5 branch establishes) rather than being ported as freestanding markup.

## 3. Which existing human components would eventually be replaced

- If the design owner accepts the brightened matte-material treatment, `humanMaterials.ts`'s `bodyMaterial`/`jointMaterial` values would be updated in place (not duplicated) to the prototype's brighter tones — this is a values-only change to an existing file, not a new file.
- `HumanScanRings.tsx`'s always-on ambient scan rings could be replaced by `Stage7RegionFocus.tsx`'s selection-gated outline pattern, if the design owner agrees the always-on rings read as decorative rather than informative (see `CURRENT_SYSTEM_AUDIT.md` F3). This would be a genuine product behavior change requiring its own review, not something this branch performs.
- `ConceptualTwinStage.tsx`'s free-running auto-rotation could be replaced by the prototype's deterministic-view-buttons-only interaction model, if the design owner agrees manual inspection should take priority over ambient rotation for a jury/projector context (see `CURRENT_SYSTEM_AUDIT.md` F4). Again: a decision for the design owner, not performed here.

## 4. How to integrate without duplicating GLB loads

Not applicable — neither the current product nor this prototype loads a GLB asset (see `ASSET_AND_LICENSE_AUDIT.md`). If a future iteration introduces a real asset, the integration should ensure only one `useGLTF`/loader call exists for it, shared via a context or a single top-level load, not one per consuming component.

## 5. How to retain Mission Overview's fail-closed behavior

The prototype's topology/anchor data is 100% static (architecture facts only) and never touches `missionStore`, `useOperationalViewModel`, or any telemetry-gated state. When/if any of this prototype's presentation ideas are ported into the OPERATIONAL avatar (as opposed to the conceptual Digital Twin), the port must go through `OperationalPhysiologyStage.tsx`'s existing `buildSensorAnchors`/operational-view-model pipeline exactly as `PhysiologyAvatar3D.tsx` already does — never by having a ported component read architecture constants directly and bypass the fail-closed gating that pipeline provides for live/telemetry-derived state.

## 6. How to preserve the Digital Twin's architecture-only boundaries

Every disclosure sentence in `Stage7DigitalTwinPrototype.tsx` ("Untrained", "Unvalidated", "Not personalized", "Not a patient model", "Not a clinical tool", "Not evidence of live astronaut monitoring") must be carried into whatever product component eventually supersedes `ConceptualTwinStage.tsx`'s own disclosure text — verbatim or a reviewed equivalent, never silently dropped for visual cleanliness.

## 7. How to run regression tests after integration

1. Re-run `npm run verify:monitoring` and confirm the count only increases, never decreases, from the accepted Stage 4-5 branch's own baseline.
2. If any product file (`humanMaterials.ts`, `HumanScanRings.tsx`, `ConceptualTwinStage.tsx`, etc.) is modified as part of the port, add or update the relevant existing structural check (e.g. `verify-webgl-fallback.mjs`'s consumer list, or a new equivalent) rather than leaving the ported behavior unverified.
3. Re-run `npm run build` and confirm the static page count and route list match expectations for whatever the integrated route structure becomes.
4. Manually re-inspect `/digital-twin` (or wherever the ported treatment lands) in a real browser at the same viewport/state matrix this prototype used (see `VERIFICATION_LEDGER.md`), plus the mobile/200%-zoom/OS-screen-reader coverage this prototype could not obtain in its own sandboxed environment.

## 8. Decisions that require a design owner

- Whether to adopt the brighter matte material treatment as the new product default (§3).
- Whether to replace always-on ambient scan rings with selection-gated region focus (§3).
- Whether to replace free-running auto-rotation with deterministic-view-only interaction (§3).
- Whether the semantic topology list pattern should become the shared accessible-equivalent pattern for both the operational avatar and the Digital Twin, or remain Digital-Twin-specific.

## 9. Prototype files that should be deleted after a successful port

Once ported, the entire `frontend/src/prototypes/stage7-digital-twin/` directory, the isolated route `frontend/src/app/research/stage7-digital-twin-prototype/`, its verifier script, and its `qa-screenshots/ismet-stage7-digital-twin-prototype/` evidence directory should all be deleted from the integrating branch — none of it is meant to persist as a permanent parallel surface once its ideas have been ported into the real product components. The `docs/ismet-stage7-digital-twin-prototype/` reports may be retained as historical design-rationale documentation or archived, per the design owner's preference.
