# Representative Case Selection Freeze

Status: frozen before results from InstantMesh, Hunyuan3D 2.1, or TRELLIS are
available.

The selection source is the C120 main-split, object-averaged sketch RG table.
Models are ordered by their mean sketch RG across the 120 objects.

1. Positive-context case P1 comes from the highest-mean model. Its object is
   the one whose RG is closest to that model's empirical 90th percentile.
2. Positive-context case P2 is selected identically from the second-highest
   model, with an object different from P1.
3. Low-context case L1 comes from the lowest-mean model. Its object is the one
   whose RG is closest to that model's empirical 10th percentile and differs
   from P1 and P2.

Ties are broken lexicographically by object ID. The displayed stochastic output
uses seed `20260715`; TripoSR uses its deterministic output (`-1`). Case labels
show object-averaged RG for selection and seed-specific F-score and voxel-IoU
changes for the displayed mesh. The original input images are displayed without
local contrast, geometry, or content edits. Mesh images use the same global
model calibration and fixed isometric renderer for every case.

