# Supplementary Information for Manuscript Draft v3

Implementation details moved from Section 3 (Materials and Methods) of `docs/paper/draft-v3.md` to keep the main manuscript concise while preserving full reproducibility.

---

## Supplementary Note S1: Museum Cohort Screening, Exclusions, and Mask Specifications

### Cleveland Museum of Art (CMA)
- One catalog record initially returned as a painting (`cma-121867`) was excluded before model inference after pre-inference catalog verification identified it as a wooden door.
- Within each of the four medium-and-support groups (oil on canvas, oil on wood, watercolor on paper, ink on paper), catalog IDs were deterministically permuted with NumPy PCG64 (seed `20261119`).
- Positions 0–3 in each group (16 works total) overlapped with the earlier native-scale pilot; 15 retained pixel-identical crops, while `cma-173965` was upgraded from an alternate rendition to the museum's full-size download.
- Post-hoc inspection showed that one frozen crop (*The Trinity*, coordinate `(5145, 503)` in the full-size TIFF) had constant black RGB `(0, 0, 0)` across all pixels. It was retained under the frozen cohort rule and checked in an exploratory exclusion sensitivity (`docs/NATIVE_REVIEW.md`).
- Frozen source plan SHA-256: `c2bc7621d3ae660f2336f2b9edba206a2e73838035c5dcd092878e9a8a3128d0`; artwork manifest SHA-256: `528d5d7cdc2fb90db95970f47a216c482fa3ad37ae3d43bfe68d7882faf6a83c`.

### Art Institute of Chicago (AIC)
- Drawn from frozen AIC catalog export SHA-256 `632d9b8796015c577ca54120a5466a8cd916ad24ff522b2650a9ef29573f7892`.
- Eligibility required a public-domain designation, valid primary IIIF image ID, published short edge ≥ 640 px, aspect ratio ≤ 2.8, and verified medium-and-support metadata, yielding 801 oil-on-canvas, 236 oil-on-wood, 97 watercolor-on-paper, and 35 ink-on-paper candidates.
- Within each group, candidates were ordered by `SHA-256("20261121|group|object_id")` (`candidate-order.json` SHA-256 `09f5e80dafe9e3154ba11a32e4128fd8cbebbceb2b7c01c77d1a712a43e67ac3`) and sequentially audited until 15 works from distinct identifiable primary artists were acquired.
- Across 84 audited candidates: 12 were skipped due to duplicate primary artist within the same group, 11 were skipped because requests for the 1686-pixel-wide IIIF JPEG redirected to 843-pixel files, and 1 failed the image-dimension check.
- All 60 acquired Chicago images are official 1686-pixel-wide IIIF JPEGs with zero source image or crop SHA-256 overlap with Cleveland. Frozen plan SHA-256: `5cb6c301a0469e2f5ecf7cc0d99c9b949fd105cea6a188037d748167f4c875af`.

### Procedural Mask Pixel Counts
- On 512 × 512 crops (262,144 pixels), target area fractions of 1% and 5% correspond to 2,621 and 13,107 masked pixels (rounded to the nearest integer pixel).
- Mask SHA-256 digests matched identically across within-group rank positions 0–14 across all four medium-and-support groups and between Cleveland and Chicago.

---

## Supplementary Note S2: Pinned Model Checkpoints, Environments, and Pre-Screening

- **LaMa**: IOPaint TorchScript release (SHA-256 verified), standard 512-pixel inference without iterative refinement.
- **MAT**: IOPaint Places-512 state dictionary (`truncation_psi = 1`). Because the IOPaint-released state dictionary omits `noise_const` and `noise_strength` buffers present in the original `G_ema` release, the explicit decoder noise path was disabled (`docs/OFFICIAL_INFERENCE.md`, `docs/DECISIONS.md`), with deterministic per-condition latent seeding.
- **PowerPaint v1**: Pinned author repository and replacement checkpoints running in an isolated Diffusers 0.27.0 / Transformers 4.40.2 / Accelerate 0.34.2 environment (`docs/ARCHITECTURE.md`).
- **SDXL Inpainting 0.1**: Diffusers 0.35.2, pinned Hugging Face revision `115134f363124c53c7d878647567d04daf26e41e`, 9-channel UNet, EulerDiscreteScheduler, verified FP16 AutoencoderKL (`force_upcast = false`; VAE file SHA-256 `4ad62825e5c8b31eefb77355ba6693785619bf7d669d9b1a6fd9f19dec6d65b3`).
- **FLUX.1 Fill [dev] pre-screening**: Excluded from GPU execution because full BF16 parameter storage alone requires at least 31.43 GiB (exceeding our single 24 GiB RTX 3090 without quantization or CPU offloading) and anonymous downloads of the gated checkpoint returned HTTP 401 (`docs/DECISIONS.md`).

