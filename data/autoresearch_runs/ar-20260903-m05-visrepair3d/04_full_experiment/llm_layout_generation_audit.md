# LLM layout generation audit

Model: `Qwen/Qwen2.5-7B-Instruct`

## Exploratory v1 (excluded)

The first completed batch passed per-layout geometric checks but selected the
`serpentine` route family in all 12 of 12 outputs. This mode collapse made the
batch unsuitable as a diversity/transfer split. Its manifest and all raw
responses are retained under `llm_layouts_qwen25_7b_v1_exploratory`; none of
these layouts enter formal statistics.

## Incomplete v2 (excluded)

The first balanced attempt tied requested strata to generation-attempt index.
JSON rejections could therefore skip strata and break exact balance. It was
stopped after 10 raw generations. Raw responses and rejection reasons are
retained under `llm_layouts_qwen25_7b_v2_incomplete`; no formal manifest was
produced and none of these layouts enter formal statistics.

## Balanced v3 (formal)

The corrected sampler ties the next required stratum to accepted-layout count,
so a rejected response retries the same stratum. The final batch contains 12
accepted layouts from 19 raw generations:

- route families: four straight, four arc, four serpentine;
- exhibit counts: four with three, four with four, four with five exhibits;
- all nine route-family/exhibit-count combinations are represented;
- each accepted record links to an immutable raw-response SHA-256 value;
- every accepted layout passed schema, room-bound, collision, continuous-route
  clearance, protected-relation, and feasible-schedule checks.

Only `llm_layouts_qwen25_7b_v3_balanced/llm_layout_manifest.json` is eligible
for the independent formal split.
