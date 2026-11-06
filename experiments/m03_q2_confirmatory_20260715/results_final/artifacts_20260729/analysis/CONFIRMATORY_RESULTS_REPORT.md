# Confirmatory Evidence Report

Primary models passing: 0 / 4.
Supporting criteria passing: 1 / 4.
Q2 publication evidence gate: FAIL.

## Primary sketch RG

| Model | Mean RG | 99% CI | Holm p | Pass |
|---|---:|---:|---:|:---:|
| triposr | 0.0089 | [0.0001, 0.0180] | 0.0377592 | no |
| instantmesh | 0.0222 | [-0.0124, 0.0583] | 0.308274 | no |
| hunyuan21 | -0.0041 | [-0.0114, 0.0030] | 0.308274 | no |
| trellis | -0.0091 | [-0.0256, 0.0071] | 0.308274 | no |

## Supporting criteria

- both_seed_directions: fail (1 stochastic models positive in both seeds)
- both_view_directions: fail (0 models positive at both additional views)
- positive_severity_slope: fail (1 models with positive sketch slope)
- model_style_metric_interaction: pass (primary Holm p=1.02835e-08)
