# Research Guidance File

## Title / Topic

- Working title: Cross-Style Geometry Hallucination in Image-to-3D Generation: A Paired Benchmark with Known 3D Ground Truth
- Target field: TBD
- Target venue or tier: q2_journal
- Technique/method: TBD from selected candidate
- Selected application scenario: TBD

## Core Idea

Modern image-to-3D systems are often evaluated on natural or product-like images, while artistic inputs such as sketches, watercolor, oil painting, flat illustration, anime/toon, and abstract low-detail images can change the visual cues that models treat as geometry. This project builds a paired benchmark from known Objaverse-style 3D objects: the same object is rendered or stylized into multiple 2D input domains while retaining the original 3D ground truth. The study quantifies style-induced geometry hallucination, including backside invention, thickness collapse, topology fragmentation, shape-material entanglement, and view-consistency degradation.

### Mechanism-Level Rationale

The novelty scan found that Art3D and manuscript-to-3D studies partially cover artistic image-to-3D, but they do not provide a controlled cross-style paired benchmark with known 3D ground truth for the same objects. This narrower formulation shifts the contribution from another image-to-3D method to a diagnostic benchmark plus lightweight geometry-preserving mitigation.

## Paper Story

- Opening problem: TBD
- Why existing work is insufficient: derive from supporting evidence and novelty scan.
- Core insight: Modern image-to-3D systems are often evaluated on natural or product-like images, while artistic inputs such as sketches, watercolor, oil painting, flat illustration, anime/toon, and abstract low-detail images can change the visual cues that models treat as geometry. This project builds a paired benchmark from known Objaverse-style 3D objects: the same object is rendered or stylized into multiple 2D input domains while retaining the original 3D ground truth. The study quantifies style-induced geometry hallucination, including backside invention, thickness collapse, topology fragmentation, shape-material entanglement, and view-consistency degradation.
- What evidence should convince the reader: baselines, ablations, robustness checks, and statistical tests.
- Main claim: TBD after pilot experiment.
- Boundary of the claim: must match available datasets and hardware.

## Paper Outline

1. Introduction:
2. Related Work:
3. Method:
4. Experiments and Results:
5. Discussion:
6. Conclusion:

## Experiment Plan

### Datasets

| Dataset | Direct access URL | License/terms | Task role | Size | Labels/targets | Split strategy | Access decision |
|---|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | pending |

### Baselines

- Stable Fast 3D
- TripoSR
- Wonder3D or another available multi-view/image-to-3D baseline
- Photorealistic-input condition as an internal reference

### Proposed Method Variants

- Main method: TBD
- Variant A: resource-scaled variant
- Variant B: ablation-friendly simplified variant

### Metrics

- Primary metric: Relative geometry degradation under artistic style shift, measured against known 3D ground truth
- Secondary metrics: TBD
- Statistical test / confidence reporting: repeated seeds or paired tests where applicable

### Required Ablations

- Style domain ablation
- Object-category ablation
- Style-stripped preprocessing
- Edge-depth assisted preprocessing
- Multi-candidate geometry-proxy reranking

### Runtime / Hardware Budget

- Resource fit: single RTX 5090 feasible
- Notes: The proposed server has one RTX 5090, 90GB RAM, Ubuntu 22.04, PyTorch 2.8, CUDA 12.8, and a 700GB data disk. This is sufficient for pilot and main benchmark runs if the study focuses on inference, rendering, and evaluation rather than training a new image-to-3D foundation model. Use CUDA 12.8+ and avoid older prebuilt CUDA extensions that lack Blackwell support.
- Data policy: public_only

## Expected Results

- Minimum acceptable result: TBD before experiments.
- Strong result: TBD before experiments.
- Failure signal: If paired stylization cannot preserve enough object identity for fair 3D comparison, or if all tested models show trivial total failure across styles without interpretable error modes, the benchmark claim weakens.
- Claim adjustment rule if expectations fail: weaken claims to match evidence; do not alter reported numbers.

## Figure and Table Plan

- Framework/architecture figure: planned after method stabilizes.
- Main result table: planned.
- Ablation table: planned.
- Error or robustness figure: planned if evidence supports it.

## Traceability Checklist

| Requirement | Dataset | Baseline/method/ablation | Metric | Expected result | Planned figure/table | Must appear in paper? |
|---|---|---|---|---|---|---|
| Dataset access check | TBD | dataset | TBD | direct public access or documented exception | dataset table | yes |
| Baseline comparison | TBD | baseline | TBD | sane baseline reproduced | main result table | yes |
| Main method | TBD | method | TBD | improves or explains failure | main result table | yes |
| Ablation | TBD | ablation | TBD | isolates mechanism | ablation table | yes |

## Citation Scope

- Must-cite papers: use supporting papers from radar/wiki first, then verified external search.
- Search keywords: TBD
- Target recency: majority from last 3-5 years unless foundational.
- Minimum reference count: 36 for journal draft, venue-appropriate count for conference draft.

## Constraints and Preferences

- Things the workflow must do: preserve failed experiments and evidence traceability.
- Things the workflow must avoid: hallucinated citations, fabricated numbers, unsupported claims.
