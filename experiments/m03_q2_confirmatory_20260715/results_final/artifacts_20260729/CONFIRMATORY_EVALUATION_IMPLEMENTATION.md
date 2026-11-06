# Confirmatory Evaluation Implementation Freeze

Status: frozen before confirmatory metric computation or statistical testing.

## Calibration records

The single model-level scale and signed-axis permutation are fitted using only
the photo reconstructions of `gso_001` through `gso_010` from discovery set
D30. C120 is not used for calibration. For stochastic models, the D30 seed is
fixed to `20260714`, which is the seed already present for InstantMesh and
Hunyuan3D 2.1 in the completed discovery run. TRELLIS is run on the same ten
images with the same seed. TripoSR is deterministic.

For each calibration object, the scale candidate is the ratio of the largest
ground-truth extent to the largest predicted extent. The model-level scale is
the median of these ten ratios. The signed-axis transform is selected from all
48 axis permutations and sign combinations by the lowest median symmetric
Chamfer-L2 across the ten objects after applying that one model-level scale.
No per-sample scale or non-rigid registration is permitted.

## Metric implementation

Surface metrics use 10,000 area-weighted samples per mesh with deterministic
hash-derived sampling seeds. Solid metrics use filled voxel occupancy on the
frozen `128^3` grid with extent 1.5. Raw-mesh topology metrics are measured
before alignment. Each evaluation record is keyed by model, `job_id`, and
seed; TripoSR uses seed `-1` in the metric table.

## Confirmatory statistics

The primary robustness gap uses `F-score@0.05` and voxel IoU:

`RG = (F_stylized - F_photo) - (IoU_stylized - IoU_photo)`.

For the C120 primary analysis, stochastic seeds are averaged within object
before inference. A two-sided 99% object-cluster bootstrap confidence interval
and two-sided bootstrap p-value are computed independently for sketch RG in
each model. The four p-values are adjusted with Holm's method. The bootstrap
uses seed `20260715` and 50,000 object resamples. Seed-specific effects remain
separate secondary results.

The view analysis pairs each stylized result with the photo result from the
same object, model, seed, and view. The severity analysis uses ordered levels
low=0, medium=1, and high=2 and estimates an object-cluster bootstrap slope.
All exclusions and metric failures are reported rather than silently removed.

For the publication evidence gate, a model passes the primary test only when
its sketch 99% interval is above zero and its four-model Holm-adjusted p-value
is below 0.01. The seed-direction support item requires positive mean sketch RG
in both seeds for at least two stochastic models. The view-direction support
item requires positive mean sketch RG at both fixed additional views for at
least two models. The severity support item requires a positive mean sketch RG
slope for at least two models. The interaction item is the cluster-robust joint
test of all model-by-style terms in object-averaged RG; the F-score@0.05 primary
and F-score@0.10 sensitivity interaction p-values are Holm-adjusted together.
