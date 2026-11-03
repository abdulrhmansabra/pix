# Figma SVG → Android Compose extraction pipeline

This repository contains a two-screen Figma export:
- pix.svg: visual source/export.
- pix.css: named layer measurements and styling.
- pix.kt: legacy placeholder XML snippets; it is not Kotlin Compose.

## Current pipeline

### Stage 1 — CSS measurements and design spec

Run:

    python tools/figma_to_compose.py --css pix.css --svg pix.svg --out generated --scale 3

The tool creates:
- generated/pix-design-manifest.json: named CSS sections, source px values, converted dp values, colors, gradients, borders and typography.
- generated/PixDesignSpec.kt: typed Kotlin data describing those measurements.

The default scale is 3 export pixels per Android dp (1080px → 360dp). Change --scale if the source frame uses a different density. The source pix.css and pix.svg are read-only inputs.

### Stage 2 — Compose screen implementation

compose/PixScreens.kt contains:
- PixTemplateBrowsingScreen
- PixProfileScreen

The screen geometry, layout positions, colors, gradients, borders, radii and text metrics are based on pix.css. The 1080px CSS coordinate system is scaled to a 360dp design width while preserving each frame's aspect ratio.

Use COMPOSE_IMPLEMENTATION.md for integration and the required text/artwork inputs. svg-css-layer-map.json records the CSS-layer-to-PixArtwork-slot mapping. That mapping is a target-slot list, not proof that identically named SVG groups exist.

### Stage 3 — SVG structural inventory

Run:

    python tools/inspect_svg.py pix.svg --out generated/svg-inspection.json

The version 2 report includes the full element hierarchy, parent/child links, transform matrices, supported primitive bounds, image usage, and resolved/unresolved internal references. It is read-only and does not rewrite SVG content. See SVG_INSPECTION.md for the report fields and geometry limitations.

Regression tests:

    python -m unittest discover -s tests -v

### Stage 4 — Confirmed source-art mapping

Use the regenerated v2 report to trace real nodes and references. Do not assign CSS names to SVG nodes based solely on visual proximity or guessed naming. Verify the actual subtree, transforms, clipping/masking references and image reuse before exporting an artwork asset and binding it to a PixArtwork slot.

## Accuracy boundary

The SVG and CSS exports are distinct inputs. The SVG root viewBox and the CSS frame dimensions may not share the same coordinate width. Treat each file's own coordinate system as authoritative until the exact relationship is verified from source geometry and transforms.

The inspector is not a renderer: it does not calculate path/text bounds, stroke-expanded bounds, CSS-computed appearance, or final filter/mask/clip output. Its group bounds are partial estimates only. Structural mapping is not visual or pixel-perfect validation.

Do not replace the source SVG/CSS or silently approximate missing artwork. Do not claim visual parity until all original artwork has been bound and screenshots have been compared against the source frames.
