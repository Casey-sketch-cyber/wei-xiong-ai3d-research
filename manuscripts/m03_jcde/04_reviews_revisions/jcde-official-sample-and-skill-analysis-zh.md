# JCDE official sample and skill-informed writing analysis for M03

Date: 2026-06-23

## 1. Current source status

The official JCDE instructions were rechecked from the Oxford Academic author-instructions page on 2026-06-23. Direct command-line PDF download from Oxford Academic was retried for eight JCDE sample papers, but every direct PDF request returned HTTP 403. This matches the earlier download note. The local evidence base therefore has two layers:

- one saved official PDF for `qwag035`, extracted locally and visually inspected page by page;
- an earlier eight-paper JCDE style scan based on official Oxford Academic article/PDF pages and recorded in `06_literature/jcde_style_scan/README-zh.md` and `04_reviews_revisions/jcde-style-informed-writing-plan-zh.md`.

This document does not claim that all eight PDFs were newly downloaded by command line. It treats the eight-paper scan as journal-style calibration and uses the saved `qwag035` PDF as the detailed exemplar.

## 2. JCDE requirements that affect M03

For a JCDE research article, the official instructions describe a typical length of 6,000 to 8,000 words and 20 to 40 references. The local M03 draft is therefore in range based on the earlier PDF audit: about 6,822 words before References and 38 bibliography entries.

The journal also expects the following submission assets and formatting choices:

- Main Document PDF, Graphical Abstract PDF, Highlights DOCX, Checklist DOCX, and a zipped Word or LaTeX source file for initial submission.
- Single-column manuscript, 1.5 line spacing, 12 pt main text, page numbers, and continuous line numbers for review.
- Oxford APA style and UK spelling.
- A single-paragraph abstract without citations or unexplained abbreviations.
- Up to six keywords.
- Figures and tables embedded in the main text, cited in numerical order, sufficiently large and clear.
- Figure references should use `Figure` in full, not `Fig.`.
- Graphical Abstract is mandatory but should be submitted separately. It should not be placed inside the manuscript PDF as an Introduction figure.
- Highlights are mandatory, with three to five bullets and each highlight no more than 15 words or 100 characters.

Implication for M03: the paper length and reference count are already plausible for JCDE, but the figure structure must be corrected. The Graphical Abstract is a separate submission file. The main manuscript should use Figure 1 to explain the controlled benchmark, Figure 2 for aggregate quantitative results, Figure 3 for the metric paradox with representative cases, and Figure 4 for the robustness rerun.

## 3. Detailed reading of qwag035

The saved qwag035 paper is `A diffusion framework based on prompt-driven masks for part-level 3D editing`, JCDE 2026. It is a useful comparator because it sits in the same broad area: generative AI, 3D assets, design workflows, and evaluation.

### 3.1 Structure

The article uses the following visible structure:

1. Front matter with abstract, keywords, and nomenclature.
2. Introduction, starting from 3D modelling applications and workflow inefficiency.
3. Background and related work, including a comparison table.
4. Proposed framework, with a large Figure 1 framework diagram.
5. Performance evaluation, with environment, metrics, ablation, quantitative comparison, qualitative comparison, multi-round editing, and section summary.
6. Conclusions and future work.

The paper is not only a method description. It repeatedly connects the technical pipeline to a 3D editing workflow: local part edits, multi-view consistency, geometry changes, and prompt-guided user control.

### 3.2 Figure and table rhythm

The most important observation is the role separation across figures:

- Figure 1 is a framework figure. It explains the workflow and modules. It does not contain final performance charts.
- Figures 2 to 4 explain internal mechanisms or architecture details.
- Figure 5 is an ablation figure.
- Tables 2 and 3 carry quantitative semantic alignment, efficiency, and resource-consumption evidence.
- Figures 6 to 12 show qualitative editing cases and sequential editing behaviour.

This confirms that M03 should not overload Figure 1 with aggregate results. Figure 1 should show the controlled benchmark: same object, same view, matched inputs, same TripoSR pipeline, output renders, and a compact diagnostic list. Aggregate performance belongs in Figure 2.

### 3.3 Writing logic

qwag035 follows a simple but strong writing chain:

