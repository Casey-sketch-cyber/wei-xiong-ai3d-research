# Manuscript Handoff & Self-Review (v4 Submission Candidate)

Non-manuscript tracking document for `docs/paper/draft-v4.md` (with `docs/PAPER_DRAFT.md` v1, `docs/paper/draft-v2.md` v2, and `docs/paper/draft-v3.md` v3 preserved read-only).

## 0. v3 → v4 Submission-Candidate Revisions (PR #34 Checklist)

| # | Requirement (PR #23 Codex + PR #34 Claude) | Action Taken in `draft-v4.md` |
| --- | --- | --- |
| 1 | Codex #1: Table 5 & §4.4 replay and equal-work weighting clarity | Updated Table 5 footnote and §4.4 text to state explicitly that each of the 19 affected works replayed only its own withheld conditions (1 to 6 per work; all 6 for *The Trinity*), averaging first within each work across its replayed conditions and then weighting all 19 works equally. |
| 2 | Codex #2: Scope of `0.0725` and `0.1137` | Specified in Abstract and Contribution 2 that `0.0725` is the overall center-masked black-to-ring MAE difference; clarified in §4.3 that `0.1137` is the 16-work condition mean for 5% contiguous losses (not a single case). |
| 3 | Codex #3: Scope §2.1 to tested pipelines and deployment choice | Scoped §2.1 paragraph to the latent diffusion pipelines tested here and explicitly labeled PowerPaint's safety filter as a deployment choice enabled by default. |
| 4 | Claude PR #34: Add submission declarations | Replaced brief `Code and Data Availability` with full `## Declarations`: `Data Availability` (CMA CC0, AIC public-domain 1686px IIIF, deterministic mask/crop code, no raw image redistribution), `Code Availability` (GitHub repo URL, note on pending repository LICENSE file, upstream model checkpoint terms), `Competing Interests`, `Author Contributions` (CRediT template for author completion), and `Declaration of Generative AI and AI-Assisted Technologies` (Claude, Gemini, Codex assisted with code/writing; author reviewed and assumes full responsibility). |
| 5 | Codex PR #36 #1–4: Sync Hopper Fig 1(a) `57.8%` & tighten Declarations | Updated Figure 1(a) single-example missed coverage from `52.9%` to `57.8%` (1,514/2,621 pixels on Edward Hopper's *Lighthouse Village*, main full-size crop, vs. prefill-arm rendition in 1(b); 60-work mean `59.5%` unchanged); separated Data Availability into public museum records, Git repository contents, and server archive (`prepared.json`, manifests, full JSON summaries); updated SDXL license name to `CreativeML Open RAIL++-M License`, specified upstream release artifacts for LaMa/MAT/PowerPaint, tightened Git vs. archive provenance wording, separated NISO CRediT `Investigation` and `Supervision`, and marked author confirmation items cleanly. |

## 1. Summary of Earlier v2 → v3 Round-1 & Round-2 Revisions

### Round 1 (PR #19 Checklist, 9 items)
| # | PR #19 Review Requirement | Action Taken in `draft-v3.md` |
| --- | --- | --- |
| 1 | Remove causal overclaim ("once controlled, ordering is identical") | Replaced throughout Abstract, Contribution 4, §4.1, §6, and Figure 1 caption with non-causal framing (*"Under the controlled protocol, …; these choices altered error magnitudes and the scored sample without reversing the ordering."*). |
| 2 | Lead §4.2, Abstract, and Contribution 1 with full 60-work Cleveland comparison (`docs/NATIVE_APERTURE.md`) | Promoted full 60-work data (59.54% mean missed 1% crack pixels; PowerPaint 0.1055 → 0.0583, −0.0471 [−0.0589, −0.0360] on 40 complete paired works / 240 conditions with safety checker on; availability 300/360 → 281/360; SDXL +0.0008 overall with condition-dependent decreases and increases) into Abstract, Contribution 1, §4.2, and Table 3; moved 16-work pilot table to `docs/paper/SUPPLEMENT.md` (Table S1). |
| 3 | Compress Abstract to ≤ 250 words with few headline numbers | Abstract compressed to 247 words (≤ 250) with 6 headline result metrics and explicit denominators/scopes. |
| 4 | Move Methods implementation minutiae to Supplementary Information | Moved MAT `noise_const` details, AIC IIIF redirect/candidate tallies, CMA wooden door exclusion & crop coordinates, SHA-256 digests, checkpoint revision hashes, FLUX.1 Fill pre-screening, and Euler `t = 901` / `0.118` derivation into `docs/paper/SUPPLEMENT.md`. |
| 5 | Unify ordering notation as `LaMa ≈ MAT < PowerPaint v1 < SDXL` | Standardized across all MAE/LPIPS ordering statements; zero occurrences of `LaMa < MAT`. |
| 6 | Remove §4.2 "near-black pixels" paragraph | Deleted the legacy hypothesis paragraph from §4.2. |
| 7 | Update Figures 1–6 per `FIGURE_SPEC.md` and production `spec.json` | Updated captions for Figures 1–6 to match the final FigGenie 2 × 2 teaser (`fig1/spec.json`), single-column two-row pipeline (`fig2/spec.json`), and restyled data plots (`FIGURES.md`). |
| 8 | Move Appendix A handoff out of manuscript | Moved to this file (`docs/paper/HANDOFF.md`); `draft-v3.md` ends cleanly after `## References`. |
| 9 | Note code-provenance logging in §3.1 | Added explicit sentence in §3.1 referencing `code_provenance` sidecars (`docs/RUN_PROVENANCE.md`). |

