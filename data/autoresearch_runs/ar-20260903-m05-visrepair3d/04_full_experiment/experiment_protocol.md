# RouteRevealBench formal experiment protocol

Protocol version: v2, 2026-09-04 (Asia/Shanghai)

Version 1 used seeds 3000-3019 directly. It is retained as a failed benchmark
build because two declared corruption strata were not constructable. Version 2
changes only case construction: it freezes the first 20 ascending candidate
seeds that pass repair-blind constructability screening. No repair result is
computed or consulted during this screening.

## Scope

This experiment tests geometric compliance with signed, route-indexed visibility
schedules. It does not measure aesthetic quality, curatorial quality, or human
experience. No human ratings are used.

## Primary procedural split

- candidate seeds begin at 4000 (the pilot used 1000-1002 and failed v1 used
  3000-3019);
- the first 20 layouts for which all 15 corruption strata are constructable;
- three route families and three to five exhibits;
- five corruption types: premature reveal, missed reveal, back-facing exhibit,
  target displacement, and a two-fault compound corruption;
- three corruption severities;
- 300 procedural primary cases in total;
- the intended construction keeps corruption magnitudes outside the repair
  action grid. A post-run implementation audit found eight compound severity-2
  cases in which one screen-translation subfault equals a grid step; the paired
  163-degree yaw subfault remains off-grid, so no complete known inverse is
  available. These cases are retained and separately sensitivity-checked;
- 36 route samples, 3 x 3 front-surface rays, and route-clearance checks at no
  more than 0.18 m spacing along every route segment.

## Independent LLM-authored split

Qwen2.5-7B-Instruct proposes bounded structured layout parameters. Every raw
response is retained. A proposal is accepted only if strict JSON-schema checks,
room bounds, collision checks, continuous route clearance, protected relations,
and derivation of a feasible signed schedule all pass automatically. The split
is a transfer check to model-authored structured proposals, not a language or
aesthetic evaluation.

The balanced formal manifest contains 12 layouts (four per route family and
four per exhibit count), yielding 180 additional transfer cases. The combined
formal run therefore contains 480 primary cases.

## Compared methods

1. no repair;
2. visibility maximization without the hide term;
3. random feasible local search;
4. generic beam search over every movable entity;
5. simulated annealing over the same action set;
6. RevealRepair3D attributed beam search.

All search methods share the same finite translation/yaw action set and a
maximum of 480 objective evaluations. RevealRepair3D differs by first-hit
failure attribution and lexicographic sparse, hard-valid selection.

## Ablations

Every fifth base layout is used for a balanced ablation subset:

- visibility-only objective;
- no sparse edit tie-break;
- no hard-constraint filter;
- target-exhibit edits only;
- partition edits only.

## Primary outcomes

- signed schedule loss and its missed-reveal/leakage components;
- success rate at schedule loss <= 0.005;
- hard-valid repair rate;
- edited-entity count and normalized edit cost;
- objective evaluations and wall-clock runtime.

The `loss <= 0.005` quantity is a tolerance-satisfaction rate and is reported
for every method, including no repair. It is not interpreted alone as evidence
that an edit improved a case; relative loss reduction from the corrupted input
is reported separately.

## Statistical analysis

- paired case-level differences against every baseline;
- 10,000-replicate percentile intervals at both the case level and by
  resampling complete `layout_id` clusters; layout-clustered intervals are
  primary for cross-method claims;
- two-sided Wilcoxon signed-rank tests on nonzero paired loss differences;
- two-sided Wilcoxon tests on per-layout mean paired differences, reported
  alongside the case-level tests;
- exact McNemar tests for discordant success outcomes;
- stratification by corruption, severity, route family, exhibit count, and
  layout source.

## Evidence gate

The formal procedural split passes only if all conditions hold:

- at least 300 primary cases complete;
- RevealRepair3D success rate is at least 0.80;
- median relative loss reduction from the corrupted scene is at least 0.80;
- all returned RevealRepair3D repairs preserve hard constraints;
- median edited-entity count is no more than two;
- the upper 95% layout-clustered paired-bootstrap confidence limit for mean
  loss difference is nonpositive against generic beam search and simulated
  annealing;
- the layout-clustered 95% interval for paired leakage loss difference between
  signed optimization and visibility-only optimization lies below zero.

Passing this gate supports a controlled geometric benchmark claim. It does not
by itself make the study submission-ready; claim, artifact, and robustness
audits remain required.
