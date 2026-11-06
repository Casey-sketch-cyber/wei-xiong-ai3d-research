# M03 A1 frozen pilot protocol

Frozen on 2026-07-14 before the complete three-model result was available.

## Research question

For the same solid 3D object, camera, foreground mask, and image-to-3D model,
does changing only the input rendering style systematically separate conventional
surface metrics from solid-geometry and topology metrics?

## Dataset and inputs

- Dataset family: Google Scanned Objects.
- Candidate solid references: complete watertight meshes reconstructed from the
  complementary break and repair fragments in the public GeometricBreaks GSO
  subset. The textured original GSO GLB is used only for input rendering.
- Strict solid-GT admission: watertight, winding consistent, valid volume, at
  most four connected components, surface F-score@0.02 at least 0.95 against
  the textured original, 95th-percentile surface error at most 0.02, and
  Chamfer distance at most 2e-4.
- Eligible objects after broad IP exclusions: 51. Frozen pilot: first 30 under
  the deterministic 20260714 selection rule.
- Inputs per object: photo, edge, flat colour, low detail, sketch, and
  watercolour. All are derived from one orthographic render and share the same
  alpha mask, camera, object scale, and approximately 9% canvas margin.
- Frozen object manifest SHA-256:
  `63d036d2cfc8175c11fda3610e14bfc934dc4d95bd2941e6f331e78d40b39ef1`.
- Frozen 180-input manifest SHA-256:
  `7ce6ee837968d608adee39407a39cc9052a9ced11d658de9af60d5d10de9c263`.

## Models and inference

- TripoSR, official repository commit
  `107cefdc244c39106fa830359024f6a2f1c78871`, marching-cubes resolution 128,
  deterministic, one reconstruction per input.
- InstantMesh, official repository commit
  `08822c52fdc399b93ea00e4fa9e596344ed52ccc`, official
  `instant-mesh-large` configuration, 75 diffusion steps, seeds 20260714 and
  3407.
- Hunyuan3D 2.1, official repository commit
  `82920d643c0dc2f7bfd7255f45f62d386edfe60c`, 25 diffusion steps, octree
  resolution 384, seeds 20260714 and 3407.
- The same seed is reused across objects and styles within each stochastic
  model as a common-random-number paired design.
- Hardware: one NVIDIA GeForce RTX 5090 with 32 GB-class VRAM.

## Alignment and metrics

- No reconstruction is independently rescaled.
- For each model, one global scale and one of 48 signed axis-permutation
  transforms are selected using only the photo outputs of `gso_001` through
  `gso_005` at seed 20260714 when applicable. This transform is then frozen for
  every style and seed from that model.
- Per-sample bounding-box translation is removed as a coordinate nuisance;
  scale variation is preserved.
- Surface metrics: symmetric Chamfer L2, F-score@0.05 and @0.1, normal
  consistency.
- Solid metrics: voxel IoU on a fixed 128-cubed grid spanning [-0.75, 0.75] on
  each axis, solid-volume ratio, absolute solid-volume error, axis-extent ratios,
  and view-depth extent error.
- Topology metrics: watertightness, winding consistency, component count,
  boundary-edge count, and non-manifold-edge count.
- Confidence intervals use 5,000 object-cluster bootstrap replicates. Seeds are
  averaged within object before the primary cross-style test.

## Frozen expansion gates

The pilot expands to 100 objects only if at least two gates pass.

1. Cross-model primary sign reversal: at least two models have at least one
   style for which the 95% bootstrap CI has delta F-score@0.05 above zero and
   delta voxel IoU below zero relative to photo.
2. Stable model-rank reversal: for at least one style and model pair, both the
   F-score difference and voxel-IoU difference have 95% CIs excluding zero and
   their signs are opposite.
3. Medium metric-family by style effect: the same style has Cohen's dz at
   least 0.5 for `delta F-score - delta voxel IoU` in at least two models, with
   median photo F-score at least 0.15 and median photo voxel IoU at least 0.05.
4. Seed consistency: each stochastic model preserves the sign pair of mean
   delta F-score and delta voxel IoU across both seeds for at least 80% of the
   five artistic styles.

If an effect appears only in TripoSR, it is not reported as a cross-model law.
