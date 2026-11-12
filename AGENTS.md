# Research handoff working rules

Read CLAUDE.md and handoff/CURRENT_STATE.md before editing this repository.

## Current task: M03 revision after JCDE rejection (2026-11-09)

M03 was rejected by JCDE. The active work is the revision plan in `revision_20261109/`. Start with `revision_20261109/README.md`, then follow `revision_20261109/CODEX_TASKS.md` step by step and log every step in `revision_20261109/DECISIONS.md`. Code for the revision lives in `experiments/m03_revision_20261109/`. The frozen confirmatory results stay read-only; the revision adds a per-sample registration protocol and reports the original protocol alongside it.

Use the current M03 four-model confirmatory evidence rather than superseded discovery-stage claims. Preserve the confirmed author order and correspondence. Keep M02, M03, and M05 scientifically separate.

Use existing protocols, code, numerical summaries, and real figure assets as the source of evidence. Never fabricate data, references, completed human ratings, or experimental validation.

Keep raw data, meshes, weights, environments, caches, and credentials outside Git. Any new remote run must use the correct isolated project root and must not modify unrelated server files.

After edits, run the checks that apply to those edits and document what was actually verified. Treat historical validation reports as dated evidence, not a current rerun.

## Branches and merging

Work on a branch (for the current revision: `revision-20261109`), not on `main`. After each completed stage, push the branch and keep one pull request open from it to `main`. **Do not merge your own work, and do not wait for the human to merge.** Claude reviews the PR (scheduled or on demand): if the stage passes, Claude merges it; if not, Claude leaves a PR comment saying what to change, and you fix it on the same branch before the next stage. After a merge, update the branch from `main` (`git pull origin main`) and keep working on it. Never force-push and never rewrite pushed history. Scientific choices that the revision plan leaves to the author still go to the author.
