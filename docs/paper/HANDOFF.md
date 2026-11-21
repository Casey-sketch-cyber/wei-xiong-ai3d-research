# Manuscript Handoff & Self-Review (v3)

Non-manuscript tracking document moved out of `docs/paper/draft-v3.md` per Claude's PR #19 review.

## 1. Summary of v2 → v3 Revisions (PR #19 Checklist)

| # | PR #19 Review Requirement | Action Taken in `draft-v3.md` |
| --- | --- | --- |
| 1 | Remove causal overclaim ("once controlled, ordering is identical") | Replaced throughout Abstract, Contribution 4, §4.1, §6, and Figure 1 caption with non-causal framing: *"Under the controlled protocol, the ordering was identical …; the three choices changed error magnitudes and the scored sample but did not reverse the ordering in our tests."* |
| 2 | Lead §4.2, Abstract, and Contribution 1 with full 60-work Cleveland comparison (`docs/NATIVE_APERTURE.md`) | Promoted full 60-work data (59.54% missed 1% crack pixels; PowerPaint 0.1055 → 0.0583, −0.0471 [−0.0589, −0.0360] on 40 paired complete works; availability 300/360 → 281/360; SDXL +0.0008 overall with opposite 1% vs. 5% shifts) into Abstract, Contribution 1, §4.2, and Table 3; moved 16-work pilot table to `docs/paper/SUPPLEMENT.md` (Supplementary Table S1) and retained as supporting text. |
| 3 | Compress Abstract to ≤ 250 words with at most 5–6 numbers | Abstract compressed to 235 words with exactly 6 quantitative figures (`120`, `59.5%`, `45%`, `0.0725`, `21.9%`, `2.8%`). |
| 4 | Move Methods implementation minutiae to Supplementary Information | Moved MAT `noise_const` details, AIC IIIF redirect/candidate tallies, CMA wooden door exclusion & crop coordinates, SHA-256 digests, checkpoint revision hashes, FLUX.1 Fill pre-screening, and Euler `t = 901` / `0.118` derivation into `docs/paper/SUPPLEMENT.md`. |
| 5 | Unify ordering notation as `LaMa ≈ MAT < PowerPaint v1 < SDXL` | Standardized every ordering statement across Abstract, Introduction, §4.1, §4.4, §4.5, §6, and Figure 1 caption; zero occurrences of `LaMa < MAT`. |
| 6 | Remove §4.2 "near-black pixels" paragraph | Deleted the legacy hypothesis paragraph from §4.2. |
| 7 | Update Figure 1 to the new PowerPoint teaser (`FIGURE_SPEC.md`) and renumber Figures 1–6 | Rewrote Introduction references and captions for Figure 1 (teaser, `figure-1-teaser.pptx`), Figure 2 (pipeline, `figure-2-pipeline.pptx`), Figure 3 (examples), Figure 4 (latent coverage), Figure 5 (condition MAE), and Figure 6 (PowerPaint availability). *(Note: if the target journal enforces strict sequential first-mention numbering, swap Figures 5 and 6 or Sections 4.4 and 4.5 during final layout.)* |
| 8 | Move Appendix A handoff out of manuscript | Moved to this file (`docs/paper/HANDOFF.md`); `draft-v3.md` ends cleanly after `## References`. |
| 9 | Note code-provenance logging in §3.1 | Added explicit sentence in §3.1 noting that starting with the full-cohort Cleveland original-mask comparison, every run sidecar recorded Git commit hash, cleanliness, diff digest, and Python source hash (`docs/RUN_PROVENANCE.md`). |

---

## 2. Citation and Figure Verification Status