### Round 2 (PR #23 Codex 5 Items + Claude 3 Items)
| # | Source & Requirement | Action Taken |
| --- | --- | --- |
| C1 | Codex #1: Scopes/denominators in Abstract, Contributions 1–2, Fig 1 caption, and HANDOFF | Qualified 59.5% as 60-work 1%-crack mean (vs. 52.9% in Fig 1(a) single example); ~45% as 40 complete paired works (240 conditions, safety checker on); Fig 1(b) luminance shifts (−0.085, +0.055, +0.034) as 16 × 6 = 96 conditions illustrated on one 5% broad-loss case; 0.0725 as overall center-masked black-to-ring shift (with 5% contiguous loss reaching 0.1137); corrected SDXL condition summary (1% contiguous loss +0.0269, 5% crack −0.0034 spanning zero) in both `draft-v3.md` and `HANDOFF.md`. |
| C2 | Codex #2: Restrict `≈` to thresholded metrics; avoid context-only attribution; use 40-work common denominator in §4.2 | Restricted `≈` in §4.1 to masked MAE and local LPIPS (reporting point-estimate sequence for pixel-pair `ΔE₀₀` and DISTS); framed expanded-input increases in §4.2 as combined input-protocol effects; replaced mixed 40/60-work comparison with the exact 40-work / 240-condition four-model intersection (original masks: 0.0274, 0.0284, 0.1055, 0.3087; expanded masks: 0.0313, 0.0337, 0.0583, 0.3115). |
| C3 | Codex #3: Table 5 replay denominator & catalog interpretation | Replaced `19 affected works` under `"Complete 6-condition works"` with `—*` and added footnote; kept +0.0369 (79 replayed conditions across 19 works) and +0.0266 (41 complete safety-on works) tied to separate denominators; stated explicitly that whole-artwork catalog subjects cannot identify why the checker flagged individual crops. |
| C4 | Codex #4: Citations & metric wording | Added pinned PowerPaint pipeline source (`@powerpaintv1src`) to `literature/papers.csv` and cited alongside `@diffuserssdxl0352` in §1 and §3.3; distinguished `@diffusers8450` qualitative discussion from our quantitative painting measurements; changed SDXL `0.99/8/20` to "example settings" with 19 effective steps from Diffusers v0.35.2; scoped MAT determinism to our fixed-seed setup; clarified both CIEDE2000 metrics as unsigned distances; clarified MISATO `CLIP@mask` (semantic) vs. `Gradient@edge` (boundary color seams). |
| C5 | Codex #5: Author corrections | Fixed TD-Paint author order (Tsiry Mayet first; Clément Chatelain last) and `bertalmio2000` third author (`Vicent Caselles`) in both `draft-v3.md` and `literature/papers.csv`. |
| E1 | Claude #1: Shorten Title to ≤ 12 words | Shortened to 12 words: *Three Protocol Choices Shape Measured Fidelity of AI Inpainting on Museum Paintings*. |
| E2 | Claude #2: Limit Introduction contributions to 1–2 numbers each | Trimmed all four bullets to 1–2 quantitative figures each, moving CIs and granular denominators to Results. |
| E3 | Claude #3: Tighten Figure 1 caption & align Fig 1–2 with `spec.json` | Rewrote Figure 1 caption (4 compact panel sentences matching `fig1/spec.json` `caption_draft` with exact denominators) and Figure 2 caption (matching `fig2/spec.json` `caption_draft`). |
| E4 | Claude Round-2 #1–3: Replace `preregistered` and bound `invariant` | Replaced all 6 occurrences of `preregistered`/`Preregistering` with `pre-specified` (first occurrence: *"pre-specified protocol, committed to version control before each inference run"*, plus §3.1 heading and consistent hyphenation); revised Abstract final sentence to *"In these cohorts, the best-performing model did not depend on painting medium..."* and §4.5 heading/closing to *"Rankings held across..."*. |

---

## 2. Citation and Figure Verification Status

