from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Mm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
LATEX = ROOT / "01_manuscript" / "latex"
FIGURES = ROOT / "02_figures_tables" / "publication_figures"
TEMPLATE = ROOT / "00_journal_template" / "original_package"
OUT = ROOT / "03_submission_materials"

TITLE = (
    "Cross-style robustness in image-to-3D generation is model-specific: "
    "A paired four-model benchmark with known 3D ground truth"
)


def set_normal_style(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(11)
    style.font.color.rgb = RGBColor(0, 0, 0)
    for section in doc.sections:
        section.page_width = Mm(210)
        section.page_height = Mm(297)
        section.top_margin = Mm(25.4)
        section.bottom_margin = Mm(25.4)
        section.left_margin = Mm(25.4)
        section.right_margin = Mm(25.4)


def add_title(doc: Document, text: str) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(3)
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = para.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(16)
    run.bold = True
    run.font.color.rgb = RGBColor(0, 0, 0)


def make_highlights() -> Path:
    doc = Document()
    set_normal_style(doc)
    add_title(doc, "Highlights")
    bullets = [
        "A paired benchmark compares five abstractions across four image-to-3D systems.",
        "All 6,240 reconstructions are evaluated against known watertight 3D ground truth.",
        "The pre-specified universal sketch robustness gap fails in all four models.",
        "Sketch degradation is severe for InstantMesh but small for Hunyuan3D and TRELLIS.",
        "Surface, solid, topology, and multi-view diagnostics expose model-specific failure modes.",
    ]
    for item in bullets:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(4)
        p.add_run(item)
    path = OUT / "JCDE_M03_Highlights.docx"
    doc.save(path)
    return path


def make_alt_text() -> Path:
    doc = Document()
    set_normal_style(doc)
    add_title(doc, "Figure Alt Text")
    entries = [
        (
            "Figure 1",
            "Paired cross-style benchmark illustrated with one Google Scanned Objects case. A photo-like rendering and five matched abstractions share the same object, camera, foreground mask, and framing. TripoSR, InstantMesh, Hunyuan3D 2.1, and TRELLIS process the same inputs. Their meshes are aligned with one fixed transform per model and evaluated against watertight ground truth using surface, solid, topology, and six-view render diagnostics.",
        ),
        (
            "Figure 2",
            "Main quantitative results for 120 objects. A heat map shows robustness-gap means for each model and abstraction. A confidence-interval plot shows that none of the four model-specific sketch tests passes the one-percent Holm-corrected criterion. A component plot shows that InstantMesh loses substantially in both F-score and voxel intersection over union, whereas Hunyuan3D 2.1 and TRELLIS have small mean canonical-sketch changes.",
        ),
        (
            "Figure 3",
            "Three pre-defined representative cases compare the ground-truth object, paired photo and sketch inputs, and the corresponding photo- and sketch-conditioned meshes. The cases include two positive robustness-gap examples and one negative-gap counterexample, demonstrating that the gap sign alone does not determine reconstruction quality.",
        ),
        (
            "Figure 4",
            "Robustness checks and independent diagnostics. Panels report sketch robustness gaps at two additional views, abstraction-severity slopes, agreement across two random seeds, and six-view silhouette and normal-render changes. Results show that canonical-view rankings are not fully stable across view, severity, or seed.",
        ),
    ]
    for label, text in entries:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(label + ": ")
        r.bold = True
        p.add_run(text)
    path = OUT / "JCDE_M03_Alt_Text.docx"
    doc.save(path)
    return path


def fill_checklist() -> Path:
    src = TEMPLATE / "Submission Checklist_V2.21" / "JCDE submission checklist (JCDE-202X-XXX) V2.21.docx"
    path = OUT / "JCDE_submission_checklist_JCDE-202X-XXX_M03_draft.docx"
    shutil.copy2(src, path)
    doc = Document(path)
    # Fill the first metadata table with the supplied manuscript information.
    if doc.tables:
        table = doc.tables[0]
        for row in table.rows:
            cells = row.cells
            label = " ".join(c.text.strip() for c in cells[:3])
            if "Manuscript Title" in label and len(cells) >= 4:
                cells[3].text = TITLE
            elif "List of All Authors" in label and "Full Names" in label and len(cells) >= 4:
                cells[3].text = "Wei Xiong, Wei Meng, Chu Qiu, ShuWen Li, Zhanhao Liang"
            elif "List of All Authors" in label and "E-mail Addresses" in label and len(cells) >= 4:
                cells[3].text = (
                    "xiongwei@guit.edu.cn; mengwei@mail.glnc.edu.cn; "
                    "appamm94@gmail.com; lishuwen@guit.edu.cn; "
                    "lyon@cumt.edu.cn"
                )
            elif "1st" in label and "CA" in label and "Full Name" in label and len(cells) >= 4:
                cells[3].text = "Chu Qiu"
            elif "1st" in label and "CA" in label and "Affiliation" in label and len(cells) >= 4:
                cells[3].text = (
                    "Guilin Life and Health Career Technical College, "
                    "No. 1 Zhongyin West Road, Xiufeng District, "
                    "Guilin, Guangxi 541001, China"
                )
            elif "1st" in label and "CA" in label and "E-mail" in label and len(cells) >= 4:
                cells[3].text = "appamm94@gmail.com"
            elif "1st" in label and "CA" in label and "ORCID" in label and len(cells) >= 4:
                cells[3].text = "https://orcid.org/0009-0004-3523-5659"
            elif "2nd CA" in label and "Full Name" in label and len(cells) >= 4:
                cells[3].text = "Zhanhao Liang"
            elif "2nd CA" in label and "Affiliation" in label and len(cells) >= 4:
                cells[3].text = (
                    "School of Materials Science and Engineering, "
                    "South China University of Technology, Guangzhou, China"
                )
            elif "2nd CA" in label and "E-mail" in label and len(cells) >= 4:
                cells[3].text = "lyon@cumt.edu.cn"
            elif "2nd CA" in label and "ORCID" in label and len(cells) >= 4:
                cells[3].text = "Not available"
            elif "APC-Paying Author" in label and "Full Name" in label and len(cells) >= 4:
                cells[3].text = "Chu Qiu"
            elif "APC-Paying Author" in label and "E-mail" in label and len(cells) >= 4:
                cells[3].text = "appamm94@gmail.com"
            elif "APC-Paying Author" in label and "Affiliation" in label and len(cells) >= 4:
                cells[3].text = "Guilin Life and Health Career Technical College"
            elif "APC-Paying Author" in label and "Address" in label and len(cells) >= 4:
                cells[3].text = "No. 1 Zhongyin West Road, Xiufeng District"
            elif "APC-Paying Author" in label and "City" in label and len(cells) >= 4:
                cells[3].text = "Guilin"
            elif "APC-Paying Author" in label and "Province" in label and len(cells) >= 4:
                cells[3].text = "Guangxi"
            elif "APC-Paying Author" in label and "Postal Code" in label and len(cells) >= 4:
                cells[3].text = "541001"
            elif "APC-Paying Author" in label and "Country" in label and len(cells) >= 4:
                cells[3].text = "China"
        for row_index in range(2, 10):
            table.cell(row_index, 4).text = "X"
        for row_index in range(14, 22):
            table.cell(row_index, 4).text = "X"

    # Mark requirements satisfied by the current manuscript and the submission
    # assumptions recorded in AUTHOR_DECLARATIONS_APPLIED-zh.md.
    review_rows = {
        1: [1],
        2: [1, 2, 3, 5, 8, 10, 12, 14, 15, 16, 17, 18],
        3: [1, 2, 4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30],
        4: [1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14, 16, 17, 18],
        5: list(range(1, 20)) + [32, 33, 34],
    }
    for table_index, rows in review_rows.items():
        if table_index >= len(doc.tables):
            continue
        target = doc.tables[table_index]
        mark_column = len(target.columns) - 2
        for row_index in rows:
            if row_index < len(target.rows):
                target.cell(row_index, mark_column).text = "X"

    # Record the selected answers as well as marking the checklist items as
    # reviewed: this manuscript is neither a special-issue submission nor a
    # previously posted preprint.
    if len(doc.tables) > 2:
        status_table = doc.tables[2]
        status_table.cell(5, 3).text = "X"
        status_table.cell(8, 3).text = "X"
    doc.save(path)
    return path


def copy_main_pdf() -> Path:
    dst = OUT / "JCDE_M03_Main_Document.pdf"
    shutil.copy2(LATEX / "main.pdf", dst)
    return dst


def copy_graphical_abstract() -> Path:
    src = OUT / "Graphical_abstract.pdf"
    dst = OUT / "JCDE_M03_Graphical_Abstract.pdf"
    shutil.copy2(src, dst)
    return dst


def make_source_zip() -> Path:
    zip_path = OUT / "JCDE_M03_Main_Document_Source_LaTeX.zip"
    include = [
        LATEX / "main.tex",
        LATEX / "references.bib",
        LATEX / "figures" / "fig1_confirmatory_framework.pdf",
        LATEX / "figures" / "fig2_confirmatory_main.pdf",
        LATEX / "figures" / "fig3_confirmatory_cases.pdf",
        LATEX / "figures" / "fig4_confirmatory_robustness.pdf",
    ]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in include:
            arcname = path.relative_to(LATEX)
            zf.write(path, arcname.as_posix())
    return zip_path


def make_author_note() -> Path:
    path = OUT / "AUTHOR_DECLARATIONS_APPLIED-zh.md"
    path.write_text(
        "\n".join(
            [
                "# M03 JCDE 已采用的作者声明与投稿假设",
                "",
                "以下内容根据用户于 2026-07-30 的授权，按论文工作链、作者排序和 JCDE CRediT 要求写入。",
                "",
                "## CRediT",
                "",
                "- Wei Xiong: Conceptualization; Methodology; Software; Validation; Formal analysis; Investigation; Data curation; Visualization; Writing - original draft.",
                "- Wei Meng: Methodology; Validation; Formal analysis; Investigation; Writing - review & editing.",
                "- Chu Qiu: Conceptualization; Resources; Supervision; Project administration; Writing - review & editing.",
                "- ShuWen Li: Data curation; Validation; Investigation; Visualization; Writing - review & editing.",
                "- Zhanhao Liang: Supervision; Writing - review & editing.",
                "",
                "正文另含：All authors reviewed and approved the final manuscript.",
                "",
                "## 其他投稿信息",
                "",
                "- Funding: no specific grant.",
                "- Special issue: No.",
                "- Preprint: No.",
                "- APC-paying author: Chu Qiu.",
                "- APC affiliation: Guilin Life and Health Career Technical College.",
                "- APC address: No. 1 Zhongyin West Road, Xiufeng District, Guilin, Guangxi 541001, China.",
                "- Corresponding authors: Chu Qiu (first); Zhanhao Liang (second).",
                "- Reproducibility repository: not yet public; the auditable package is available from the corresponding authors during peer review.",
                "- ORCID: the deleted multi-author ORCID summary was not restored. Chu Qiu's ORCID is retained in the title-page contact line; Zhanhao Liang has no ORCID, as confirmed by the user on 2026-09-09.",
                "",
                "## 责任边界",
                "",
                "以上为基于现有证据的保守分配。投稿行为仍表示五位作者认可作者顺序、贡献声明、无专项资助声明和最终稿内容。",
                "AI-assisted drafting and code/document preparation should be transparently disclosed in the cover letter according to the submission system's current policy.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def make_required_files_zip(
    main_pdf: Path,
    graphical_abstract: Path,
    highlights: Path,
    checklist: Path,
    source_zip: Path,
) -> Path:
    zip_path = OUT / "JCDE_M03_initial_submission_required_files.zip"
    items = [
        (main_pdf, "1_Main_Document.pdf"),
        (graphical_abstract, "2_Graphical_abstract.pdf"),
        (highlights, "3_Highlights.docx"),
        (checklist, "4_Checklist.docx"),
        (source_zip, "5_Main_Document_Source_LaTeX.zip"),
    ]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, arcname in items:
            zf.write(path, arcname)
    return zip_path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    main_pdf = copy_main_pdf()
    graphical_abstract = copy_graphical_abstract()
    highlights = make_highlights()
    alt_text = make_alt_text()
    checklist = fill_checklist()
    source_zip = make_source_zip()
    author_note = make_author_note()
    required_zip = make_required_files_zip(
        main_pdf,
        OUT / "Graphical_abstract.pdf",
        highlights,
        checklist,
        source_zip,
    )
    outputs = [
        main_pdf,
        graphical_abstract,
        highlights,
        alt_text,
        checklist,
        source_zip,
        author_note,
        required_zip,
    ]
    for item in outputs:
        print(item)


if __name__ == "__main__":
    main()