---

## Supplementary Note S3: SDXL Dual-Path Initialization Scaling and Audits

- In Diffusers v0.35.2's `StableDiffusionXLInpaintPipeline`, the `masked_image` conditioning branch zeroes masked pixels in normalized `[-1, 1]` space (corresponding to mid-gray).
- When `strength = 1.0`, the initial latent is sampled from pure Gaussian noise.
- When `strength = 0.99` with 20 requested steps (`CFG = 8.0`), Diffusers executes 19 effective denoising steps starting at timestep `t = 901`, where the EulerDiscreteScheduler noise scale is `σ ≈ 8.391`. The pipeline encodes the entire pre-masked RGB `image` through the VAE to form `z_img`, initializes `z_img + σ·ε`, and divides by `√(1 + σ²)` before the first UNet forward pass—assigning the encoded input latent a weight of `1 / √(1 + σ²) ≈ 0.118` (`docs/OFFICIAL_INFERENCE.md`).
- The 12-case Cleveland SDXL qualitative contact-sheet audit drew case IDs without replacement using NumPy PCG64 seed `20261121`; two sampled cases were re-run with the pinned pipeline and seed to verify pixel-exact reproduction alongside VAE checksum verification (`docs/NATIVE_REVIEW.md`).
- Beginning with the full-cohort Cleveland original-mask comparison (`docs/NATIVE_APERTURE.md`, `docs/RUN_PROVENANCE.md`), each execution recorded `git_head`, `git_dirty`, `git_diff_sha256`, `source_python_sha256`, and `git_state` into per-execution provenance sidecars (`provenance/<model>/<execution_id>.json`).

---

## Supplementary Table S1: 16-Work Native-Scale Pilot Latent-Alignment Summary

For completeness, the earlier 16-work native-scale pilot before-versus-after alignment results (`docs/LATENT_ALIGNMENT.md`) that motivated the full 60-work comparison in Table 3 of the main text:

| Procedural condition | Missed hole pixels (SDXL / PowerPaint) | Stride-8 expanded / original area ratio | PowerPaint MAE change [95% CI] (n) | SDXL MAE change [95% CI] (n = 16) |
| --- | ---: | ---: | ---: | ---: |
| Crack 1% | 55.96% / 56.29% | 2.539 | −0.1252 [−0.1931, −0.0614] (n = 14) | −0.1085 [−0.1498, −0.0703] |
| Crack 5% | 25.20% / 24.67% | 1.594 | +0.0138 [−0.0023, 0.0329] (n = 14) | −0.0587 [−0.0877, −0.0323] |
| Flake 1% | 53.14% / 53.14% | 2.948 | −0.1553 [−0.1999, −0.1132] (n = 15) | −0.0868 [−0.1188, −0.0580] |
| Flake 5% | 25.43% / 25.36% | 1.727 | +0.0037 [−0.0054, 0.0132] (n = 13) | +0.0670 [0.0398, 0.0966] |
| Contiguous loss 1% | 14.05% / 14.29% | 1.386 | −0.0017 [−0.0063, 0.0025] (n = 14) | +0.0062 [−0.0279, 0.0396] |
| Contiguous loss 5% | 6.39% / 6.40% | 1.158 | +0.0054 [0.0013, 0.0096] (n = 14) | +0.0411 [0.0158, 0.0706] |
| **Overall native pilot** | **—** | **—** | **−0.0424 [−0.0617, −0.0251] (0.0974 → 0.0550; n = 12)** | **−0.0233 [−0.0374, −0.0104] (0.2963 → 0.2730; n = 16)** |