- **Citations**: All 52 active citation keys in `docs/paper/draft-v3.md` (51 prior keys + `@powerpaintv1src`) resolve against `literature/papers.csv` and match all 52 reference entries 1-to-1.
- **Read-only drafts**: Neither `docs/PAPER_DRAFT.md` (v1) nor `docs/paper/draft-v2.md` (v2) was modified.
- **Figures**: Captions align with `docs/paper/FIGURES.md`, `docs/paper/figures/src/fig1/spec.json`, and `docs/paper/figures/src/fig2/spec.json`. *(Note: Figures 5 and 6 retain the numbering in `FIGURES.md` / `FIGURE_SPEC.md`; if a journal requires strict sequential first-mention order, swap Figures 5 and 6 or Sections 4.4 and 4.5 at final layout.)*

---

## 3. Claim–Evidence Map (`paperwrite` §11)

| Claim | Evidence | Status |
| --- | --- | --- |
| Under the controlled protocol, `LaMa ≈ MAT < PowerPaint v1 < SDXL` holds identically across Cleveland and Chicago for MAE/LPIPS without reversal by the three protocol choices | Table 1, Table 2 (`docs/NATIVE_MAIN.md`, `docs/AIC_REPLICATION.md`, `docs/NATIVE_APERTURE.md`; 40-work common intersection: 0.0274/0.0284/0.1055/0.3087 vs. 0.0313/0.0337/0.0583/0.3115) | Supported |
| MAT and LaMa are practically equivalent within 0.01 MAE and 0.02 LPIPS | Table 2: +0.0022 [0.0015, 0.0030] / +0.0102 [0.0070, 0.0135] (CMA); +0.0032 [0.0023, 0.0041] / +0.0088 [0.0066, 0.0110] (AIC) | Supported |
| Default 8× latent downsampling misses a mean of 59.54% of 1% crack and 52.93% of 1% flake pixels across 60 Cleveland works; grid alignment reduces PowerPaint MAE by 44.7% (0.1055 → 0.0583) on 40 complete paired works (safety checker on) while lowering availability (300/360 → 281/360) and yielding mixed condition-level SDXL shifts (+0.0008 overall: −0.0704 1% crack, −0.0652 1% flake, −0.0034 5% crack, +0.0269 1% loss, +0.0594 5% flake, +0.0574 5% loss) | Table 3 (`docs/NATIVE_APERTURE.md`), corroborated by Supplementary Table S1 (`docs/LATENT_ALIGNMENT.md`) | Supported |
| At SDXL's 0.99 example settings, hole prefill color alone shifts overall MAE by 0.0532 (16-work native) and 0.0725 (60-work center), reaching 0.1137 on 5% contiguous losses, and reverses luminance bias | Table 4 (`docs/SDXL_PREFILL.md`, `docs/OFFICIAL_INFERENCE.md`) | Supported |
| Ring-color `0.99 / 8 / 20` cuts Cleveland 60-work SDXL MAE from 0.3015 to 0.1114, leaving +0.0789 gap vs. LaMa | §4.3 (`docs/NATIVE_REVIEW.md`) | Supported (Cleveland cohort) |
| PowerPaint safety filtering withholds 21.9% in Cleveland vs. 2.8% in Chicago; the 79 replayed Cleveland conditions (19 works) had a higher MAE gap (+0.0369) than the 41 complete safety-on works (+0.0266), while mixed-cohort ranking remained unchanged | Table 5 (`docs/NATIVE_REVIEW.md`, `docs/AIC_REPLICATION.md`) | Supported |
| `LaMa ≈ MAT < PowerPaint v1 < SDXL` holds across all 6 damage conditions and all 4 medium/support strata, while between-group gap magnitudes vary across collections | Table 6, Table 7 (`docs/NATIVE_MAIN.md`, `docs/AIC_REPLICATION.md`) | Supported |

---

## 4. Adversarial Self-Review (`paperwrite` §9)

1. **Contribution**: *Pass.* Quantifies three protocol sensitivities at full cohort scale with exact software/literature precedents (`@shamsolmoali2025tdpaint`, `@diffusers8450`, `@diffuserssdxl0352`, `@powerpaintv1src`) and zero novelty overclaims.
2. **Clarity**: *Pass.* Title tightened to 12 words; Abstract 242 words (≤ 250) with explicit denominators; Introduction contributions streamlined to 1–2 quantitative figures each; Figure 1–2 captions synchronized with FigGenie specs.
3. **Strength of results**: *Pass.* Full 60-work aperture comparison and exact 40-work common-denominator four-model check eliminate mixed-denominator ambiguity.
4. **Completeness**: *Ready for Codex round-2 verification & Claude merge review.* All 52 citation keys and bibliographic records verified; `bertalmio2000` and `shamsolmoali2025tdpaint` corrected in both manuscript and `literature/papers.csv`.
5. **Soundness**: *Pass.* Causal overclaims removed; thresholded `≈` restricted to MAE/LPIPS; context attribution bounded; catalog counts clearly distinguished from checker triggers; all five scope boundaries consolidated in §5.3.
