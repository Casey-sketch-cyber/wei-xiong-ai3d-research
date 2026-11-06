# Prompt for AI-assisted figure layout

Use the attached real experimental images as fixed scientific evidence. Do not invent, repaint, redraw, or replace the input images, TripoSR mesh renders, object shapes, metric values, or charts. Your task is only to design a clean journal-quality layout around these provided assets.

Create a publication-quality Figure 1 for a computational design / image-to-3D reconstruction paper titled:

`Style-induced volumetric bias in image-to-3D reconstruction: A controlled benchmark on artistic input transformations`

Scientific message:

The same real 3D object is rendered as a photo input and five matched artistic inputs: edge, flat colour, low detail, sketch, and watercolour. The same TripoSR image-to-3D pipeline reconstructs a mesh from each input. Conventional point metrics can improve, but the reconstructed mesh volume can collapse.

Use these real assets:

- `M03_candidate_real_samples_overview.png` as a candidate overview.
- For the recommended dramatic sample, use folder `840d2861eb4441239d14fc7013c57e79/`.
- For a more intuitive object sample, use folder `02f2bd71a28a421c87288b35524df8d0/`.
- Each sample folder contains:
  - `gt/gt_iso.png`
  - `inputs/input_photo.png`
  - `inputs/input_edge.png`
  - `inputs/input_flat.png`
  - `inputs/input_low_detail.png`
  - `inputs/input_sketch.png`
  - `inputs/input_watercolor.png`
  - `triposr_renders/triposr_photo.png`
  - `triposr_renders/triposr_edge.png`
  - `triposr_renders/triposr_flat.png`
  - `triposr_renders/triposr_low_detail.png`
  - `triposr_renders/triposr_sketch.png`
  - `triposr_renders/triposr_watercolor.png`
- Use the real aggregate result panels from:
  - `data_panels/aggregate_main_results.png`
  - `data_panels/aggregate_graphical_abstract.png`

Recommended layout:

Panel A: Real paired input construction.
Show the selected object with a row of tiles:
GT object, photo input, edge, flat colour, low detail, sketch, watercolour.

Panel B: Same reconstruction pipeline.
Place a simple arrow or compact model block labelled `Same TripoSR pipeline` between the input row and output row.

Panel C: TripoSR mesh outputs.
Show the corresponding output mesh render tiles:
photo, edge, flat colour, low detail, sketch, watercolour.
Keep the outputs visually faithful to the provided render images.

Panel D: Diagnostic result.
Use the provided aggregate chart image or redraw the chart only from the supplied values. The message should be:
`Point metrics can improve while usable 3D volume collapses.`

Style requirements:

- Clean Nature / CVPR / SIGGRAPH-style scientific figure.
- White background, thin grey separators, precise alignment, no decorative gradients.
- Use British spelling: `flat colour`, `watercolour`, `stylised`.
- Use labels exactly: `Photo`, `Edge`, `Flat colour`, `Low detail`, `Sketch`, `Watercolour`.
- No fake numerical values.
- No title text saying `Graphical Abstract`.
- No marketing style, no dramatic lighting, no decorative icons.
- Keep typography sharp and publication-ready.
- Aspect ratio around 16:9 or 2:1.
- Export high-resolution PNG and preferably editable vector PDF/SVG if the tool supports it.

Important integrity instruction:

The input tiles and TripoSR output tiles are experimental evidence. They must remain recognisable and traceable to the provided files. The AI may improve spacing, alignment, labels, arrows, and panel composition, but must not alter the scientific content of the images or charts.
