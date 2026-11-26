# 投稿任务书：*Applied Sciences*（MDPI）

> 历史任务书。作者已改投 [PeerJ Computer Science](SUBMISSION_PEERJ_CS.md)。

> Claude 起草，2026-11-25。作者已选定投 MDPI *Applied Sciences*（ISSN 2076-3417，Basel）。投稿栏目选 **Computing and Artificial Intelligence**。本文件给 Gemini 和 Codex 分配投稿版的工作。期刊要求依据 [作者须知](https://www.mdpi.com/journal/applsci/instructions)，于 2026-11-25 查阅；开工前若发现须知已改，以官网为准，并在 PR 里注明。

## 期刊概况（2026-11-25 查阅）

- 文章类型选 Article。正文没有字数上限，v4 约 9,000 词，不用为字数删内容。
- 版面费 CHF 2,400，录用后才收（[APC 页](https://www.mdpi.com/journal/applsci/apc)）。
- JCR Q2（Engineering, Multidisciplinary），IF 2.9（[期刊主页](https://www.mdpi.com/journal/applsci)）。

## 分工与顺序

| 谁 | 做什么 | 分支 / 产出 |
| --- | --- | --- |
| Gemini | 以 v4 为底稿，按下面“正文要求”写投稿版正文、Featured Application 和 cover letter | 分支 `gemini/paper-v5-applsci`。产出 `docs/paper/draft-v5-applsci.md` 和 `docs/paper/cover-letter-applsci.md` |
| Codex | 套 MDPI 官方模板，并核对格式和文献（见“模板、格式与文献”）。准备模板和 `.bib` 不依赖 Gemini 的正文，可与 Gemini 同时开工；正文到位后再排版、核对 | 分支 `codex/applsci-template`。产出 `docs/paper/applsci/` |
| Claude | 审查两个 PR，做最后的润色和图的把关 | — |
| 作者 | 填写署名、单位、基金和 CRediT 角色；确认利益冲突、AI 声明、数据访问方式和项目许可证；推荐 3 位审稿人；最后在 SuSy 系统提交 | — |

`draft-v4.md`（以及更早的各版）只读，不要改。

## 正文要求（Gemini）

**不改内容的前提。** 数字、分母、结论范围和引文都沿用 v4。v4 已经由 Codex 核过，这一轮只按期刊要求调整格式和篇幅。v4 里没有的数字不要写进来。

1. **摘要。** 压到 **200 词以内**，写成一段，不加 Background、Methods 之类的小标题（须知原文：“about 200 words maximum”，单段结构式）。目前是 248 词。建议保留：三项协议细节各一个核心数字，排序结论，以及“必须报告这三项”。缩写首次出现时写全称。
2. **关键词。** 3–10 个，沿用 v4 的 6 个即可。
3. **Featured Application。** *Applied Sciences* 可选、建议写。用 1–2 句话说明这项研究对博物馆数字化或修复规划人员的实际用处。不加新数字。
4. **章节顺序。** Introduction → Related Work → Materials and Methods → Results → Discussion → Conclusions。“Related Work”单列一节在 Computing and AI 栏目很常见，可以保留，但不要变长。
5. **方法里加一段生成式 AI 说明。** MDPI 要求：生成式 AI 参与了代码、分析或文字的，须在 Materials and Methods 里说明。在 §3 末尾加一小段（例如 *3.5 Use of Generative AI Tools*），写清三件事：
   - Claude、Gemini、Codex 各做了什么：实验与图的代码、统计核对脚本、英文写作与编辑；
   - 研究问题、方案定稿和结论解读由作者决定；
   - 所有数字都由脚本从冻结的运行结果复算。

   只改语法、拼写的工具不需要写。
6. **文末各项，按 MDPI 的顺序。**
   1. Supplementary Materials：引用 `SUPPLEMENT.md` 对应的补充文件，按 “Table S1: …” 的格式命名；
   2. Author Contributions：MDPI 写法，例如 “Conceptualization, X.X.; methodology, X.X.; …”，名字缩写留占位；
   3. Funding：作者确认前先写 “This research received no external funding.”，并标为待确认；
   4. Institutional Review Board Statement：Not applicable.；
   5. Informed Consent Statement：Not applicable.；
   6. Data Availability Statement：沿用 v4 的三层说法；
   7. Acknowledgments：按 MDPI 模板写 AI 声明，“During the preparation of this manuscript/study, the author(s) used [tool name, version information] for the purposes of [description of use]. The authors have reviewed and edited the output and take full responsibility for the content of this publication.”，工具名和用途与 §3 那段一致；
   8. Conflicts of Interest：“The authors declare no conflicts of interest.”，标为待确认；
   9. Abbreviations：可选，列出 MAE、LPIPS、DISTS、ΔE00、CMA、AIC、VAE、CFG 等；
   10. References。

   v4 的 Code Availability 并入 Data Availability Statement，或者放进 Supplementary Materials 的说明里。MDPI 没有单独的代码声明栏目。权重部分采用 [PR #38](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/38) 里 Codex 核实过的写法：LaMa、MAT 用 IOPaint 发布件，PowerPaint 源码 `5b4c3d5` / 权重 `b4174b7`，SDXL 权重 `115134f`；溯源旁车文件只说“有记录的运行”。
7. **引文。** 继续用 `[@key]`，不要自己改成编号，编号由 Codex 的 BibTeX 生成。不要新增引文；如果确实需要，写 `[@TODO-…]` 并在 PR 里列出。
8. **图表。**
   - 每张图、每个表的说明都写成“一句短标题 + 说明”。
   - 表里的 `*`、`†` 等符号都要在说明里解释。
   - 缩写在第一张图或第一个表里也要写全称。
   - 图 1、图 2 的说明沿用 v4，保留 57.8% 和 59.5%。
9. **Cover letter**（`cover-letter-applsci.md`，英文，一页以内）。写四点：
   - 研究的意义，以及与已有工作的关系；
   - 为什么适合 Computing and Artificial Intelligence 栏目；
   - 声明 “not published or under consideration elsewhere”；
   - 声明 “all authors approved the submission”。

   不要在信里推荐审稿人。署名留占位。

**交稿检查**（写进 PR 描述）：
- [ ] 摘要 ≤ 200 词；
- [ ] 数字与 v4 一致；
- [ ] `[@key]` 集合与 v4 相同；
- [ ] 方法里有 AI 说明，Acknowledgments 里有 AI 声明；
- [ ] 文末各项的顺序正确；
- [ ] 所有待作者确认项都用斜体标注，并在 PR 里列出；
- [ ] v4 未改动。

## 模板、格式与文献（Codex）

1. **模板。** 从 [MDPI LaTeX 页](https://www.mdpi.com/authors/latex) 下载官方模板，设 `\documentclass[applsci,article,submit,pdftex,moreauthors]{Definitions/mdpi}`，单作者时去掉 `moreauthors`。模板只用于投稿，不得用于预印本服务器。用 LaTeX 是因为图是矢量 PDF，公式和表格也更容易控制。如果作者要 Word 版，再用 [Word 模板](https://mdpi-res.com/files/word-templates/applsci-template.dot) 另出一份。
2. **文献**（`references.bib`）。
   - 52 个键都要有条目，与 `literature/papers.csv` 和 v4 文末一一对应。
   - 写全文章标题，有 DOI 的都填上；软件、模型卡、GitHub 版本写清版本号或 commit 和访问日期。四个权重发布件按 PR #38 核实的版本建条目（PowerPaint 权重 `b4174b7`、SDXL `115134f`、IOPaint 的 LaMa/MAT 发布页）。
   - 用模板自带的 MDPI 编号格式，按首次出现排序。引用用方括号、放在标点前，例如 `[1–3]`。图表说明里的引用也参与编号。
   - 检查有没有正文没引用的条目，或引用了却没有条目的键。
3. **格式核对。**
   - 摘要字数；关键词 3–10 个；
   - 缩写首次出现处写全称（摘要、正文、第一张图表各一次）；
   - 表格每列都有列名，排版后字号 ≥ 8 pt；
   - 图按首次引用的顺序编号，放在首次引用附近；
   - 文末各项的顺序与上面“正文要求”第 6 条一致；
   - 编译无错误，无明显 overfull；
   - 表 1–7 的数值与 v4 逐行一致。
4. **图片文件。**
   - 正文用服务器归档的矢量 PDF。
   - 另外导出 **600 dpi** 的 PNG 或 TIFF，供系统单独上传，须知写的是 “preferably no less than 600 dpi”。图 1、图 2 从 `build.sh` 的 `fig.final.svg` 导出；图 3–6 用原脚本重出。
   - 图形摘要可选，最小 1100 × 560 像素，不能与正文的图重复。作者不要求就不做。
5. **审稿人候选**（只做参考，由作者决定）。从引文作者里找 5–6 位与作者不同单位、近三年没有合作过的人，列出姓名、单位、公开的机构主页和代表作。放在 PR 描述里，不进稿件，也不写进 cover letter。
6. **进 Git 与不进 Git。**
   - 进 Git：`.tex`、`.bib`、`Definitions/`（先查模板自带的许可说明，允许再分发才入库，否则只放服务器，并在 README 写下载地址和版本）、编译出的 PDF 第一页预览 PNG（≤ 1 MB）。
   - 不进 Git：图片、PDF 全文和提交用的 ZIP，这些放服务器数据盘 `paper/applsci-submission/`，并在 PR 里给出清单 SHA-256。
   - 写好 `.gitignore`，确保这些文件不会被误提交。

## 不变的规则

- 不新增实验，不改结论范围。
- 图像和权重不进 Git。
- 不强推，不改写已推送的历史。
- 不在 Git 里放任何密钥。
