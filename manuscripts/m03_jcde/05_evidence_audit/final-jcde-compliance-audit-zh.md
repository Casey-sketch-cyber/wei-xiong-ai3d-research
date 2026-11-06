# JCDE M03 final compliance audit

Date: 2026-06-07

## Status

The manuscript and initial submission package are finalised for technical/content review, except for author-specific metadata and public data/code DOI or URL information that must be supplied before journal submission.

## Verified items

- Target journal material checked against the local JCDE template/checklist notes and the OUP/JCDE author instructions: https://academic.oup.com/jcde/pages/General_Instructions
- Main manuscript compiles successfully with `pdflatex -> biber -> pdflatex -> pdflatex`.
- Final PDF length: 20 pages.
- PDF word count before References: 6,822 words by `pdftotext` extraction, within the typical 6,000--8,000 Research Article range.
- References: 38 entries in `references.bib`; biber found 38 citekeys; no undefined citation warnings in the final LaTeX log.
- Section 3 title is `Material and methods`.
- Main framework figure is placed after the `Material and methods` heading and before the detailed benchmark subsections.
- Figure 1 is a combined benchmark overview and diagnostic result figure, not a pure workflow chart.
- Graphical abstract is generated from `graphical_abstract.pdf` and summarises the core findings: volume reduction and the point-metric/volume diagnostic mismatch.
- Graphical abstract PNG export is 5232 x 2330 pixels, above the required 1250 x 500 minimum.
- Highlights file contains 5 highlights; each checked item is no more than 15 words and no more than 100 characters.
- Main submission ZIP contains the five required initial-submission files:
  - `JCDE_M03_Main_Document.pdf`
  - `JCDE_M03_Graphical_Abstract.pdf`
  - `JCDE_M03_Highlights.docx`
  - `JCDE_submission_checklist_JCDE-202X-XXX_M03_draft.docx`
  - `JCDE_M03_Main_Document_Source_LaTeX.zip`
- Source ZIP contains `main.tex`, `references.bib`, and the three PDF figures required by the LaTeX manuscript.
- Visual QA was performed on the manuscript title page, Figure 1 page, and graphical abstract render.
- A lightweight reproducibility release package has been prepared at `04_reproducibility_package/M03_reproducibility_release.zip`.

## Remaining author-side blockers

The following items still require human author information before real submission:

- Author names, affiliations, e-mail addresses, ORCID identifiers, and corresponding-author details.
- Funding and acknowledgements.
- Author contributions.
- Final confirmation of competing-interest statement.
- Public data/code release DOI or stable URL for the prepared reproducibility package and any cleared object identifiers.

## Tool notes

`texcount` was installed through MiKTeX, but the local machine does not have the Perl engine required by MiKTeX to run it. Word count was therefore verified from extracted PDF text before the References section.