1. A design task is difficult in practice.
2. Existing computational methods solve related tasks but miss a specific requirement.
3. A framework is introduced as a controlled solution to that requirement.
4. The framework is unpacked visually before the metrics appear.
5. Experiments are organised by claim: ablation, quantitative comparison, qualitative comparison, efficiency, and robustness-like multi-step tests.
6. The conclusion returns to the practical 3D editing value, not only the algorithm.

M03 should mirror the claim-by-claim structure without pretending to be a new model paper. Its core chain should be:

1. Design and asset workflows often use non-photographic references.
2. Current image-to-3D evaluation mostly reports point-based surface metrics.
3. A paired benchmark can isolate input depiction style while holding object, view, model, and ground truth fixed.
4. Stylised inputs produce systematic volume shrinkage in TripoSR.
5. Chamfer and F-score can improve at the same time, so point metrics alone can mislead design-oriented evaluation.
6. A higher-resolution rerun reduces the chance that the finding is only a mesh-extraction artefact.

## 4. Eight-paper JCDE style scan: usable lessons

The earlier eight-paper scan remains useful as a calibration set. Its main lessons are:

- JCDE papers in AI and computational design usually begin with a concrete design or engineering workflow, then introduce the computational gap.
- Early figures teach the workflow. They are not decorative. They help the reader understand objects, inputs, processing modules, and outputs before detailed metrics.
- Visual examples and quantitative evidence appear together. A purely numeric benchmark reads too thin for JCDE when the topic is visual or design-facing.
- Tables are used to compress protocols, related work, metric values, or efficiency comparisons.
- Discussion sections translate results into design implications instead of stopping at benchmark scores.
- Limitations are specific and practical: dataset boundaries, model boundaries, user-study gaps, computational cost, and generalisation.

M03 should therefore keep the manuscript as a diagnostic benchmark paper, not a model paper. The text should repeatedly say what is controlled: same object, same view, same reconstruction model, different input depiction style.

## 5. Current M03 readiness

Current strengths:

- Experiments are complete for the main M03 claim: 100 objects, 6 input styles, 600 TripoSR outputs.
- A 30-object `mc-resolution=128` rerun provides robustness evidence.
- The bibliography has 38 entries, within JCDE's 20 to 40 reference range.
- The paper already uses `Material and methods`, which fits JCDE better than only `Methods`.
- Figure 1 has been rebuilt as an editable PowerPoint framework using real M03 assets.

Current gaps:

- The LaTeX manuscript still points to the old Figure 1 and old caption.
- The current Figure 3 is the robustness plot, but under the new plan robustness should become Figure 4.
- A new Figure 3 is needed for the metric paradox, ideally scatter plus two or three representative cases.
- Captions and Results text need to match the final 4-figure structure.
- The paragraph-level logic should be checked after figure insertion, because the reader should see real experimental evidence before extended interpretation.

## 6. Final figure plan

### Figure 1. Paired benchmark and reconstruction pipeline

Role: framework figure.

Panels:

- matched inputs from the same object;
- same TripoSR pipeline;
- TripoSR outputs by input style;
- paired diagnostics list only.

Decision: do not place aggregate statistics in Figure 1. Panel D should list the diagnostic types, not show the final results.

### Figure 2. Main quantitative results

Role: main statistical evidence.

Panels:

- volume ratio by style;
- z-extent ratio by style;
- F-score change by style;
- Chamfer change or combined metric-disagreement summary.

Scientific conclusion: all stylised inputs reduce reconstructed volume, while point metrics can improve.

### Figure 3. Metric paradox and representative cases

Role: conceptual core.

Recommended archetype: asymmetric mixed-modality figure.

Panels:

- hero scatter plot of volume ratio against F-score change;
- highlighted region for cases where F-score improves but volume collapses;
- two or three case strips showing input, photo output, stylised output, and local metric values.

Scientific conclusion: the metric paradox is not abstract. It can be seen in specific meshes.

### Figure 4. Robustness check

Role: validation.

Panels:

- `mc-resolution=128` volume ratio by style;
- z-extent ratio by style;
- compact comparison to the main run if space allows.

Scientific conclusion: the effect persists when mesh extraction resolution increases.

## 7. Skill selection and execution order

The user requested that writing follow `external/humanizer/SKILL.md` first and then `external/AI-Research-SKILLs/20-ml-paper-writing/ml-paper-writing/SKILL.md`. I will follow that order for prose.

