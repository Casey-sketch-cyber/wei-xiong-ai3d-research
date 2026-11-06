# M03 Figure 1 AI prompt and assets

## Recommended upload set

Use the files in:

`required_primary_sample_white_bg/`

Upload all 13 images:

- `gt_iso.png`
- `input_photo.png`
- `input_edge.png`
- `input_flat_colour.png`
- `input_low_detail.png`
- `input_sketch.png`
- `input_watercolour.png`
- `render_photo.png`
- `render_edge.png`
- `render_flat_colour.png`
- `render_low_detail.png`
- `render_sketch.png`
- `render_watercolour.png`

Do not upload `data_panels/aggregate_main_results.png` for Figure 1. That aggregate result panel should be used later as a separate Figure 2, not inside the framework figure.

Optional backup sample:

- `optional_secondary_sample/`

Use this only if the AI layout tool needs a more dramatic failure case. Do not mix the primary and secondary samples in the same row unless the layout explicitly marks them as different objects.

Note: `required_primary_sample/` contains the original transparent-background PNGs. Some tools flatten the transparent pixels as black, white, or grey depending on hidden RGB values. For AI layout generation, prefer `required_primary_sample_white_bg/`, which composites the same evidence images onto a consistent white background.

## Prompt to copy into the AI figure tool

Create a publication-quality Figure 1 for a computational design and image-to-3D reconstruction paper.

Paper title:

`Style-induced volumetric bias in image-to-3D reconstruction: A controlled benchmark on artistic input transformations`

Scientific message:

The same real 3D object is represented as one photo input and five matched artistic inputs: Edge, Flat colour, Low detail, Sketch, and Watercolour. Each input is processed by the same TripoSR image-to-3D reconstruction pipeline. The resulting meshes show that non-photographic artistic inputs can change reconstructed geometry and shrink usable volume, even when point-based metrics improve.

Use the attached images as fixed scientific evidence. Do not repaint, redraw, hallucinate, replace, stylise, crop aggressively, or alter the object shapes, input images, mesh renders, chart content, labels, or metric values. Your task is only to arrange the provided assets into a clean journal-quality figure.

Required figure layout:

Panel A: Paired input construction.
Show one row of tiles in this order:

1. GT object
2. Photo
3. Edge
4. Flat colour
5. Low detail
6. Sketch
7. Watercolour

Use the exact attached input images for these tiles. Label the panel `A` and label the row `Matched inputs from the same object`.

Panel B: Controlled reconstruction pipeline.
Place a compact central block or arrow between the input row and output row. Label it exactly:

`Same TripoSR pipeline`

Add small text under it:

`same object, same view, same model`

Do not add decorative icons. A simple thin arrow or clean pipeline block is enough.

Panel C: Reconstructed mesh outputs.
Show one row of output mesh render tiles in this order:

1. Photo
2. Edge
3. Flat colour
4. Low detail
5. Sketch
6. Watercolour

Use the exact attached `render_*.png` files. Label the panel `C` and label the row `TripoSR mesh renders`.

Panel D: Evaluation readout, schematic only.
Do not include the aggregate result chart. Instead, add a small clean schematic box labelled:

`Paired diagnostics`

Inside the box, list only these metric names:

`Volume ratio`
`z-extent ratio`
`Chamfer change`
`F-score change`

This panel should indicate what is measured after reconstruction, not show the final experimental results. The aggregate result chart will be a separate Figure 2.

Optional local case callout for the primary sample:

`Sketch case: volume ratio = 0.062, F-score change = +0.320`

Style requirements:

- Clean Nature / JCDE / SIGGRAPH-style scientific figure.
- White background.
- Thin light-grey separators.
- Precise alignment, equal tile sizes, consistent spacing.
- Professional sans-serif typography.
- Use British spelling exactly: `Flat colour`, `Watercolour`, `stylised`.
- Do not use a decorative gradient, dramatic lighting, shadows, 3D icons, cartoon arrows, or marketing-style design.
- Do not put a large title inside the figure.
- Do not include aggregate plots, bar charts, scatter plots, heatmaps, or final result panels in Figure 1.
- Keep labels short and legible.
- Aspect ratio around 2:1 or 16:9.
- Export high-resolution PNG. If possible, also export editable PDF or SVG.

Integrity constraints:

- The input tiles and mesh render tiles are experimental evidence.
- They must remain recognisable and traceable to the uploaded files.
- The AI may improve layout, spacing, panel letters, arrows, separators, and captions.
- The AI must not invent new images, new objects, new numbers, or new charts.
- If exact image preservation is impossible, create only a blank layout template with labelled placeholders and do not fabricate the experiment images.

## Chinese note for the user

这张图的目标不是让 AI 重新画实验结果，而是让 AI 帮我们做论文级排版。最理想的输出是：AI 保留所有上传的真实输入图和 render 图，只负责对齐、留白、箭头、panel label 和整体视觉风格。

如果你用的 AI 工具会把上传图片重新生成、导致 object 或 mesh 变形，那就让它只生成空白版式模板。生成后发我，我再把真实实验图严谨地嵌回去。