- **Citations**: All 51 active citation keys in `docs/paper/draft-v3.md` resolve against `literature/papers.csv` (preserving Codex's PR #19 verified bibliography, including `@shamsolmoali2025tdpaint`, `@diffuserssdxl0352`, `@diffusers8450`, and non-peer-reviewed status for `@controlled300`).
- **Read-only drafts**: Neither `docs/PAPER_DRAFT.md` (v1) nor `docs/paper/draft-v2.md` (v2) was modified.
- **Figures**: Captions align with `docs/paper/FIGURE_SPEC.md` (Figures 1–6). PowerPoint teaser (`figure-1-teaser.pptx`), pipeline (`figure-2-pipeline.pptx`), and restyled data plots (Figures 3–6) are pending Codex generation and Claude visual polish.

---

## 3. Claim–Evidence Map (`paperwrite` §11)

| Claim | Evidence | Status |
| --- | --- | --- |
| Under the controlled protocol, `LaMa ≈ MAT < PowerPaint v1 < SDXL` holds identically across Cleveland and Chicago without reversal by the three protocol choices | Table 1, Table 2 (`docs/NATIVE_MAIN.md`, `docs/AIC_REPLICATION.md`, `docs/NATIVE_APERTURE.md`) | Supported |
| MAT and LaMa are practically equivalent within 0.01 MAE and 0.02 LPIPS | Table 2: +0.0022 [0.0015, 0.0030] / +0.0102 [0.0070, 0.0135] (CMA); +0.0032 [0.0023, 0.0041] / +0.0088 [0.0066, 0.0110] (AIC) | Supported |
| Default 8× latent downsampling misses 59.54% of 1% crack and 52.93% of 1% flake pixels across 60 Cleveland works; grid alignment reduces PowerPaint MAE by 44.7% (0.1055 → 0.0583) while lowering availability (300/360 → 281/360) and leaving SDXL overall MAE near zero (+0.0008) due to opposite 1% vs. 5% shifts | Table 3 (`docs/NATIVE_APERTURE.md`), corroborated by Supplementary Table S1 (`docs/LATENT_ALIGNMENT.md`) | Supported |
| At `strength = 0.99`, hole prefill color alone shifts SDXL MAE by 0.0532–0.0725 and reverses luminance bias | Table 4 (`docs/SDXL_PREFILL.md`, `docs/OFFICIAL_INFERENCE.md`) | Supported |
| Ring-color `0.99 / 8 / 20` cuts Cleveland 60-work SDXL MAE from 0.3015 to 0.1114, leaving +0.0789 gap vs. LaMa | §4.3 (`docs/NATIVE_REVIEW.md`) | Supported (Cleveland cohort) |
| PowerPaint safety filtering withholds 21.9% in Cleveland vs. 2.8% in Chicago; replayed Cleveland subset had higher mean MAE gap (+0.0369 vs. +0.0266) while mixed-cohort ranking remained unchanged | Table 5 (`docs/NATIVE_REVIEW.md`, `docs/AIC_REPLICATION.md`) | Supported |
| `LaMa ≈ MAT < PowerPaint v1 < SDXL` holds across all 6 damage conditions and all 4 medium/support strata, while between-group gap magnitudes vary across collections | Table 6, Table 7 (`docs/NATIVE_MAIN.md`, `docs/AIC_REPLICATION.md`) | Supported |

---

## 4. Adversarial Self-Review (`paperwrite` §9)

1. **Contribution**: *Pass.* Quantifies three protocol sensitivities at full cohort scale (60 Cleveland works for mask alignment; two museums / 120 works for main comparison and safety coverage) with exact mechanism precedents cited (`@shamsolmoali2025tdpaint`, `@diffusers8450`, `@diffuserssdxl0352`) and zero novelty overclaims.
2. **Clarity**: *Pass.* Abstract compressed to ≤ 250 words and 6 numbers; Methods streamlined by moving low-level implementation and screening details to `docs/paper/SUPPLEMENT.md`; ordering notation unified as `LaMa ≈ MAT < PowerPaint v1 < SDXL`; legacy near-black paragraph removed.
3. **Strength of results**: *Pass.* Full 60-work original-mask comparison replaces the 16-work pilot as primary evidence in §4.2 and reveals the accuracy–availability tradeoff (300/360 → 281/360) and SDXL condition-level cancellation (+0.0008 overall).
4. **Completeness**: *Ready for Codex verification & Claude review.* All 51 citations resolve cleanly; pending Codex number/citation verification on v3 and final figure rendering per `FIGURE_SPEC.md`.
5. **Soundness**: *Pass.* Causal overclaims removed; all five scope boundaries consolidated cleanly in §5.3.
