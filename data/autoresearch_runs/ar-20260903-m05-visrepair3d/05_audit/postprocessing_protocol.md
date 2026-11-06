# Formal postprocessing protocol

Frozen before completion of the 480-case primary run on 2026-09-04
(Asia/Shanghai). These analyses do not alter any primary repair result.

## Primary statistical analysis

- input: the complete `outputs_formal_v2/full_results.csv` only;
- success tolerance: signed schedule loss at or below `0.005`;
- 10,000 bootstrap replicates with seed `20260904`;
- case-level percentile intervals retained descriptively;
- `layout_id` cluster bootstrap used for cross-method confidence claims;
- two-sided Wilcoxon tests on case differences and per-layout mean differences;
- Holm adjustment within each reported family of baseline comparisons.

## Measurement robustness

- deterministic subset: `SHA256(case_id) mod 5 == 0`;
- reevaluate the unchanged final repairs with 5 x 5 front-surface rays;
- reevaluate with twice the route sampling density;
- combine dense rays and dense route sampling;
- perturb interior route samples with fixed 5 cm and 10 cm Gaussian noise;
- require at least 0.75 tolerance satisfaction under combined dense sampling,
  at least 0.70 under 10 cm route noise, and 100% hard-valid outputs.

## Restricted exact oracle

- exclude compound corruptions;
- sort eligible case IDs by SHA-256 and retain the first 48;
- enumerate no-op plus every single edit in the shared formal action set;
- report loss matches for all cases and loss-plus-cost matches where the main
  method returned no more than one edited entity;
- make no global optimality claim beyond this enumerated scope.

## Stochastic-baseline sensitivity

- select the first SHA-256-ranked case in every
  `source x corruption x severity` stratum (30 cases expected);
- rerun random feasible search and simulated annealing with five fixed,
  previously declared seed offsets: `1013, 2027, 3041, 4051, 5059`;
- preserve the primary evaluation budget of 480 per run;
- report every repeat and the best of five for each baseline;
- keep the deterministic RevealRepair3D result fixed for comparison.

## Failure analysis and visualization

- retain every case above the fixed `0.005` tolerance;
- stratify failures by source, corruption, and severity;
- report budget exhaustion and whether generic beam or annealing is better;
- select representative successful examples by declared corruption type and
  largest no-repair loss, without manual image cherry-picking.