### 7.1 Humanizer

Use as a prose constraint, not as a licence to weaken the science.

Tasks:

- remove generic AI-sounding academic filler;
- prefer concrete subject-verb sentences;
- avoid inflated language such as `crucial`, `pivotal`, `showcase`, and empty `highlights`;
- keep UK spelling;
- avoid formulaic conclusion language.

### 7.2 ML-paper-writing

Use as the scientific argument layer.

Tasks:

- enforce a one-sentence contribution;
- apply What, Why, and So What logic;
- make each Results subsection state the claim it supports;
- keep figure captions self-contained;
- prevent citation hallucination by verifying references programmatically or marking gaps.

### 7.3 Nature-figure

Use for Figure 2 to Figure 4. Backend: Python, because existing M03 figures and data are already Python/Matplotlib-oriented. PowerPoint remains acceptable for the editable framework figure and small manual layout adjustments.

Figure contract:

- core conclusion first;
- each panel must carry a distinct evidence role;
- white background, restrained colours, direct labels, clear statistics;
- export PDF, PNG, SVG, and TIFF where possible.

### 7.4 Nature-citation

Use for citation discipline and final reference audit, not for restricting the paper to Nature/CNS sources. JCDE uses Oxford APA and the field requires broader 3D reconstruction literature, so the manuscript should cite the best relevant sources across JCDE, CV, graphics, and generative 3D venues.

Tasks:

- verify that cited papers exist;
- check DOI/title/year/venue consistency where metadata is available;
- prefer Crossref, DOI metadata, Semantic Scholar, arXiv, and publisher pages;
- do not add references from memory.

### 7.5 Nature-writing / nature-polishing

These are not primary writing tools for this manuscript because the user requested humanizer plus ML-paper-writing. They may be used only as secondary style checks if a section still reads too generic or if LaTeX layout needs a specialised pass.

## 8. Planned manuscript revision

1. Replace the old Figure 1 asset in LaTeX with the revised Figure 1 exported from the editable PowerPoint.
2. Keep or refresh Figure 2 from the main 100-object CSV.
3. Build a new Figure 3 from the metric-paradox CSV/asset pool.
4. Rename the existing robustness plot as Figure 4 and update all references.
5. Add or tighten Methods formulas for:
   - volume ratio;
   - z-extent ratio;
   - F-score change;
   - Chamfer change;
   - metric paradox criterion.
6. Rewrite Results so the order is:
   - representative paired examples;
   - aggregate volume and z-extent shrinkage;
   - point-metric paradox;
   - robustness.
7. Polish Introduction, Discussion, Limitations, and Conclusion under the humanizer and ML-paper-writing constraints.
8. Recompile and run the final audits.

## 9. Multi-pass final checks

### Pass 1: paragraph logic

For every paragraph, check:

- one paragraph, one claim;
- the paragraph's first sentence connects to the previous paragraph;
- the final sentence either states evidence or moves the argument forward;
- no paragraph overclaims beyond TripoSR and the tested styles.

### Pass 2: section and JCDE requirements

Check:

- abstract is one paragraph, citation-free, and concise;
- keywords no more than six;
- section titles and order match JCDE expectations;
- Graphical Abstract remains outside the manuscript PDF;
- figures are referenced in order and with `Figure` in full;
- tables have captions above them;
- declarations are present.

### Pass 3: format, length, references

Check:

- compile by `pdflatex -> biber -> pdflatex -> pdflatex`;
- PDF page count and visual placement;
- word count before References remains in the 6,000 to 8,000 target range;
- bibliography count remains at least 30 and preferably within JCDE's 20 to 40 range;
- no undefined citations;
- no uncited bibliography entries unless intentionally retained for template reasons;
- DOI/title/year/venue metadata checked across available sources.

## 10. Immediate decision

The manuscript is suitable to continue as a JCDE research article if the final version is treated as a diagnostic benchmark paper. It should not claim to introduce a stronger 3D model. The strongest novelty claim is:

`A paired cross-style benchmark shows that artistic input transformations can systematically shrink TripoSR reconstructions while improving point-based metrics, revealing a design-relevant metric gap in image-to-3D evaluation.`

