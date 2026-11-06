# M03 Q2 confirmatory protocol

Status: frozen before confirmatory object selection, input rendering, or model inference.

## 1. Confirmatory claim

Stylized inputs can produce a model-dependent surface-solid robustness gap in single-image 3D reconstruction: surface F-score may understate the loss of solid occupancy measured by voxel IoU. The confirmatory target is a difference in degradation magnitude, not a sign-reversal paradox.

The original 30-object pilot is the discovery set D30. Its objects and outputs are excluded from all confirmatory tests.

## 2. Confirmatory cohort C120

- Source: public Google Scanned Objects assets mirrored in `WalkerCH/stream3d`.
- Target: 120 objects not used by D30.
- Candidate order: SHA-256 rank of `m03-q2-confirmatory-20260715:<object_name>`.
- Selection is independent of model outputs and stylized-input behavior.
- Candidate processing continues in hash order until 120 strict solid GT objects pass.
- Branded names may remain in the numerical cohort, but publication examples will use neutral objects.

### Solid GT construction

1. Import and concatenate the source GSO triangle geometry while retaining the original textured GLB for input rendering.
2. Normalize the source geometry to a unit maximum extent.
3. Run official ManifoldPlus commit `a0cc6d9817f81efff63b704a2fed53567ea44cbd` with fixed `--depth 8`.
4. Accept the repaired solid only when all conditions hold:
   - watertight, winding-consistent, and a valid positive-volume solid;
   - at most four connected components;
   - surface F-score@0.02 against the normalized source is at least 0.95;
   - bidirectional surface-distance p95 is at most 0.02;
   - symmetric Chamfer-L2 is at most 0.0002;
   - relative extent MAE is at most 0.03.

No threshold may be changed after inspecting model results.

## 3. Models

1. TripoSR, deterministic, official commit `107cefdc244c39106fa830359024f6a2f1c78871`.
2. InstantMesh, official commit `08822c52fdc399b93ea00e4fa9e596344ed52ccc`, seeds 20260715 and 3407.
3. Hunyuan3D 2.1, official commit `82920d643c0dc2f7bfd7255f45f62d386edfe60c`, seeds 20260715 and 3407, 25 steps, octree resolution 384.
4. TRELLIS-image-large, official code commit `442aa1e1afb9014e80681d3bf604e8d728a86ee7`, seeds 20260715 and 3407, mesh output.

Stable Fast 3D is excluded because its official weights require gated access and no authenticated access is available on the experiment server.

## 4. Main inputs

- One canonical orthographic view per C120 object using the frozen D30 camera transform.
- Six matched variants: photo, edge, flat colour, low detail, sketch, and watercolour.
- All variants retain the exact photo alpha mask, object scale, framing, camera, and white background.
- Style transforms are deterministic and generated before inference.

## 5. Prespecified robustness subsets

### V30 view generalization

- The first 30 C120 objects under the frozen hash rank.
- Two additional fixed camera rotations.
- Inputs: photo, edge, and sketch.
- One seed per stochastic model: 20260715.

### S30 severity response

- The same 30 objects as V30 at the canonical view.
- Edge and sketch at low, medium, and high severity.
- Medium equals the main C120 transform.
- The four additional low/high inputs are evaluated with seed 20260715.

## 6. Alignment and metrics

- One global scale and one of 48 signed-axis permutations per model.
- Calibration uses ten D30 photo objects only; C120 is not used for calibration.
- Translation is removed per sample; per-sample scaling is forbidden.
- Surface: Chamfer-L2, F-score@0.05, F-score@0.10, and normal consistency using 10,000 surface samples.
- Solid: voxel IoU at 128^3, solid-volume ratio/error, per-axis extent ratios, and depth error.
- Topology: watertightness, winding consistency, connected components, boundary edges, and non-manifold edges.
- Secondary rendering diagnostics: silhouette IoU and standardized multi-view normal-render similarity.

## 7. Primary estimand and tests

For model m, style s, and object i:

`RG_i,m,s = (F_stylized - F_photo) - (IoU_stylized - IoU_photo)`

Positive RG means solid occupancy degrades more than surface F-score indicates.

Primary test:

- Sketch RG has a two-sided 99% object-cluster bootstrap CI above zero in at least two of four models.
- Holm correction is applied across the four model-specific sketch tests.
- Seeds are averaged within object for the primary effect; seed-specific estimates are also reported.

Secondary tests:

- edge RG;
- model-by-style-by-metric-family interaction;
- absolute surface and solid degradation;
- topology failure-rate changes;
- view-specific RG in V30;
- linear severity trend in S30;
- seed reliability using object-level correlation and sign agreement.

## 8. Power and sample size

Pilot sketch effects were dz=0.647 for TripoSR and dz=0.789 for InstantMesh. The confirmatory calculation shrinks the plausible effect to dz=0.35. With n=120 independent objects and two-sided alpha=0.01, the normal approximation gives approximately 90% power. Repeated styles, views, and seeds do not increase the nominal independent-object sample size.

## 9. Publication evidence gate

The revised Q2 claim is considered supported only when:

1. the primary sketch RG test passes in at least two models; and
2. at least two of the following hold:
   - the supported direction appears in both stochastic seeds where applicable;
   - the RG direction generalizes to both additional V30 views;
   - S30 has a positive severity slope in at least two models;
   - the model-by-style-by-metric-family interaction is significant after correction.

All failed hypotheses, model exceptions, and sensitivity analyses remain in the manuscript.
