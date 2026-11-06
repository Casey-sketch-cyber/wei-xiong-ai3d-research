# M05 formal novelty scan

Snapshot date: 2026-09-03 (Asia/Shanghai)

## Executive decision

**Conditional pass after narrowing.** The original M05 proposal, understood as
generic visibility-aware minimal-change repair of a 3D layout, is not novel
enough. Classical furniture arrangement already optimizes visibility together
with accessibility, circulation, collision, and relative arrangement. Recent
work (Roomer and ScenePilot) already performs sparse or local repair of
generated 3D indoor layouts. Virtual-cinematography work already supports a
negative visibility constraint in one scene followed by a positive visibility
constraint in another.

The narrower candidate survives this scan:

> **Sparse counterfactual repair of an existing AI-generated 3D exhibition
> layout to satisfy a fixed visitor route's signed, trajectory-indexed exhibit
> visibility schedule, while preserving hard physical/navigation constraints
> and protected semantic relations.**

No direct match was found in the sources and search families recorded below.
This is not proof that no unpublished, non-indexed, differently worded, or
future work exists. The defensible confidence is **medium-high for task-level
novelty** and **medium for mechanism-level novelty**.

## Search coverage

Five independent passes were retained as machine-readable evidence:

| Pass | Sources | Query families | Raw | Deduplicated | Failures |
|---|---|---:|---:|---:|---:|
| Broad task discovery | Semantic Scholar, OpenAlex, Crossref | 30 | 1,718 | 1,421 | 10 S2 calls; other sources covered the same queries |
| Broad arXiv discovery | arXiv relevance + newest | 12 | 506 | 331 | 0 |
| Reveal-specific discovery | Semantic Scholar, OpenAlex, Crossref | 16 | 978 | 922 | 2 S2 calls; other sources covered the same queries |
| Reveal-specific arXiv discovery | arXiv relevance + newest | 15 | 662 | 439 | 0 |
| Citation snowball | OpenAlex references, citations, related works | 10 seed papers | - | 416 | 0 |

Targeted exact-phrase web searches additionally covered combinations of
`visibility schedule`, `progressive reveal`, `narrative visibility`, `reveal
order`, `serial vision`, `fixed route`, `minimal edit`, and `layout repair`.
Preprints through the snapshot date were included.

## What the scan invalidated

1. **Not novel:** visibility-aware object arrangement. `Make It Home` includes
   viewing frusta, accessibility, collision, door-to-door paths, distances,
   orientations, and relative relations in furniture-layout optimization.
2. **Not novel:** hidden-then-visible constraints by themselves. `Automated
   staging for virtual cinematography` explicitly describes a first framing in
   which a subject is not visible followed by a second in which it is visible.
3. **Not novel:** sparse local repair of generated 3D layouts. `Roomer` binds
   measured violations to implicated objects and commits finite candidate edits
   only after full-scene verification. `ScenePilot` learns grow-and-repair
   trajectories with minimal move/rotate/scale operations.
4. **Not novel:** curatorial sequence diagnostics or visual-perception trends
   along paths. Recent exhibition and landscape work compares planned and
   visibility-driven routes or optimizes paths to quantified perception trends.
5. **Not novel:** museum visibility optimization broadly. Artwork placement,
   digital-twin exhibition optimization, signage optimization, and visual
   exposure analysis all occupy this space.

## Surviving contribution boundary

The paper must present the contribution as the conjunction of all five axes:

1. **Existing-layout repair**, not generation from scratch and not free global
   rearrangement.
2. **Fixed physical visitor route**, not camera/path optimization.
3. **Signed per-exhibit schedule**, penalizing both premature visibility
   (leakage) and insufficient visibility during a focal interval.
4. **Attributed sparse counterfactual edits**, restricted to exhibits,
   partitions, or first-hit blockers implicated by failed rays.
5. **Certified preservation**, rejecting edits that create collision, reduce
   route clearance/connectivity, leave room bounds, or break protected spatial
   relations.

