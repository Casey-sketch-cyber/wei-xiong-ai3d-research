# RevealRepair3D method specification

## Working title

**RevealRepair3D: Sparse Counterfactual Repair of Route-Conditioned Visibility
Schedules in AI-Generated 3D Exhibitions**

## Inputs

- room polygon and fixed visitor route sampled at eye height;
- existing 3D layout represented by exhibits, partitions, and protected props;
- per-exhibit front direction and surface samples;
- signed schedule over route samples: `hide`, `show`, or `free`;
- hard constraints and optional text-derived relations to preserve.

## Automatic measurements

- visible front-surface fraction per exhibit and route sample;
- missed-reveal loss, premature-reveal leakage, profile error, and focal-window
  interval IoU;
- first valid reveal index and reveal-order violations;
- number of edited entities, translation distance, yaw change, and total sparse
  edit cost;
- collision, route clearance/connectivity, room bounds, and relation retention;
- ray evaluations, objective evaluations, and wall-clock time.

## Repair algorithm

1. Ray cast from each route sample to stratified samples on exhibit front
   surfaces.
2. For each failed show ray, record the first blocking entity; for each failed
   hide sample, record direct exposure and candidate shielding partitions.
3. Rank implicated entities by weighted violation contribution.
4. Generate finite local translations/yaw changes for only the target exhibit,
   first-hit blockers, and eligible partitions.
5. Search candidates lexicographically: hard feasibility first, signed schedule
   loss second, sparse edit cost third.
6. Recompute the full scene after every accepted edit and emit a repair
   certificate containing before/after metrics, actions, and constraint checks.

## Baselines

- no repair;
- visibility maximization only (negative control);
- random feasible local search;
- generic beam search over all movable entities without blocker attribution;
- simulated annealing over the same action set and evaluation budget;
- tiny-scene exhaustive oracle for optimality-gap checks.

## Benchmark

`RouteRevealBench` starts from valid gallery layouts and generates five
controlled corruptions with known inverses whose complete inverse sequences
are absent from the repair search grid:

- premature reveal;
- missed reveal induced by screen displacement;
- back-facing exhibit;
- target displacement;
- compound two-fault corruption.

The formal run will stratify by room shape, route family, exhibit count,
occluder count, corruption type, severity, and random seed. A second split will
use open-source LLM-generated structured layouts, then apply the same objective
checks and controlled corruptions.

## Pilot pass criteria

- at least 80% relative reduction in signed schedule loss on repairable cases;
- both missed-reveal and leakage components improve;
- 100% hard-constraint preservation;
- median edited-entity count no more than 2;
- attributed search reaches matched satisfaction with fewer objective
  evaluations than generic beam search and simulated annealing;
- all results reproduce from a fresh isolated environment and fixed seed.
