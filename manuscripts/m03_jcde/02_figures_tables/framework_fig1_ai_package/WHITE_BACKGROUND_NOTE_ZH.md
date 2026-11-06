# Why some backgrounds became black

The original PNG files are not uniformly white-background images. Many of them have transparent pixels. The hidden RGB value under the transparent background differs by source:

- GT/photo/render tiles often have transparent pixels whose hidden RGB is black;
- edge/watercolour tiles often have transparent pixels whose hidden RGB is white;
- flat colour/sketch tiles may use grey hidden RGB values.

When an AI image tool or editor flattens the transparent PNGs, it may use those hidden RGB values, which creates mixed black, white, and grey tile backgrounds.

For Figure 1 layout generation, use:

`required_primary_sample_white_bg/`

This folder contains the same 13 primary sample images composited onto a consistent white background. The compositing only changes the transparent background; it does not change the object geometry or the mesh renders.
