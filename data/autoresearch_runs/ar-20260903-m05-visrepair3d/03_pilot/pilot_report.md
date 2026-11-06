# Preregistered pilot report

Run: `outputs_preregistered_v2`

## Decision

The small feasibility gate passed and authorized a larger benchmark. It does
not constitute paper-level evidence.

## Primary result

- 15 controlled cases: three base scenes x five corruption types x severity 1;
- six methods and 90 result rows, with no missing or duplicate case-method pair;
- RevealRepair3D exact-solution rate: 15/15;
- median relative signed-loss reduction: 1.00;
- missed and leakage components non-worsening: 15/15;
- hard-valid outputs: 15/15;
- median edited-entity count: 1.

Median RevealRepair3D evaluations were 38 for back-facing faults, 75 for each
single translation fault, and 320 for compound faults. On the 12 cases where
generic beam search also reached zero loss, generic beam used a median of 223
evaluations versus 75 for RevealRepair3D. Random search reached zero on ten
cases and was faster in median evaluations on that easy paired subset (50
versus 75), so the pilot does not support a blanket claim that attribution is
always the fastest search strategy.

## Limitations that motivated the formal run

- corruption magnitudes in this pilot were represented in the action set;
- the scenes shared one simple room/route topology;
- only three base seeds and one severity were tested;
- the benchmark used procedural boxes only;
- success on known-inverse corruptions does not establish transfer to unseen
  layouts or perturbed visibility evaluation.

The formal protocol therefore uses held-out layouts, off-grid corruptions,
multiple topologies and severities, an LLM-authored split, ablations, paired
statistics, denser rerendering, route perturbations, and a bounded exact oracle.
