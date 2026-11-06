# M03 JCDE final compliance audit

Date: 2026-06-23

## Manuscript status

- Main manuscript: `D:\AutoResearch\manuscripts\m03_jcde\01_manuscript\latex\main.tex`
- Compiled PDF: `D:\AutoResearch\manuscripts\m03_jcde\01_manuscript\latex\main.pdf`
- Submission copy: `D:\AutoResearch\manuscripts\m03_jcde\03_submission_materials\JCDE_M03_Main_Document.pdf`
- Article type: JCDE Research Article
- Final PDF length: 22 A4 pages
- Official JCDE requirement checked from Oxford Academic Instructions to Authors on 2026-06-23:
  - Research Article typical length: 6,000-8,000 words
  - Research Article references: 20-40 references
  - Graphical Abstract, Highlights, Checklist, Main Document PDF, and Main Document Source File are handled as separate submission materials.

## Word and structure audit

- Abstract: 201 words.
- Main body estimate excluding references and excluding figure/table bodies: 5,730 words.
- Caption text rough estimate: 60 words.
- Estimated article text excluding references: 5,991 words.
- Interpretation: the manuscript is effectively at the lower edge of the JCDE 6,000-8,000 word target. The PDF text extraction gives a higher value because it counts layout text, figure/table text, and repeated pagination artefacts more heavily.
- Section structure follows JCDE research-article logic:
  - Abstract
  - Introduction
  - Related work
  - Material and methods
  - Results
  - Discussion
  - Limitations
  - Conclusion
  - Data and code availability
  - Acknowledgements
  - Author contributions
  - Competing interests
  - References

## Figure audit

- Figure 1: framework figure revised from the user-provided AI/PPT version.
  - Editable source: `D:\AutoResearch\manuscripts\m03_jcde\02_figures_tables\publication_figures\fig1_framework_editable.pptx`
  - Manuscript asset: `D:\AutoResearch\manuscripts\m03_jcde\01_manuscript\latex\figures\fig1_framework_revised.pdf`
  - Status: checked visually in the rendered PDF; white background, no unwanted black panels, no unnecessary separator lines, and labels now distinguish input labels from output labels. The B panel label was moved close to the central TripoSR pipeline panel in the 2026-06-23 evening revision.
- Figure 2: main quantitative results.
  - Manuscript asset: `D:\AutoResearch\manuscripts\m03_jcde\01_manuscript\latex\figures\fig2_main100_results.pdf`
  - Status: checked visually; supports the central volume-shrinkage and metric-paradox claim.
- Figure 3: per-object metric paradox and representative cases.
  - Generation script: `D:\AutoResearch\manuscripts\m03_jcde\scripts\make_fig3_metric_paradox_cases.py`
  - Manuscript asset: `D:\AutoResearch\manuscripts\m03_jcde\01_manuscript\latex\figures\fig3_metric_paradox_cases.pdf`
  - Status: checked visually; now fixed with `[H]` so it appears in the correct Results subsection. The A/B/C panel labels were left-aligned and the panel A annotations were repositioned to avoid label overlap in the 2026-06-23 evening revision.
- Figure 4: robustness check at mc-resolution=128.
  - Manuscript asset: `D:\AutoResearch\manuscripts\m03_jcde\01_manuscript\latex\figures\fig4_res128_robustness.pdf`
  - Status: checked visually; supports the claim that volume shrinkage is not only a low-resolution extraction artefact.

## Compilation audit

- Main manuscript compiled with:
  - `pdflatex`
  - `biber`
  - `pdflatex`
  - `pdflatex`
- Latest compiled manuscript: 22 pages, PDF 1.7.
- Log scan: no unresolved citations, no undefined references, no overfull/underfull layout warnings requiring action, and no rerun warning.
- Source ZIP independent check:
  - Source ZIP extracted to `D:\AutoResearch\manuscripts\m03_jcde\tmp\source_zip_compile_check`
  - Independent compilation succeeded and produced a 22-page PDF.
  - After the 2026-06-23 evening Figure 1/Figure 3 revision, the updated Source ZIP was rechecked at `D:\AutoResearch\manuscripts\m03_jcde\tmp\source_zip_compile_check_figfix`; independent compilation again succeeded and produced a 22-page PDF.

## Reference audit

- Bibliography entries in final manuscript: 38.
- Cited keys in text: 38.
- Uncited bibliography entries: 0.
- DOI-bearing entries: 35.
- DOI handle resolution success: 35/35.
- Semantic Scholar coverage: 38/38, using cached selected-reference files and cached latest-candidate files where the live endpoint rate-limited.
- Cross-check outputs:
  - `D:\AutoResearch\manuscripts\m03_jcde\05_evidence_audit\reference_crosscheck_final_20260623.csv`
  - Earlier raw Crossref/API attempt retained as `reference_crosscheck_20260623.csv` and `reference_doi_semanticscholar_crosscheck_20260623.csv`.
- Interpretation: the reference list satisfies the user's requirement of at least 30 references and JCDE's 20-40 reference expectation.

## Sample-paper and skill audit

- Official/sample-paper analysis:
  - `D:\AutoResearch\manuscripts\m03_jcde\04_reviews_revisions\jcde-official-sample-and-skill-analysis-zh.md`
  - `D:\AutoResearch\manuscripts\m03_jcde\04_reviews_revisions\jcde-style-informed-writing-plan-zh.md`
- Writing workflow followed:
  - Evidence and structure were aligned with JCDE sample-paper logic.
  - Prose was shaped with the requested humanizer-first approach.
  - ML-paper writing checks were used to keep the claim, method, result, and limitation structure explicit.
  - Figure design followed the requested publication-style figure workflow rather than using a generic AI-generated diagram as-is.

## Submission package

- Updated required-files bundle:
  - `D:\AutoResearch\manuscripts\m03_jcde\03_submission_materials\JCDE_M03_initial_submission_required_files.zip`
- Bundle contents:
  - `JCDE_M03_Main_Document.pdf`
  - `JCDE_M03_Graphical_Abstract.pdf`
  - `JCDE_M03_Highlights.docx`
  - `JCDE_submission_checklist_JCDE-202X-XXX_M03_draft.docx`
  - `JCDE_M03_Main_Document_Source_LaTeX.zip`
- Source ZIP contents:
  - `main.tex`
  - `references.bib`
  - `figures/fig1_framework_revised.pdf`
  - `figures/fig2_main100_results.pdf`
  - `figures/fig3_metric_paradox_cases.pdf`
  - `figures/fig4_res128_robustness.pdf`

## Remaining author-side items

- Author information, affiliations, e-mail addresses, and corresponding-author details were inserted on 2026-07-01.
- The ORCID iD line was removed from the manuscript title page on 2026-07-01 at the author's request; ORCID iDs can still be supplied in the journal submission metadata if needed.
- Confirm final spelling/capitalisation of author names, especially `ShuWen Li`.
- Confirm final English form of the third affiliation, currently written as `Guilin Life and Health Career Technical College`.
- Confirm funding, acknowledgements, author contributions, and competing-interest statement.
- Insert the final public repository DOI or stable URL in Data and code availability after the release location is decided.
- Confirm whether raw Objaverse object identifiers can be shared in the cleared release package under each object's licence.
