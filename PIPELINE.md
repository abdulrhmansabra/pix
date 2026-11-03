# Figma SVG → Android Compose extraction pipeline

This repository contains a two-screen Figma export:
- `pix.svg`: visual source/export.
- `pix.css`: named layer measurements and styling.
- `pix.kt`: legacy placeholder XML snippets; it is not Kotlin Compose.

## Stage 1 — CSS measurements and design spec

Run:

    python tools/figma_to_compose.py --css pix.css --svg pix.svg --out generated --scale 3

The tool creates:
- `generated/pix-design-manifest.json`: named CSS sections, source px values, converted dp values, colors, gradients, borders and typography.
- `generated/PixDesignSpec.kt`: typed Kotlin data describing those measurements.

The default scale is 3 export pixels per Android dp (1080px → 360dp). Change `--scale` if the source frame uses a different density. The source `pix.css` and `pix.svg` are read-only inputs.

## Stage 2 — Compose screen implementation

`compose/PixScreens.kt` contains:
- `PixTemplateBrowsingScreen`
- `PixProfileScreen`

The screen geometry, layout positions, colors, gradients, borders, radii and text metrics are based on `pix.css`. The 1080px CSS coordinate system is scaled to a 360dp design width while preserving each frame's aspect ratio.

Use `COMPOSE_IMPLEMENTATION.md` for integration and the required text/artwork inputs. `svg-css-layer-map.json` records the CSS-layer-to-`PixArtwork`-slot mapping. That mapping is a target-slot list, not proof that identically named SVG groups exist.

## Stage 3 — SVG structural inventory

Run:

    python tools/inspect_svg.py pix.svg --out generated/svg-inspection.json

The version 2 report includes the full element hierarchy, parent/child links, transform matrices, supported primitive bounds, image usage, and resolved/unresolved internal references. It is read-only and does not rewrite SVG content. See `SVG_INSPECTION.md` for the report fields and geometry limitations.

Regression tests:

    python -m unittest discover -s tests -v

## Stage 4 — Original raster extraction and frame references

Run:

    python -m pip install CairoSVG
    python tools/export_svg_artwork.py pix.svg --out generated/svg-artwork

The exporter:
- Copies embedded image data-URI payloads byte-for-byte into `generated/svg-artwork/embedded/`.
- Records original SVG image IDs, dimensions, MIME types, SHA-256 hashes and local `<use>` references in `manifest.json`.
- Renders the two 1080px-wide source viewports to `template-browsing.png` and `profile.png`, keeping the original SVG descendants, definitions, transforms and clipping relationships.

The default SVG crop origins are Template browsing x=1200 and Profile x=0; the exporter validates both viewports against the source viewBox. Override the origins only after checking the source geometry. Use `--skip-render` to extract embedded images without CairoSVG.

The PNGs are full-screen comparison references, not individual component painters. The embedded raster files may be full-frame source images reused by SVG clipping and transforms; do not assign them directly to individual Compose slots.

## Stage 5 — Component-level source mapping and Compose binding

Run:

    python -m pip install CairoSVG Pillow
    python tools/export_pix_components.py pix.svg --out generated/pix-artwork

The component exporter creates 25 source-derived image crops as PNG and lossless WebP. Its manifest records each source SVG node path, source clip path, crop dimensions, exact source SVG SHA-256, and the hash of every WebP asset. The selected subtrees render with the original SVG definitions so their patterns, gradients, embedded images, and clip paths remain available.

The exported components are wired into `PixArtwork` through `compose/PixArtworkResources.kt`. `compose/PixScreens.kt` now supports screen-specific header action and credit-lightning art and displays the source Agent robot image. The screen geometry, positions, dimensions, text values, and visual styling were not changed by this binding.

For an Android app, copy the generated WebP files into `app/src/main/res/drawable-nodpi/` and call `rememberPixArtwork()`. This repository has no Gradle app module, so resource loading and app compilation must be verified in the consuming app. See `COMPOSE_IMPLEMENTATION.md`.

Special case: the inactive Mine navigation icon's inline mask renders differently in CairoSVG than in the original full-frame render. The exporter omits that mask reference only in the exported icon copy so the exported icon matches the visible source-frame outline. The original `pix.svg` is not modified.


## Accuracy boundary

The SVG and CSS exports are distinct inputs. The SVG root viewBox and the CSS frame dimensions do not share the same coordinate width. Treat each file's own coordinate system as authoritative and use the verified SVG frame origins for viewport cropping.

The inspector is not a renderer: it does not calculate path/text bounds, stroke-expanded bounds, CSS-computed appearance, or final filter/mask/clip output. Its group bounds are partial estimates only. Structural mapping and successful rasterization are not proof of pixel-perfect validation.

Do not replace the source SVG/CSS or silently approximate missing artwork. Do not claim visual parity until the original artwork has been bound and screenshots have been compared against the source frames.
