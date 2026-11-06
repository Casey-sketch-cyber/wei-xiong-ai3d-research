# Formal objective and algorithm

Let `x` be an existing exhibition layout, `r_t` the fixed visitor-route sample
at index `t`, and `s_it in {-1, 0, +1}` the signed schedule for exhibit `i`.
`+1` denotes a focal reveal, `-1` denotes a required hidden interval, and `0`
is unconstrained. The ray estimator returns the visible fraction `v_it(x)` of a
stratified front-surface sample set.

With `tau_on > tau_off`, the two normalized components are

```text
L_on(x)  = mean_{s_it=+1} [max(tau_on - v_it(x), 0) / tau_on]^2
L_off(x) = mean_{s_it=-1} [max(v_it(x) - tau_off, 0) / (1 - tau_off)]^2
L_sched(x) = 0.5 [L_on(x) + L_off(x)].
```

The final-state edit cost relative to the input layout `x_0` is

```text
C(x; x_0) = ||delta(x, x_0)||_0
          + sum_j ||translation_j||_2 / room_diagonal
          + 0.35 sum_j |yaw_j| / pi.
```

Candidate layouts are ranked lexicographically by

```text
(1[x not in H], L_sched(x), C(x; x_0)),
```

where `H` is the hard-feasible set defined by collision freedom, continuous
route clearance, room bounds, exhibit ordering, route-side relations, and
screen-to-exhibit relations. Thus a lower schedule loss cannot justify an
invalid layout, and equal-loss candidates prefer fewer/smaller edits.

## Failure attribution

For every violated show sample, the evaluator records the first object hit by
each failed camera-to-surface ray. A back-facing test separately assigns the
target exhibit. For a violated hide sample, the target exhibit and its eligible
screen receive exposure-weighted scores. Only the highest-scoring implicated
entities enter the local action expansion. Generic beam search uses the same
action set and budget but expands every movable entity.

## Narrative visibility debt

For tolerance `epsilon`, narrative visibility debt is the counterfactual
quantity

```text
D_epsilon(x_0) = min_x C(x; x_0)
                 subject to L_sched(x) <= epsilon and x in H.
```

The cost of any returned repair with `L_sched(x) <= epsilon` is a feasible
upper bound on this quantity. Because the implemented search prioritizes lower
schedule loss before edit cost, its returned cost is not assumed to minimize
`D_epsilon`. The one-edit oracle experiment reports the subset on which the
returned repair matches exhaustive no-op/one-edit enumeration in both loss and
cost. Narrative visibility debt is a geometric compliance diagnostic, not a
human preference or aesthetic score.

## Attributed repair pseudocode

```text
evaluate the complete input scene
for depth = 1 ... d:
    rank targets, first-hit blockers, and eligible screens by violation score
    expand finite translation/yaw actions only on the top implicated entities
    reject every candidate outside H
    recompute all visibility schedules and protected constraints
    retain the beam with best (schedule loss, final-state edit cost)
    stop if schedule loss reaches zero within numerical tolerance
return final scene, net edit certificate, before/after metrics, and checks
```
