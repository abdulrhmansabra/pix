# Exporting original SVG artwork

This stage extracts original embedded image payloads from `pix.svg` and renders two full-frame visual references. It does not infer component names from unnamed SVG groups.

## Run

From the repository root:

```bash
python -m pip install CairoSVG
python tools/export_svg_artwork.py pix.svg --out generated/svg-artwork
```

The output is:

```text
generated/svg-artwork/
  template-browsing.png
  profile.png
  manifest.json
  embedded/
    image0_0_1.jpg
    image1_0_1.png
    ...
```

The frame crop defaults reflect the two 1080px-wide canvases reported in the current SVG inspection: Template browsing at SVG x=1200 and Profile at SVG x=0. Override them with `--template-x` or `--profile-x` only when the source geometry has been rechecked. The SVG viewBox is validated before rendering.

Use `--scale 2` or `--scale 3` for larger reference PNGs. Use `--skip-render` to extract embedded raster payloads without installing CairoSVG.

## What is preserved

- Embedded JPEG/PNG/WebP/GIF/SVG data-URI payloads are written byte-for-byte.
- Each embedded image retains its original SVG element ID, declared dimensions, MIME type, SHA-256, and local `<use>` references.
- Full-frame rendering keeps the source SVG descendants, including their original paths, gradients, patterns, `clipPath` elements, masks, and transforms. The exporter changes only the root viewport and output dimensions for each render.

## Important boundary

The two PNG files are full-screen comparison references, not individual reusable component painters. The files under `embedded/` are original raster sources; some are full-frame image sources reused through SVG `<use>` and clipping. Do not bind them directly to `templatePhotos`, `profilePhotos`, or icon slots without checking the associated `<use>`, clip-path, and transform chain.

This exporter intentionally does not edit `pix.svg`, `pix.css`, `PixScreens.kt`, or the CSS-to-Compose slot map. The next stage is to verify each required component's actual SVG subtree and crop semantics, export that verified artwork, and only then bind it to `PixArtwork`. CairoSVG output also needs a visual comparison; successful rendering alone does not prove pixel parity.


## Component-level export

Once the original pix.svg is available, use the component exporter to create named Painter assets from the verified source tree:

```bash
python -m pip install CairoSVG Pillow
python tools/export_pix_components.py pix.svg --out generated/pix-artwork
```

The exporter creates 25 component crops as PNG plus lossless WebP, and manifest.json. It keeps the complete source defs block when rendering a selected subtree so referenced patterns, gradients, images, masks and clip paths remain available. The manifest records SVG node paths and exact clip path IDs.

The output includes the four template-photo crops, two profile-photo crops, distinct header actions for both screens, separate credit lightning icons, search and settings, navigation icons, profile tabs, promotional art, usage sparkle, and the source Agent robot.

For Android, copy only the .webp files to app/src/main/res/drawable-nodpi and preserve their filenames. Use compose/PixArtworkResources.kt to load them into PixArtwork. See COMPOSE_IMPLEMENTATION.md for the R namespace note and the call sites.

The inactive Mine icon is a special case: its inline SVG mask is interpreted differently by CairoSVG than in the original full-frame render. The exporter removes that mask reference only in the exported icon subtree, matching the visible outlined head-and-shoulders icon in the supplied source render. The original SVG remains unchanged.

This export stage validates component source selection and preserves the actual image crops. It does not claim Android screenshot pixel parity; the consuming app still needs to load the resources and compare its rendered screens against the source full-frame references.
