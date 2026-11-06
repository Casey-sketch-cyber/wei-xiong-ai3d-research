# Formal experiment files

- `experiment_protocol.md`: frozen hypotheses, splits, outcomes, and gates.
- `formal_benchmark.py`: varied scene generator, off-grid corruptions, methods.
- `screen_procedural_layouts.py`: repair-blind case-constructability screening.
- `generate_llm_layouts.py`: Qwen structured-layout generation and validation.
- `run_full.py`: checkpointed parallel experiment runner.
- `analyze_full.py`: paired bootstrap, nonparametric tests, tables, figures.
- `run_robustness.py`: denser rays/routes and route-noise reevaluation.
- `run_oracle.py`: exact no-op/one-edit enumeration on a deterministic subset.
- `run_stochastic_sensitivity.py`: repeated random/annealing runs on a
  deterministic source-by-corruption-by-severity subset.
- `visualize_cases.py`: top-down repair examples and visibility profiles.
- `analyze_failures.py`: automatic residual-failure stratification.
- `test_formal.py`: generator, corruption, repair, and continuous-clearance tests.

Directories ending in `exploratory`, `incomplete`, or `v1_failed` are retained
negative evidence and must not be merged into the primary tables.
