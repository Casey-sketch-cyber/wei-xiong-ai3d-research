# M03 JCDE writing process

User-preferred order for manuscript drafting:

1. Lock evidence and structural boundaries first.
2. Draft prose using the humanizer-first style requested by the user: avoid AI-like inflation, vague claims, promotional language, mechanical transitions, and unsupported significance statements.
3. Apply the `20-ml-paper-writing` discipline after drafting: contribution clarity, citation verification, BibTeX hygiene, and ML/AI paper-style argument checks.
4. Use `nature-skills` for later figure production and figure QA.

## Current draft status

- Working manuscript: `01_manuscript/latex/main.tex`
- Verified bibliography: `01_manuscript/latex/references.bib`
- Citation source: arXiv API metadata fetched during drafting.
- Scope boundary: the manuscript frames M03 as a controlled benchmark and diagnostic analysis, not a new image-to-3D model.
- Compile status: `01_manuscript/latex/main.pdf` builds successfully with `pdflatex -> biber -> pdflatex -> pdflatex`.
- TeX packages installed during compile setup: `hycolor`, `biblatex-apa`, `stringenc`, `intcalc`, `bitset`, `bigintcalc`, `threeparttable`, `caption`, `preprint`, `titlesec`, `csquotes`, `psnfss`, `setspace`, and `float`.
- Remaining compile notes: two minor bibliography overfull warnings and one unused figure-caption setup warning; no undefined citations or cross-references.
- Pending: author details, final related-work expansion, figure regeneration, graphical abstract, highlights, and JCDE checklist.
