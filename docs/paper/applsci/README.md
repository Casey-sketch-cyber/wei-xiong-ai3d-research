# Applied Sciences 投稿版

期刊栏目为 Computing and Artificial Intelligence。LaTeX 正文基于 Gemini 的投稿稿 `6a34c78`。作者稿和投稿信的原始 Markdown 位于本目录的上一级。此目录中的 `manuscript.tex`、`supplement.tex` 和 `cover-letter.tex` 可直接编辑。

## 编译

1. 下载 MDPI 的 **ACS Citation Style** 模板，使用 2026-11-12 发布包中的 `Definitions/`。本次使用 `mdpi.cls` v6.5e（类日期 2026-11-09），ZIP 的 SHA-256 为 `f6d5ae546a3d246bd73ee1dbaefc60a8b7398496ef7cfc8e10b7cc83d26067b7`。官方 ZIP 未随附再分发说明，`Definitions/` 随投稿包保存在服务器数据盘。[MDPI LaTeX 下载页](https://www.mdpi.com/authors/latex)
2. 在 `manuscript.tex` 同目录放置 `Definitions/`，并将服务器数据盘 `paper/applsci-submission/figures/` 中的六份矢量 PDF 复制到 `figures/`。图件清单 SHA-256 为 `92e9a916389225925bac565c6dc75edcb8f5724c78858acd7a43dfdf946ebc5e`。
3. 使用 TeX Live 的 pdfLaTeX 和 BibTeX。作者名单确定后，单作者从文档类选项中去掉 `moreauthors`。正文的编号引用由 MDPI 的 `mdpi.bst` 按首次出现排序。投稿 ZIP 包含用 `epstopdf` 从官方 EPS 转换的 PDF 标识。使用单独下载的模板时，可先运行 `epstopdf --outfile=Definitions/logo-mdpi-eps-converted-to.pdf Definitions/logo-mdpi.eps`。

```sh
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
bibtex manuscript
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error cover-letter.tex
```

## 图件上传顺序

| 投稿图号 | 归档图件文件名（PDF 和 600 dpi PNG 共用） |
| --- | --- |
| 1 | `figure-1-teaser` |
| 2 | `figure-2-pipeline` |
| 3 | `figure-3-examples` |
| 4 | `figure-4-latent-coverage` |
| 5 | `figure-6-powerpaint-coverage` |
| 6 | `figure-5-condition-mae` |

图 5、图 6 按首次引用排序。期刊模板用于投稿。作者需确认署名、单位、通讯信息、CRediT、基金、利益冲突、AI 工具版本与审阅范围、归档访问方式及项目许可证，并核对投稿信中的作者批准和投稿状态声明。投稿前在 SuSy 核对期刊要求。[作者须知](https://www.mdpi.com/journal/applsci/instructions)
