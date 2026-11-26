# PeerJ Computer Science LaTeX 投稿版

正文排版以 Gemini 的 v5（`6a34c78`）及已核对的 56 条参考文献为据。审稿稿采用 12 pt Times、US Letter、1 英寸边距、左对齐和连续行号。引文按作者—年份显示。适用投稿要求与作者待确认项见[投稿交接](../SUBMISSION_PEERJ_CS.md)。

## 编译

投稿源码 ZIP 附带用于本次编译的 `wlpeerj.cls` 和六份矢量图。独立检出时，将该类文件放在 `manuscript.tex` 旁，并从服务器审查包的 ZIP 提取 `figures/`。类文件是 PeerJ/Overleaf 模板采用的 `wlpeerj` v1.2，复编使用 rticles 的离线版本（提交 `accdfa39225570a8ad9b786fbb3077060d1e12a5`，SHA-256 `7e8fe7e34634bbb864a57ee168cc6614d4f59b3623373e77141b67e6fe7037ac`）。PeerJ/Overleaf 模板页列 CC BY 4.0，rticles 随包标 GPL-3。[官方模板](https://www.overleaf.com/latex/templates/latex-template-for-peerj-journal-submissions/ptdwfrqxqzbn) · [离线类来源](https://github.com/rstudio/rticles/blob/accdfa39225570a8ad9b786fbb3077060d1e12a5/inst/rmarkdown/templates/peerj/skeleton/wlpeerj.cls)

```sh
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
bibtex manuscript
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error cover-letter.tex
```

辅助 PDF 使用独立的单栏格式。补充文件在系统中标为 `Supplemental Article S1`。投稿表单说明供作者填写字段时使用。每个 `tables/TableN.tex` 都是正文引用的可编辑表源。

## 图件映射

| 投稿图 | 服务器冻结矢量图文件名 |
| --- | --- |
| Fig1.png | `figure-1-teaser.pdf` |
| Fig2.png | `figure-2-pipeline.pdf` |
| Fig3.png | `figure-3-examples.pdf` |
| Fig4.png | `figure-4-latent-coverage.pdf` |
| Fig5.png | `figure-6-powerpaint-coverage.pdf` |
| Fig6.png | `figure-5-condition-mae.pdf` |

图号随正文首次引用。独立 PNG 从对应矢量 PDF 按 3000 px 宽渲染。审查包放在服务器数据盘的 `paper/peerj-cs-submission/doi-20261126/`，清单覆盖正文、独立补件、源 ZIP、六张 PNG 与七张表。独立复现代码采用 MIT，当前归档快照为 `0b34175`。审查包另含八个机器可读补件、SHA-256 索引及 MIT 软件 1.0.0 的归档快照。[复现仓库](https://github.com/liangdagongjue-code/mengwei/tree/0b3417599e6dfd88b9597789cfca762a91c66251) · [版本 DOI](https://doi.org/10.5281/zenodo.24561409)
