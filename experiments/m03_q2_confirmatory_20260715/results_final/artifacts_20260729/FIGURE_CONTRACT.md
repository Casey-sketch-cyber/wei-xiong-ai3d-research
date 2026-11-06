# Confirmatory Figure Contract

Backend: Python only (`matplotlib` for quantitative panels; the fixed CUDA
rasterizer for mesh image plates).

## Figure 2: main quantitative result

- Core conclusion: the surface-solid robustness gap is style- and
  model-dependent, and the pre-registered sketch effect can be judged directly
  from four model-specific 99% intervals.
- Archetype: quantitative grid with the sketch forest plot as the hero panel.
- Panel A: model-by-style heat map of object-averaged RG.
- Panel B: sketch RG forest plot with 99% object-cluster bootstrap intervals and
  Holm-adjusted decisions.
- Panel C: separate surface F-score and solid IoU degradation for sketch, so the
  composite RG is auditable.
- Review risk: do not imply that repeated seeds increase `n`; show `n=120`
  objects and state that seeds were averaged within object.

## Figure 3: per-object gap and representative geometry

- Core conclusion: positive aggregate RG is supported by paired object-level
  effects and corresponds to visible solid-geometry loss in representative
  cases rather than being an averaging artifact.
- Archetype: asymmetric mixed-modality figure with a large paired scatter and a
  subordinate image plate.
- Panel A: surface degradation versus solid degradation for sketch, faceted by
  model, with the equality line and selected cases identified.
- Panels B-C: original photo/sketch inputs and standardized GT/photo-output/
  sketch-output mesh renders from the two models with the highest model-level
  sketch RG, using the object nearest each model's 90th RG percentile.
- Panel D: the corresponding image plate for the model with the lowest
  model-level sketch RG, using the object nearest its 10th RG percentile.
- Review risk: selection must be reproducible from source data; labels must show
  object, model, seed, and metric values; no local image enhancement.

## Figure 4: robustness and diagnostic validation

- Core conclusion: the main effect's degree of support across seeds, fixed
  views, severity, and independent render-space diagnostics is visible without
  changing the primary estimand.
- Archetype: quantitative grid with view generalization as the hero panel.
- Panel A: sketch RG at the two fixed additional views.
- Panel B: ordered sketch severity slope.
- Panel C: two-seed correlation and sign agreement for stochastic models.
- Panel D: sketch changes in six-view silhouette IoU and normal-render
  similarity.
- Review risk: label negative or unsupported robustness results explicitly;
  these panels are secondary and must not be presented as confirmatory sample
  size inflation.

## Export and QA

- Double-column target width: 183 mm; white background.
- Sans-serif body text 6.5-7 pt at final size; bold lowercase panel labels 8 pt.
- Low-saturation model colors plus neutral surface/solid colors; no rainbow map
  and no red-green-only encoding.
- Export editable SVG and PDF plus 600-dpi TIFF and 300-dpi PNG preview.
- Every quantitative panel has a traceable CSV, interval definition, object `n`,
  seed handling, and correction method in its caption/source-data notes.
- Open and inspect the PNG, SVG, and PDF at final size before delivery.
