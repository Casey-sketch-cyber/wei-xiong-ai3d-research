# M05: RevealRepair3D

Run ID: `ar-20260903-m05-visrepair3d`

## Working question

Can a post-hoc, training-free optimizer sparsely repair violations of signed,
route-conditioned exhibit visibility schedules using only local translations
and yaw changes, while preserving collision-free navigation and protected
spatial relations?

## Evidence gates

1. Novelty gate: no directly overlapping method is found after direct,
   mechanism, application, and adjacent-community searches; the surviving
   claim must be narrower than generic 3D layout refinement.
2. Pilot gate: compared with the unchanged corrupted layout, the method must
   reduce both missed-reveal and premature-reveal loss, preserve every hard
   constraint, and use a bounded number of edits.
3. Full-experiment gate: the advantage must hold across scene seeds, corruption
   types, and at least three optimization baselines with paired uncertainty.

## Current status

**Experimental gate passed on 2026-09-04.** The frozen formal run completed
480/480 cases with no task failures and produced 3,405 method rows. The full
method satisfies the declared loss tolerance in 476/480 cases (99.17%), keeps
all encoded hard constraints valid, and uses a median of one edited entity and
99 objective evaluations. Final claims, deviations, and limitations are in
`05_audit/final_evidence_report.md` and `05_audit/claim_evidence_matrix.md`.

This status means the narrowly framed geometric task is ready for manuscript
drafting. It does not establish human narrative quality, global optimality,
real-museum deployment, or journal acceptance.

## Directory map

- `01_novelty_scan`: query protocol, raw metadata, closest-prior matrix, verdict.
- `02_method`: method specification, objective, algorithm, implementation.
- `03_pilot`: small pre-registered feasibility test.
- `04_full_experiment`: frozen configurations, raw runs, aggregate results.
- `05_audit`: reproducibility, claim-evidence, citation, and artifact checks.
