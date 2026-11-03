# Figma SVG → Android Compose extraction pipeline

This repository contains a two-screen Figma export:
- `pix.svg`: visual source/export.
- `pix.css`: named layer measurements and styling.
- `pix.kt`: legacy placeholder XML snippets; it is **not** Kotlin Compose.

## Current pipeline

### Stage 1 — CSS measurements and design spec
Run:

```bash
python tools/figma_to_compose.py --css pix.css --svg pix.svg --out generated --scale 3
```

The tool creates:
- `generated/pix-design-manifest.json`: named CSS sections, source px values, converted dp values, colors, gradients, borders and typography.
- `generated/PixDesignSpec.kt`: typed Kotlin data describing those measurements.

The default scale is 3 export pixels per Android dp (1080px → 360dp). Change `--scale` if the source frame uses a different density. The source `pix.css` and `pix.svg` are read-only inputs.

### Stage 2 — Compose screen implementation
`compose/PixScreens.kt` now contains:
- `PixTemplateBrowsingScreen`
- `PixProfileScreen`

The screen geometry, layout positions, colors, gradients, borders, radii and text metrics are based on `pix.css`. The 1080px source coordinate system is scaled to a 360dp design width while preserving each frame's aspect ratio.

Use `COMPOSE_IMPLEMENTATION.md` for integration and the required text/artwork inputs. `svg-css-layer-map.json` records the CSS-layer-to-PixArtwork-slot mapping.

## SVG accuracy boundary

The connector could not return the 3.6 MB `pix.svg` body for inspection. Consequently, the actual SVG group IDs, vector paths, photo crops, masks and embedded raster assets have **not** been verified in this implementation. There are no substitute drawings or invented photos: the Compose screens accept the original artwork as `Painter` inputs through `PixArtwork`. A missing painter leaves that specific art slot empty.

Do not treat the CSS labels as proof that the SVG contains identically named groups. Inspect the local SVG and confirm its IDs/labels before binding assets.

## Next validation stage

1. Inspect the SVG locally and map each real group ID/label to the corresponding slot in `PixArtwork`.
2. Export the original photos/vectors while preserving their exact crop, clipping and aspect ratios.
3. Supply the actual strings and exported assets to the two Compose screens.
4. Compare emulator screenshots against the source frames at 360×705dp and 360×702dp.
5. Correct only measured mismatches; do not redesign or change source colors.

Do not replace the source SVG/CSS or silently approximate missing assets.
