# RevealRepair3D final evidence report

Snapshot date: 2026-09-04 (Asia/Shanghai)

## Decision

**The frozen experimental gate passed, and the candidate is ready to enter
manuscript drafting within the claim boundary below.** This decision supports a
paper about an automated geometric repair task and benchmark. It does not
establish human narrative quality, aesthetic preference, deployment readiness,
global optimality, or guaranteed acceptance by any journal.

## Surviving novelty boundary

The broad idea of visibility-aware 3D layout optimization was rejected. The
surviving contribution is the conjunction of:

1. post-hoc repair of an existing AI-generated exhibition layout;
2. a fixed visitor route;
3. signed, exhibit-specific hide/show schedules along that route;
4. first-hit visibility attribution followed by bounded local edits; and
5. hard preservation of collision, route clearance, bounds, ordering, side,
   and protected screen relations.

The formal scan retained 1,421 broad and 922 reveal-specific deduplicated
records from Semantic Scholar, OpenAlex, and Crossref; 331 broad and 439
reveal-specific arXiv records; and 416 citation-snowball records. Exact-phrase
web searches were also recorded. No direct match was found, but this is not
proof that no unpublished, non-indexed, differently worded, or future work
exists. Confidence is medium-high for task-level novelty and medium for
mechanism-level novelty.

The closest boundaries are visibility-aware furniture arrangement, staged
visibility constraints in virtual cinematography, museum/signage visibility
optimization, perception-driven path planning, and recent generated-scene
repair. Accordingly, the paper must not claim the first visibility optimizer,
the first reveal constraint, or the first 3D scene-repair method.

## Frozen study

- Protocol SHA-256:
  `958efa741cdd5ed9e00b439672ef36c9c08a64fcd98152d20a97f25932a97d60`.
- Result-table SHA-256:
  `b2943eb186c220aeb35db3e502292a64a450c29338311c00ca8d09820a5ae864`.
- Layouts: 20 procedurally constructed and 12 accepted Qwen2.5-7B-Instruct
  structured layouts, giving 32 independent layout clusters.
- Cases: 5 corruption types x 3 severities x 32 layouts = 480.
- Primary methods: no repair, unsigned visibility maximization, random feasible
  search, generic beam search, simulated annealing, and RevealRepair3D.
- Ablations: five variants on a deterministic 105-case subset.
- Total result rows: 3,405.
- Visibility estimator: 36 route samples and 3 x 3 front-surface rays in the
  primary run.
- Primary threshold: signed schedule loss no greater than 0.005.
- Inference uses deterministic geometry and search; no human ratings are used.

## Primary results

| Method | Mean signed loss | Tolerance satisfaction | Median edits | Median evaluations | Hard-valid |
|---|---:|---:|---:|---:|---:|
| No repair | 0.131845 | 1.46% | 0 | 1 | 100% |
| Visibility only | 0.053929 | 43.33% | 1 | 393 | 100% |
| Random feasible | 0.022354 | 75.63% | 1 | 410.5 | 100% |
| Generic beam | 0.008586 | 90.63% | 1 | 480 | 100% |
| Simulated annealing | 0.033156 | 23.13% | 6 | 480 | 100% |
| **RevealRepair3D** | **0.000164** | **99.17% (476/480)** | **1** | **99** | **100%** |

For RevealRepair3D, the layout-cluster bootstrap 95% interval is
[0.000085, 0.000263] for mean loss and [98.33%, 99.79%] for tolerance
satisfaction. The exact-zero-loss rate is 90.42%, and the median relative loss
reduction from the corrupted input is 100%.

Paired differences favor RevealRepair3D over generic beam by -0.008422 mean
loss, with a layout-cluster 95% interval of [-0.011586, -0.005350]. It wins 102
cases, ties 378, and loses none on signed loss; it alone satisfies tolerance in
41 paired cases. Among the 435 cases where both satisfy tolerance, its median
evaluation advantage is 196 evaluations, while median edit-cost difference is
zero. These results support attribution efficiency and loss reduction, not a
claim of universally lower edit cost.

## Signed-objective evidence

Unsigned visibility maximization reduces missed-reveal loss but creates large
premature-reveal leakage. RevealRepair3D reduces mean leakage by 0.095897
relative to that negative control; the layout-cluster 95% interval for the
paired difference is [-0.113447, -0.079170]. RevealRepair3D wins 390 cases and
ties 90 on leakage, with no losses. This supports the need for a signed
hide/show objective rather than viewability maximization alone.

