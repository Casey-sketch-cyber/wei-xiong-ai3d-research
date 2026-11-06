# M03 JCDE style-informed writing plan

Date: 2026-06-19

## 1. Why this scan was needed

The current M03 draft already has a coherent claim: for the same 3D object, photo input and artistic inputs such as edge, flat colour, low-detail, sketch, and watercolour are fed into the same image-to-3D model, TripoSR, and the resulting meshes show systematic geometry changes. However, the draft is still too close to a numerical benchmark report. JCDE papers in computational design usually make the design object, workflow, visual evidence, and quantitative evidence visible early.

The main correction is therefore not only wording. The paper needs a stronger visual and evidential spine: same object, matched inputs, generated outputs, and metric shifts should appear as a central result figure, not only as text and aggregate plots.

## 2. JCDE sample papers reviewed

| No. | Paper | Pages | Observed structure and figure/table logic | Lesson for M03 |
| --- | --- | ---: | --- | --- |
| 1 | Zhu et al., 2026, part-level 3D editing | 38 | Graphical abstract, nomenclature, highlights, Introduction, Background and related work, framework, evaluation, conclusion, data availability. It introduces a 3D editing problem through design workflow constraints, then shows framework and qualitative/quantitative evaluation. | M03 can use a graphical abstract and a main workflow/result figure. If formulas are used, include a short notation block or define metrics cleanly in Methods. |
| 2 | Shin et al., 2026, design preference learning | 22 | Graphical abstract, highlights, early Figure 1 with the conceptual factors, related-work table, framework, experiments, discussion around design preference use. | M03 should introduce the controlled factors early: object, view, style, model, metric. A first figure should teach the paired design before numbers appear. |
| 3 | Park et al., 2026, generative 3D appearance design survey | 23 | Review article with nomenclature, taxonomy figures, comparative tables, and a design-stage framing around generation, segmentation, and editing. | Related work should connect M03 to appearance/design workflow and generative 3D practice, not only to ML reconstruction metrics. |
| 4 | Xu et al., 2025, DVS-3D | 14 | Introduction, related methods table, Methods, quantitative comparisons, visual comparisons, ablation tables and figures. It uses Objaverse and OmniObject3D, and pairs visual examples with metrics. | M03 should combine Objaverse-style examples with aggregate metrics. A benchmark paper still needs qualitative render panels and robustness/ablation evidence. |
| 5 | Jin et al., 2025, sketch-based modeling | 15 | Abstract starts from sketch as an intuitive design input. Methods begin with an overview, then detailed stages. Results include many visual examples, usability results, and at least one table. | Because M03 includes sketch/watercolour/artistic inputs, it should show real artistic inputs and reconstructed results. A purely numeric argument is too thin for this topic. |
| 6 | Liang et al., 2025, CADCL | 9 | Compact paper: problem, gap, two-stage method, experiments on two datasets, table-heavy results, concise conclusion. | If M03 must stay short, the acceptable compact pattern is still method overview plus visible experimental results plus tables. |
| 7 | Lee et al., 2024, generative architectural visualizations | 20 | Design-workflow problem, AI visualization pipeline, prompt/data table, many generated-image panels, scenario-based demonstrations. | M03 should frame artistic inputs as realistic design/creative inputs, not synthetic nuisances. The style-generation protocol deserves a table or appendix. |
| 8 | Jin et al., 2025, CMLsearch | 21 | System paper with visual system explanation, task scenarios, user study, and quantitative satisfaction/decision metrics. | The discussion should translate the metric paradox into design workflow consequences: what a designer would wrongly trust if only point metrics are reported. |

## 3. Cross-paper patterns found

JCDE papers in this area usually follow this rhythm:

1. Start from a concrete design or engineering workflow, then introduce the computational gap.
2. Put a graphical abstract or early Figure 1 before the reader gets lost in technical details.
3. Use a "problem -> gap -> proposed controlled framework -> evidence -> design implication" logic.
4. Pair qualitative visual evidence with quantitative tables or plots.
5. Use tables to summarize protocols, related methods, or main metric results.
6. Keep discussion tied to design utility, not only algorithmic accuracy.
7. Include data availability, funding, author contributions, competing interests, and other submission declarations.

For M03, this means one framework figure is not enough. The main text should contain at least one real experimental montage and one quantitative result figure, with the robustness result either as a main figure or a compact table plus supplementary figure.

## 4. Revised one-sentence contribution

M03 should be framed as a controlled diagnostic benchmark showing that non-photographic artistic inputs can induce systematic geometric shrinkage in image-to-3D reconstruction, even when conventional point-based metrics appear to improve.

This is stronger and cleaner than claiming a new reconstruction model. The novelty is the paired cross-style evidence and the metric-gap diagnosis for design-oriented image-to-3D workflows.

## 5. Detailed manuscript structure

