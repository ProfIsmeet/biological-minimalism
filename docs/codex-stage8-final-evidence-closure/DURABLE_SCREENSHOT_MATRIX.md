# Durable screenshot matrix

All images are full-page or exact native browser-window PNGs from the final implementation checkpoint. Every file decoded, had non-zero bytes, matched its recorded dimensions and SHA-256, and received a visual `PASS`. No browser error overlay, loading skeleton, private path, secret, unrelated desktop content, clipped essential control, horizontal page overflow, or false source error was observed.

| Coverage group | Required | Captured | Result |
|---|---:|---:|---|
| Mission Overview: 1440×900, 1366×768, 1280×720, 1024×768, 768×1024, 390×844 | 6 | 6 | PASS |
| Live Monitoring: same six viewports | 6 | 6 | PASS |
| Six remaining principal routes at 1440×900 and 390×844 | 12 | 12 | PASS |
| Real S14 nominal/fault/withheld/rebuilding/recovered/fresh | 6 | 6 | PASS |
| Genuine 100%/200% zoom on four routes | 8 | 8 | PASS |
| Normal/reduced motion | 2 | 2 | PASS |
| Total | 40 | 40 | PASS |

The responsive review covered the complete vertical pages. Scripted checks found zero horizontal overflow, exactly one page heading, no essential text below 12 px, and no error/loading residue at each responsive slot. Visual inspection confirmed readable charts, axes, labels, legends and alternatives; intact right rails and navigation; Stage 6 scientific plots; Stage 7 human geometry; and the accepted Mission Overview ring, radar, trend, signal, pipeline, fault/recovery, and provenance semantics.

The authoritative per-file index—including route, viewport, PNG dimensions, browser, zoom, motion, source, replay state, fault state, timestamp, hash, review result, and canonical status—is `EVIDENCE_MANIFEST.json`.
