# Figma SVG → Android Compose extraction pipeline

This repository contains a two-screen Figma export:
- `pix.svg`: visual source/export.
- `pix.css`: named layer measurements and styling.
- `pix.kt`: legacy placeholder XML snippets; it is **not** Kotlin Compose.

## Run the extractor

Requires Python 3.10+; no third-party packages are needed.

```bash
python tools/figma_to_compose.py --css pix.css --svg pix.svg --out generated --scale 3
```

The command creates:
- `generated/pix-design-manifest.json`: named CSS sections, raw px values, converted dp values, colors, gradients, borders and typography.
- `generated/PixDesignSpec.kt`: typed Kotlin data describing those measurements.

The default scale is 3 export pixels per Android dp (1080px → 360dp). Change `--scale` if the source frame uses a different density. The source `pix.css` and `pix.svg` are read-only inputs.

## Important accuracy boundary

This is the first deterministic extraction stage, not a claim that arbitrary Figma SVG exports can be converted into production Compose UI with perfect fidelity. CSS gives geometry and styles, while the SVG may contain paths, masks, clipping, gradients, embedded photos and outlined text. Those need to be mapped and validated separately. The generated Kotlin file is a design-spec layer; it does not pretend that a photo or complex vector has become an editable Compose component.

## Recommended next stage

1. Inspect the SVG structure and identify stable layer IDs/names.
2. Map each named SVG group to its matching CSS section.
3. Export each required image/vector asset without altering its crop.
4. Implement Compose composables from the manifest, preserving the 1080×2115 and 1080×2106 coordinate systems.
5. Compare emulator screenshots against the source at the same aspect ratio and fix only measured differences.

Do not replace the source SVG/CSS or silently approximate missing assets.