## Transfer, failures, and ablations

- Procedural layouts: 298/300 satisfy tolerance (99.33%).
- LLM-generated layouts: 178/180 satisfy tolerance (98.89%).
- Four failures remain: two procedural and two LLM cases, all compound
  corruptions; three are severity 2 and one is severity 3. All four exhaust the
  480-evaluation budget. Generic beam is not better on any; annealing is better
  on two.
- On the matched 105-case ablation subset, the full method satisfies tolerance
  in 97.14% of cases. Targets-only reaches 69.52%, partitions-only 58.10%, and
  removing the hide term 44.76%.
- Removing the hard filter leaves signed loss unchanged on this subset but
  lowers hard-valid output rate to 98.10%, showing that the filter acts as a
  safety constraint rather than a loss-improvement component.
- The no-sparsity variant is outcome-identical on this subset. Therefore the
  current data do not support a causal claim that the cost tie-break improves
  satisfaction or edit count. Sparse output is descriptive: the full method's
  median is one edited entity.

## Robustness and restricted optimality

A SHA-256-selected 103-case subset was re-evaluated under six conditions. The
hard-valid rate remains 100% throughout. Tolerance satisfaction is 98.06% with
5 x 5 surface rays, 96.12% with twice as many route samples, 93.20% with both,
96.12% under 5 cm route noise, and 82.52% under 10 cm route noise. The declared
robustness gate passes.

Exact enumeration of no-op plus every one-action candidate was run on 48
SHA-256-selected non-compound cases. RevealRepair3D returns one edit on 47.
Within those 47 cases, 40 (85.11%) match the restricted oracle in both loss and
cost. This is a one-action-space certificate only; it is not evidence of global
optimality for deeper repairs.

On a fixed 30-stratum subset, random feasible search and annealing were each
rerun five times. RevealRepair3D's fixed result satisfies tolerance on 100%.
Random search satisfies 76.67% across runs and 80.00% under best-of-five
selection; annealing satisfies 24.00% across runs and 63.33% under best-of-five.
Neither baseline is strictly better than RevealRepair3D on any selected case,
even after best-of-five selection.

## Integrity and disclosed deviations

- Remote tests pass: 3/3 core tests and 4/4 formal tests.
- The 480-case replay audit passes geometry, label, hard-validity, corruption,
  known-inverse restoration, uniqueness, and source-stratum balance checks.
- All single-fault corruptions are fully outside the repair grid, and no case
  has a complete known inverse available in that grid.
- Eight compound severity-2 cases contain one 1.8 m screen-shift subfault that
  coincides with a search step; their paired 163-degree yaw subfault remains
  off-grid. These cases are retained. Excluding them post hoc gives 468/472 =
  99.15% tolerance satisfaction and 100% hard-validity, versus 476/480 = 99.17%
  in the full benchmark.
- A first procedural formal run with two unconstructable strata and an initial
  LLM batch with collapsed route diversity are retained as excluded development
  runs. Both exclusions occurred before eligible repair outcomes were used.

## Claim boundary for a manuscript

Supported: RevealRepair3D is an automated, training-free, attributed local
search method that repairs signed route-conditioned visibility schedules more
reliably and with fewer objective evaluations than the tested baselines on
RouteRevealBench, while preserving the encoded hard constraints.

Not supported: universal superiority; human-perceived narrative or aesthetic
quality; global minimum narrative visibility debt; arbitrary mesh-level,
photorealistic, or real-museum generalization; deployment safety; or an
unqualified “first” claim.

The returned edit cost of a successful repair is a feasible upper bound on the
idealized narrative visibility debt. Only the restricted one-action oracle can
certify exact loss-and-cost agreement within its enumerated scope.

## Environment

The formal run used Linux, Python 3.12.3, NumPy 2.1.3, SciPy 1.17.1, and
Matplotlib 3.9.2. The server exposed 14 cgroup CPU cores and an RTX 3090 24 GB;
Qwen layout generation used the model environment, while geometric repair and
evaluation are CPU procedures. Full package versions are retained in
`environment_remote/pip_freeze.txt`.

## Final assessment

The innovation is experimentally feasible and the frozen evidence gate passes.
The strongest paper is a narrowly framed task/benchmark/method paper. A claim
to broad real-world 3D exhibition optimization would still require independent
external layouts, mesh-level occlusion geometry, and preferably prospective
validation; those are recommended extensions, not evidence already obtained.
