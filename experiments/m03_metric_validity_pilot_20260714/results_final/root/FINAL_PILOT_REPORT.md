# M03 A1 final pilot report

## Decision

- Pilot: 30 objects, 3 image-to-3D models, 6 matched input styles.
- Evaluated reconstructions: 900/900 successful.
- Frozen gates passed: 1/4.
- Mechanical decision: **STOP AT 30; do not expand to 100 objects.**

The preregistered cross-model sign-reversal hypothesis was not supported. No model had a style whose 95% object-cluster bootstrap interval simultaneously showed an F-score increase and a voxel-IoU decrease.

## Frozen design

- Models: TripoSR, InstantMesh, and Hunyuan3D 2.1.
- Inputs: photo, edge, flat, low-detail, sketch, and watercolor.
- Pairing: same object, same view, same model; only the input style changes.
- Randomness: InstantMesh and Hunyuan3D 2.1 use seeds 20260714 and 3407; TripoSR is deterministic.
- Ground truth: 30 strictly audited solid meshes reconstructed from complementary GeometricBreaks fragments and linked to the original Google Scanned Objects assets used for rendering.
- Alignment: one global scale and one signed-axis permutation per model, calibrated from the first five photo inputs only. No per-sample scaling or style-informed alignment was used.
- Metrics: 10,000 surface samples, F-score@0.05, Chamfer-L2, normal consistency, 128^3 voxel IoU, solid-volume error, extent error, and topology diagnostics.
- Statistics: 5,000 deterministic object-cluster bootstrap replicates.

## Validation

- Manifest rows: 180 unique object-style pairs.
- TripoSR: 180 records, 30 objects, 6 styles.
- InstantMesh: 360 records, 30 objects, 6 styles, 2 seeds.
- Hunyuan3D 2.1: 360 records, 30 objects, 6 styles, 2 seeds.
- Primary metrics finite: yes.
- Records with more than 1% voxel-grid clipping: 0.
- Evaluation failures: 0.

## Frozen gates

| Gate | Result | Evidence |
|---|---:|---|
| Cross-model primary sign reversal | FAIL | No model/style met CI(delta F-score) > 0 and CI(delta voxel IoU) < 0. |
| Stable model-rank reversal | FAIL | No model pair had significant opposite rankings under F-score and voxel IoU. |
| Medium metric-family-by-style effect | PASS | Sketch: InstantMesh dz=0.789; TripoSR dz=0.647. |
| Seed-direction consistency | FAIL | Hunyuan3D 2.1: 20%; InstantMesh: 60%; both below 80%. |

## Main quantitative pattern

Photo baselines were adequate for all three models. InstantMesh had the strongest mean photo baseline (F-score 0.395, voxel IoU 0.329), followed by Hunyuan3D 2.1 (0.335, 0.298) and TripoSR (0.308, 0.246).

The robust result is degradation rather than a sign-reversal paradox:

- InstantMesh edge: delta F-score -0.246, delta voxel IoU -0.310.
- InstantMesh sketch: delta F-score -0.136, delta voxel IoU -0.276.
- TripoSR sketch: delta F-score -0.027, delta voxel IoU -0.056.
- Hunyuan3D 2.1 edge: delta F-score -0.007, delta voxel IoU -0.079.

Sketch therefore creates a reliable metric-family divergence for InstantMesh and TripoSR: both metrics worsen, but solid occupancy worsens substantially more. This supports a narrower metric-sensitivity or style-robustness claim, not the original claim that a surface metric improves while solid geometry collapses.

## Interpretation boundary

The result does not justify expanding the original hypothesis to 100 objects. A defensible next direction would be a new, separately frozen study of style-specific robustness and the unequal sensitivity of surface and solid metrics, with sketch and edge as the main stressors. The current 30-object pilot should be retained as an honest negative result for the original sign-reversal hypothesis.

## Integrity hashes

- Pilot manifest: `63d036d2cfc8175c11fda3610e14bfc934dc4d95bd2941e6f331e78d40b39ef1`
- Input manifest: `7ce6ee837968d608adee39407a39cc9052a9ced11d658de9af60d5d10de9c263`
- Hunyuan result manifest: `a8543816c2068954d7094a34fe590e11e0c291137f839311be7a276cb2a32980`
- Final evaluation CSV: `d69ff88be0135f1d934f340898d30159d729f86cacb198f7a9722576a5b53eae`
- Frozen gate JSON: `4a48e8f8ffd2f216d7e56c0eddf63153d1a6cafe504ad2d2fa43e6046c606870`
