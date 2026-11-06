# M03/M02 Status Dashboard

Generated UTC: `2026-06-05T06:16:51.178835+00:00`

## Overall

- automatic package status: `pass`
- required checks: 133 / 133
- boundary checks: 7 / 7
- external status: `pending_external_or_human_steps`

## M03

- status: `complete_for_mainline_draft`
- role: main paper direction
- key claim: Style-induced geometry collapse and metric paradox in image-to-3D reconstruction.

## M02

- status: `automatic_experiments_complete_hunyuan_shape_smoke_not_viable_pending_human_steps`
- role: supplement/discussion or future SSCI/AHCI extension
- Hunyuan3D 2.1 shape smoke: 8 / 8 succeeded; texture status `not_run_bpy_unavailable_in_python312_base_env`
- Hunyuan3D 2.1 colorized projection: 8 / 8 succeeded; texture status `not_official_pbr_front_view_vertex_color_projection`
- human evaluation: `pending_human_evaluators`
- ArtEmis/WikiArt authorization: `pending_human_action`

## Completed Automatic Experiments

| experiment | scale | completed outputs | key finding |
|---|---|---:|---|
| M03 main100 | 100 objects x 6 styles | 600 | Style inputs shrink volume/thickness while Chamfer/F-score can improve. |
| M03 res128 robustness | 30 objects x 6 styles | 180 | Volume and z-extent shrinkage persists at higher mesh extraction resolution. |
| M02 proxy | 100 objects x 6 styles renders | 600 | Sketch has strongest affect-proxy drift; geometry and affect degradation differ. |
| M02 EmoArt-5k | 50 paintings | 50 | Painting-to-3D lowers fine emotion and valence proxy consistency. |
| M02 EmoArt-100 robustness | 100 paintings | 100 | The valence drop persists at 100 paintings, strengthening the proxy evidence. |

## Remaining Human Or External Steps

- ArtEmis/WikiArt authorization and formal data use
- Human evaluators filling annotation CSV files

## Entry Points

| purpose | file |
|---|---|
| run_index | `RUN_INDEX-zh.md` |
| completion_audit | `experiment-completion-audit-zh.md` |
| claim_matrix | `paper-claim-evidence-matrix-zh.md` |
| reproducibility | `REPRODUCIBILITY-zh.md` |
| verification | `package_verification/verification_summary.md` |