### Abstract

Use a five-move abstract:

1. Design workflows increasingly use sketches, flat-colour images, edges, and watercolour-like inputs as prompts for image-to-3D tools.
2. Existing evaluations mostly assume photographic inputs or emphasize point-based reconstruction metrics.
3. We build a paired cross-style benchmark where the same Objaverse object, same view, same TripoSR pipeline, and matched photo/artistic inputs are compared.
4. Across 100 curated objects, artistic inputs reduce reconstructed volume and z-extent while several point metrics improve.
5. The result shows why design-oriented image-to-3D evaluation should report volumetric and usability-sensitive diagnostics alongside Chamfer/F-score.

### 1. Introduction

Paragraph plan:

1. Start from computational design practice: designers and artists often begin from sketches, low-detail images, edges, or stylized concept art.
2. Explain why image-to-3D models make this workflow attractive.
3. State the problem: these models are usually benchmarked as if the input is photographic, but design inputs are often non-photographic.
4. State the hypothesis: changing only the input depiction style may systematically bias recovered geometry.
5. State the controlled design: same object, same canonical view, same image-to-3D model, paired photo and artistic variants.
6. Give the main finding: stylized inputs collapse volume/z-extent even when F-score or Chamfer can look better.
7. Contributions:
   - a public, paired cross-style evaluation protocol for image-to-3D reconstruction;
   - evidence of systematic volume shrinkage across five artistic input styles;
   - a metric-gap analysis showing disagreement between point metrics and design usability;
   - a robustness rerun under higher mesh-extraction resolution.

### 2. Related work

Use four subsections:

2.1 Image-to-3D reconstruction and generative 3D priors

Discuss TripoSR, LRM-like models, Zero123-style novel-view generation, DVS-3D-type methods, and Objaverse-style datasets.

2.2 Artistic, sketch, and non-photographic inputs for 3D creation

Connect sketch-based modeling, image-based modeling, concept art, edges, watercolour, and low-detail visual inputs. The point is not that all these systems use TripoSR, but that these input types are natural in design workflows.

2.3 Evaluation metrics for generated 3D assets

Cover Chamfer, F-score, normal consistency, volume, extents, and why point metrics alone can miss geometry usability.

2.4 Controlled style/domain-shift evaluation

Position M03 as a controlled diagnostic benchmark rather than a new generative model.

### 3. Material and methods

Keep the title as `Material and methods`, which matches JCDE style better than only `Methods`.

3.1 Study overview and paired benchmark design

Introduce the object index \(i\), style \(s\), photo input \(p\), input image \(x_{i,s}\), reconstruction model \(f\), and output mesh \(M_{i,s}=f(x_{i,s})\). Refer to Figure 1.

3.2 Object selection and ground-truth rendering

Describe Objaverse object curation, view control, rendered photo input, and ground-truth mesh/render use.

3.3 Matched artistic input generation

Define edge, flat colour, low-detail, sketch, and watercolour. Include the same crop, object, and view constraints. Put full prompts and generation settings in appendix or reproducibility package.

3.4 Reconstruction protocol

Describe TripoSR version, preprocessing, mesh extraction, resolution, GPU/compute, and deterministic settings where available.

3.5 Metrics and statistical analysis

Add compact formulas:

\[
r^V_{i,s}=\frac{V(M_{i,s})+\epsilon}{V(M_{i,p})+\epsilon}
\]

\[
r^Z_{i,s}=\frac{Z(M_{i,s})+\epsilon}{Z(M_{i,p})+\epsilon}
\]

\[
\Delta F_{i,s}=F(M_{i,s},G_i)-F(M_{i,p},G_i)
\]

\[
\Delta CD_{i,s}=CD(M_{i,s},G_i)-CD(M_{i,p},G_i)
\]

Use paired tests and confidence intervals. Define the metric paradox as cases where \(\Delta F_{i,s}>0\) while \(r^V_{i,s}\ll 1\), or where Chamfer improves while volume/extent collapse.

3.6 Reproducibility

List public data source, generated variants, scripts, hardware, and expected runtime/storage.

### 4. Results

4.1 Representative paired examples show style-dependent geometry changes

Use a real montage. This should be the section that answers the reader's first visual question: "What exactly changed?"

4.2 Stylized inputs consistently shrink reconstructed volume

Use the main aggregate plot and Table 2.

4.3 Point metrics can improve while design geometry worsens

Use scatter/case panels linking F-score/Chamfer changes to volume ratios. This is the conceptual core of the paper.

4.4 The effect persists under higher mesh-extraction resolution

Use the robustness rerun. If page pressure is high, keep Table 3 in the main text and move one robustness plot to supplementary material.

### 5. Discussion

5.1 Why artistic inputs may produce smaller meshes

Discuss missing texture cues, sketch abstraction, silhouette emphasis, priors from training data, and single-view ambiguity.