Removing any one of these axes moves the claim into a well-populated prior-art
area. Accordingly, the manuscript must not use broad claims such as “the first
visibility-aware 3D layout optimizer,” “the first narrative visibility
constraint,” or “the first 3D scene repair method.”

## Proposed formalization

For exhibit `i` and route sample `t`, let `s(i,t)` be `+1` (should be visible),
`-1` (should remain hidden), or `0` (unconstrained), and let `v(i,t)` be the
ray-estimated visible fraction of the exhibit's front surface. With on/off
thresholds `tau_on > tau_off`, the signed schedule loss is

`L_schedule = sum w_on max(tau_on - v, 0)^2 + sum w_off max(v - tau_off, 0)^2`.

The sparse edit cost combines number of edited entities, normalized
translation, and normalized yaw change. The idealized **narrative visibility
debt** is the minimum edit cost needed to bring schedule loss below a declared
tolerance while all hard constraints remain satisfied. The implemented search
prioritizes hard feasibility and schedule loss before edit cost, so a returned
successful repair provides only a feasible upper bound on that debt. Exact
claims are limited to the separately enumerated no-op/one-edit oracle subset.
The quantity is a counterfactual geometric diagnostic; it is not a human
preference score.

## Closest-work distinctions

The detailed comparison is in `closest_prior_matrix.csv`. The most important
distinctions are:

- Cinematography solvers can specify visibility across shots, but solve actor
  and camera staging rather than minimally repair an existing exhibition under
  a fixed walked route.
- Perception-driven path optimization modifies the route while preserving the
  environment; the proposed task fixes the route and minimally modifies the
  environment.
- Roomer and ScenePilot repair generated layouts, but their violation sets are
  physical, access, and relation constraints rather than signed route-indexed
  visual narratives.
- Museum placement work optimizes global visibility/intervisibility or route
  alignment, not counterfactual sparse repair with leakage penalties.

## Experiment gate

Proceed to a pilot only if the implementation can demonstrate all of the
following without human ratings:

1. lower signed schedule loss than no repair, random feasible search, generic
   greedy search, and simulated annealing;
2. simultaneous reduction of missed-reveal and premature-reveal violations;
3. zero newly introduced collision, route-clearance, out-of-bounds, or
   protected-relation violations;
4. fewer edited entities and lower geometric edit cost than generic search at
   matched schedule satisfaction;
5. reproducible gains on held-out scene seeds and multiple corruption types;
6. a negative-control result showing that visibility maximization alone causes
   leakage and therefore does not solve the signed task.

Failure on items 2-4 stops the candidate. Passing a tiny pilot authorizes a
larger procedural benchmark, not a paper-level claim by itself.

## Residual risks

- The novelty is a task/mechanism combination, not a wholly new primitive.
  The method therefore needs a strong formal definition, benchmark, and
  ablations rather than relying on application novelty.
- A boxes-only benchmark may be judged synthetic. The full study should add
  open-source LLM-generated layouts and mesh-level rerendering while retaining
  procedural corruptions for ground-truth repairs.
- A single gallery topology is insufficient. Results need varied room shapes,
  routes, exhibit counts, occluder types, corruption severities, and seeds.
- The objective verifies geometric visibility, not aesthetic quality or human
  narrative experience. Claims must remain at that objective level unless a
  separate human study is later added.

## Evidence artifacts

- `discovery_raw.json`, `discovery_deduplicated.json`,
  `discovery_failures.json`
- `arxiv_raw.json`, `arxiv_deduplicated.json`, `arxiv_failures.json`
- `reveal_discovery_raw.json`, `reveal_discovery_deduplicated.json`,
  `reveal_screened_candidates.json`, `reveal_discovery_failures.json`
- `arxiv_reveal_raw.json`, `arxiv_reveal_deduplicated.json`,
  `arxiv_reveal_failures.json`
- `snowball_seeds.json`, `snowball_candidates.json`,
  `snowball_failures.json`
- `papers/` for locally retained official/author PDFs and extracted text