5.2 What this means for computational design workflows

Explain the practical risk: a designer may see a better F-score or lower Chamfer but receive a less usable 3D asset.

5.3 Benchmarking recommendations

Recommend paired evaluation, reporting of volume/extent, visual paired cases, and style-specific diagnostics.

5.4 Limitations and future work

Limit claims to TripoSR and the tested styles. Future work can test Hunyuan3D, texture-aware models, multi-view input, and human design-utility ratings after visual quality improves.

### 6. Conclusion

State the controlled finding, the metric lesson, and the practical benchmark recommendation in one concise closing paragraph.

## 6. Figure and table plan

### Required main figures

Graphical abstract, submission/front-matter asset

Purpose: one-screen story for editors and readers. It should show photo/artistic input changing the mesh geometry and the headline result: volume decreases while point metrics may improve.

Figure 1, paired benchmark and real sample montage

Content:
- one real 3D object;
- its photo input;
- five artistic inputs: edge, flat colour, low-detail, sketch, watercolour;
- TripoSR renders/meshes for photo and each style;
- a small callout showing volume ratio and F-score change for the same object.

This is the most important missing figure. It should use real experimental data, not a purely conceptual AI illustration.

Figure 2, aggregate geometry and metric results

Content:
- volume ratio by style;
- z-extent ratio by style;
- F-score delta by style;
- Chamfer delta or paired metric shift by style.

Recommended layout: four aligned panels with consistent style order and shared color mapping.

Figure 3, metric-paradox case analysis

Content:
- scatter plot of volume ratio versus F-score delta;
- highlighted objects where F-score improves but volume collapses;
- 3-4 corresponding mini visual examples.

This figure gives reviewers the "why the metric is misleading" evidence.

Figure 4, robustness under higher mesh-extraction resolution

Content:
- 30-object rerun at marching-cubes resolution 128;
- compact comparison against main setting;
- optional paired plot for volume and z-extent.

### Optional supplementary figures

Figure S1: style-generation protocol and prompt examples.

Figure S2: object curation overview and excluded cases.

Figure S3: per-object or per-category distribution plots.

Figure S4: additional representative failures and non-failures.

### Required tables

Table 1: benchmark construction and input styles

Columns: component, setting, rationale, reproducibility location.

Table 2: main 100-object results relative to photo input

Keep current values, but align columns with the figure order and include confidence intervals if available.

Table 3: robustness rerun at higher mesh-extraction resolution

Keep compact. Main text can cite the figure or table depending on page pressure.

Table S1: selected example objects

Include object UID, style, volume ratio, F-score delta, and reason for inclusion in figures.

## 7. Writing logic to preserve

The paper should repeatedly return to the same controlled comparison:

Same object. Same view. Same reconstruction model. Different input depiction style.

This gives M03 a clean causal interpretation without overclaiming. The paper should avoid saying "all image-to-3D models fail on artistic input." A safer and stronger claim is: "In this controlled TripoSR benchmark, artistic depiction styles systematically changed output geometry, and point metrics did not fully reflect the design-relevant degradation."

## 8. Skill workflow for the next writing pass

1. Evidence and structure layer: use this JCDE style scan plus the existing M03 experiment artifacts. This layer decides the paper architecture, figure set, and claims.
2. First drafting layer: follow `external/humanizer/SKILL.md` as a prose constraint so the initial paragraphs avoid generic AI-sounding academic filler.
3. Scientific-argument layer: run `external/AI-Research-SKILLs/20-ml-paper-writing/ml-paper-writing/SKILL.md` to enforce the one-sentence contribution, What/Why/So-What logic, figure-first narrative, explicit experiment claims, and citation verification.
4. Figure layer: use `external/nature-skills/skills/nature-figure/SKILL.md`. I recommend the Python backend because the existing M03 analysis and current publication figures are already Python/Matplotlib-oriented.
5. Final compliance layer: return to the JCDE template and checklist, then compile with the full LaTeX/BibTeX cycle.

## 9. Concrete next steps

1. Build Figure 1 from real M03 assets once the user provides or approves the sample images.
2. Regenerate Figure 2 and Figure 3 from the existing metric CSVs with journal-ready styling.
3. Decide whether robustness remains Figure 4 or becomes Table 3 plus supplementary figure.
4. Rewrite `main.tex` using the structure above.
5. Recheck all references, keeping at least 30 verified citations.
6. Compile and audit page count, figure placement, captions, declarations, and JCDE checklist items.

## 10. Immediate decision

The manuscript should not proceed as a text-only or one-framework-figure paper. The JCDE sample scan supports a more visual, evidence-forward structure. For M03, the strongest main-text figure is the real paired montage: one object, photo input, five artistic inputs, corresponding TripoSR outputs, and local metric changes.
