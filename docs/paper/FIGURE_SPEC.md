# 论文配图设计说明

> 给 Codex 的配图任务书，Claude 起草于 2026-11-21。先读完全文再动手。正文图注由 Gemini 按本说明重写。

## 当前做法（2026-11-21 起，优先于下文中与之冲突的条目）

作者决定：**图 1、图 2 由 Claude 用 [FigGenie](https://github.com/Sleepy-Avacado/FigGenie-paper-diagram-skill)（MIT）画**，Codex 负责把服务器上的真实画作裁片和模型输出放进去并运行构建脚本。FigGenie 的规则统计自 3,528 篇 AI 顶会论文的 Figure 1 和 2,041 张人工评分的系统顶会插图，与彭老师"第一眼漂亮、高级"的要求一致；它直接产出可编辑的 PowerPoint，满足"用 PowerPoint 画 pipeline 图"的要求。

**流程**（FigGenie 的 8 步，在本项目的落地）：
1. 简报：图要让读者看到什么，见本文第 3、4 节。
2. 规格 `spec.json`：由 `make_fig*.py` 一并写出，用 `spec_validate.py` 校验。
3. 范例：Claude 用 `find_ai_exemplars.py` 检索 AI 顶会 Figure 1，选了 cvpr26-0019（每个问题一栏、红框问题绿框修正）、icml26-0066（面板下方加 (a)(b)(c) 标题、虚线分隔）、cvpr26-0033（一对颜色贯穿全图）。只借用做法，不照抄。
4. 绘图计划写在 `make_fig*.py` 的坐标里。
5. 手写 SVG：1 单位 = 1 pt，每个元素一个 `<g id>`，图片放 `<image>`。
6. 检查循环：`check.py` 做 lint、渲染和人工看图，**lint 必须 0 错误**。
7. 交付：`embed_fonts.py` 嵌入字体，`export_pdf.py` 导出论文用 PDF，`svg2pptx.py` 导出可编辑 PPTX，再用 `pptx_noshadow.py` 去掉 PowerPoint 主题阴影。
8. 按反馈修改后重跑。

一条命令完成：`bash docs/paper/figures/src/build.sh`（参数见脚本头部）。

**与下文规则的调和**
- **字号**：改用 FigGenie 的印刷规则。正文 6.5 pt，标题 7.5 pt，关键数字 9 pt，最多三级，任何文字不小于 6 pt。第 2 节"7–8 pt / 9 pt / 10 pt"作废。
- **宽度**：按 CVPR 通栏 495 pt（17.5 cm）画，期刊双栏通用。
- **配色**：沿用第 2 节"浅色底块、同色相深色边线、单一强调色"的原则，判定色改用 FigGenie 的 `verdict-contrast` 色组：错 `#C00000`，对 `#70AD47`，蓝 `#4472C4`，浅蓝 `#DEEBF7`。红绿判定一律加 ✓ / ✗ 符号，不只靠颜色。
- **图标**：简单图标（盾牌、博物馆、锁）直接用矢量形状画。不使用 FigGenie 自带的 `assets/symbols` 和范例图，它们裁自其他论文，只能当参考。
- **真实图片**：(a) 的覆盖图由 `experiments/make_teaser_assets.py` 按冻结的掩码种子规则重建，是真实几何；画作裁片和 SDXL 输出必须用服务器上的真实文件，占位图不得进入投稿版。

## 0. 为什么重做

彭老师的[论文写作模板](https://pengsida.notion.site/c1a22465a0fa4b15a12985223916048e)把画图放在写作流程的第 1 步（"画一个清楚的 pipeline figure 的草图"）和第 6 步（"美化 pipeline figure，画论文 teaser 图"），并说论文拿到好评审的关键是"第一眼看起来很漂亮、高级"，第一条就是"好看的 teaser figure、pipeline figure"。作者要求 teaser 和 pipeline 图用 **PowerPoint** 画。

现在的图 1 用 Matplotlib 画方框，内容是整个实验流程。问题有两个：观感像实验记录；读者看不出这篇论文新在哪里。

## 1. 参考的顶会画法

不照抄任何一张图，借的是下面这些做法：

| 做法 | 参考 | 用在哪里 |
| --- | --- | --- |
| 用浅色底块区分"像素空间"和"潜空间"，同一种空间全图同色 | Latent Diffusion（Rombach 等，CVPR 2022）的方法图 | 图 1(a)、图 2 |
| 把几种方案并排放，差异处用强调色，其余全部灰色 | BrushNet（Ju 等，ECCV 2024）对比几类补全架构的图 | 图 1(b) |
| teaser 放真实结果缩略图，不放抽象方框；一栏只讲一件事；数字直接写在图上 | CVPR/ECCV 常见的 teaser 写法 | 图 1 |
| 从左到右单向流动；圆角矩形；箭头统一粗细；每个模块配一个小图标 | 计算机视觉论文常见的 pipeline 图 | 图 2 |
| 每个分图一个圆角面板，蓝灰细边框，分图标签 (a)(b)(c) 放在面板底边中间，面板里以真实图像为主、文字很少 | 4K4D（Xu 等，CVPR 2024，彭老师组）的 pipeline 图 | 图 1、图 2 |
| 大面积浅色底块（浅黄、浅蓝、浅橙）区分模块，深绿或深蓝细字 | PowerPaint（Zhuang 等，ECCV 2024）的 overview 图 | 图 2 |
| 结果网格每列一个方法、每行一个案例，列标题在顶上，放大框标出细节 | 补全论文的定性对比图（LaMa、MAT、PowerPaint 等） | 图 3 |

动手前，Codex 先找出上面几篇论文的对应图，各截一张缩略图，放在服务器的 `paper/figure-refs/`（不进 Git），作为风格参考。

## 2. 全文统一的视觉规范

**配色**：取自顶会图的实测配色。2026-11-21，Claude 在浏览器里对 BrushNet 图 2、图 3，PowerPaint 图 2，4K4D 图 2 的原图做了像素统计，去掉白色和灰色后，出现最多的颜色是：
- BrushNet：浅粉 `#F8D8D8`、浅蓝 `#D8E8F8`、浅黄 `#F8F8C8`；强调色为亮蓝 `#3888D8`，深红 `#883838` 用于文字和边线。
- PowerPaint：浅黄、浅蓝、浅杏 `#F8E8D8`。
- 4K4D：低饱和蓝灰 `#8898B8`，文字为深灰蓝 `#383848`。

共同规律：
- 模块底块用大面积**低饱和浅色**；边线和文字用**同色相的深色**；
- **只有一种高饱和强调色**，而且只用在要读者注意的地方；
- 渲染图和照片本身是彩色的，所以框架颜色要淡。

本文据此定配色，全文所有图一致，每种颜色只表示一种含义：

| 用途 | 底块（浅） | 边线 / 文字（深） | 出处 |
| --- | --- | --- | --- |
| 面板边框、默认文字 | — | `#8898B8` 边框，`#383848` 文字 | 4K4D |
| 输入与数据（画作、裁片、掩码） | `#F8F8C8` 浅黄 | `#8A7A3A` | BrushNet / PowerPaint |
| 像素空间（LaMa、MAT） | `#E8E8D8` 米灰 | `#6B6B58` | BrushNet |
| 潜空间（PowerPaint、SDXL） | `#D8E8F8` 浅蓝 | `#3888D8` | BrushNet |
| **问题**：漏掉的像素、被拦截的条件、变暗 | `#F8D8D8` 浅粉 | `#B84848` 砖红 | BrushNet |
| **修正后 / 可评分** | `#E2F0D9` 浅绿 | `#3A6B48` 深绿 | PowerPaint |
| 唯一的高饱和强调色（图 1 每栏最关键的那个数字或像素） | — | `#3888D8` 亮蓝；问题类强调用 `#D04848` | BrushNet |

数据图里的模型颜色沿用同一套色相：像素空间的两个模型用蓝色系，扩散模型用暖色和紫色，再用**点的形状**区分，保证灰度打印也能分清。

| 模型 | 颜色 | 点形 |
| --- | --- | --- |
| LaMa | `#2F6FB5` | 圆 |
| MAT | `#7FB2E0` | 方 |
| PowerPaint v1 | `#D9952B` | 三角 |
| SDXL Inpainting | `#8A6FAE` | 菱形 |

画作缩略图上的叠加色（漏掉的像素）用 `#D04848`，不透明度 85%，外加 0.5 px 白描边，保证在深色和浅色画面上都看得清。

**字体与尺寸**
- Arial（没有就用 Helvetica），不用中文字体。
- 最终尺寸下，正文 7–8 pt，栏标题 9 pt 粗体，分图标签 (a)(b)(c) 10 pt 粗体。
- **PowerPoint 的幻灯片尺寸直接设成成图尺寸**：双栏 17.4 cm 宽，单栏 8.5 cm 宽。这样 PPT 里的字号就是印刷字号，不会缩放。

**线条与形状**
- 线宽 0.75 pt，箭头 1 pt；圆角矩形的圆角统一。
- 不用阴影、3D、渐变和艺术字。

**图片**
- 嵌入原尺寸 PNG（至少 300 dpi 等效），不拉伸变形；所有缩略图边长一致，并对齐网格。

**文字**
- 图里只写短语，不写句子。
- 数字只放最关键的 1–2 个，其余放图注。

## 3. 图 1：teaser（PowerPoint，双栏 17.4 × 约 7 cm）

**核心信息**：三个很少被报告的协议细节会大幅改变测得的误差；在控制它们的协议下，四个模型的排序在两馆、四类画作、六种破损中一致。

注意措辞：底栏不能写成"控制后才一致"。我们的数据是这三项改变了误差大小，没有改变排序。

布局为上面三栏、下面一条底栏。三栏等宽，栏间留 3 mm，每栏顶上一行标题。

### (a) 掩码怎样进入模型：*What the model is asked to fill*
- **元素**：同一个 1% 裂缝例子，并排三块（每块约 1.8 cm 见方）。
  1. 画作裁片放大块，原掩码用白色半透明叠加。
  2. 8×8 最邻近取样后的覆盖：覆盖到的像素用绿色，**漏掉的用砖红**，背景画出浅灰网格线。
  3. 整格扩张后：全部覆盖，扩张多出的格子用浅绿。
- 三块之间用箭头连接，箭头上写 "8× downsample" 和 "grid-aligned"；第 2 块放在浅蓝底块上，表示潜空间。
- **标注数字**："59.5% of crack pixels missed"（60 幅，1% 裂缝）；栏底一行小字："PowerPaint MAE −45% after alignment"。
- **图片来源**：用 FIGURES.md 里图 4（原图 3）的 1% 裂缝选例，选例规则不变；覆盖图由脚本导出透明底 PNG。

### (b) 洞里先填什么：*What fills the hole first*（SDXL，strength 0.99）
- **元素**：左边是同一个洞的三种预填充色块，即黑、中灰、洞外环带均色，各配一个小方块。
- 中间一个"扩散模型"图标块，标 "SDXL, strength 0.99"。
- 右边是三张对应的输出缩略图，下方各标亮度偏移：−0.085 / +0.055 / +0.034。
- 黑色那一行用砖红边框标出，表示"变暗"。
- **图片来源**：SDXL_PREFILL 原尺度 16 幅中，按固定规则（同一盐值、按条件 ID 的 SHA-256 排序取第一个）选一个条件，三种颜色用同一个条件，不挑效果最好的。

### (c) 谁被算进分母：*Which outputs get scored*（PowerPaint v1 安全检查）
- **元素**：两个方块图（waffle chart），每个 360 个小方格，排成 18 × 20。
  - 克利夫兰：281 格灰色，79 格砖红。
  - 芝加哥：350 格灰色，10 格砖红。
- 两个方块图上方各放一个盾牌图标，标 "safety checker"；下方标馆名缩写 "CMA 78%" 和 "AIC 97%"。
- 方块图用 PowerPoint 原生小方格生成（python-pptx 可以批量画），不要贴图。

### (d) 底栏：*Under the controlled protocol*
- **元素**：
  - 一排四个模型色块，按 LaMa ≈ MAT < PowerPaint v1 < SDXL 排；"≈" 和 "<" 用大号符号。
  - 右侧三组小图标加数字："2 museums"（博物馆建筑图标）、"4 media"（画架、木板、水彩笔、毛笔图标）、"6 loss conditions"（裂缝图标）。
- 底块用浅绿 `#E2F0D9`，表示"已控制"。

## 4. 图 2：方法流程图（PowerPoint，双栏 17.4 × 约 6 cm）

从左到右六个模块，每个模块一个圆角矩形，加一个图标和一行短语。

1. **Open-access cohorts**：博物馆图标 ×2，写 "CMA 60 + AIC 60, 4 media × 15"。
2. **512 crop + 6 masks**：一张裁片缩略图，旁边 2×3 的小掩码缩略图（裂缝、剥落、缺失，1% 和 5%）。
3. **Shared input**：裁片加扩张掩码的缩略图，标 "8×8-aligned aperture"。
4. **Four pinned models**：两个底块，米灰（像素空间）放 LaMa、MAT，浅蓝（潜空间）放 PowerPaint v1、SDXL。模型名用第 2 节的模型色。旁边放 GPU 图标，标 "RTX 3090, seed 2026"。
5. **Composite in original hole**：输出缩略图，原洞轮廓用细虚线。
6. **Score + ledger**：上半部分是四个指标标签（MAE、ΔE₀₀、LPIPS、DISTS）；下半部分是一个"台账"小表，三行 planned / scored / withheld。
- 模块 1–6 上方贯穿一条细时间线，起点放锁图标，写 "protocol committed before inference"。
- 图 1 已经讲过的三个细节，在这里只用砖红小圆点标出所在模块（a 在模块 3，b 在模块 4，c 在模块 6），不再展开。

## 5. 数据图（脚本生成，套用第 2 节的配色和字体）

先写一个共用的 Matplotlib 样式文件 `experiments/paper_style.mplstyle`，定义字体、字号、线宽和模型颜色，所有数据图都用它。

- **图 3：示例对比**。行是三个案例（裂缝、剥落、缺失），列依次为原图、掩码、LaMa、MAT、PowerPaint、SDXL。列标题用模型色的小色条加名字；每格右下角标该格 MAE；放大框统一用细白边。可以在 PowerPoint 里排版，图块由脚本导出。
- **图 4：漏覆盖示意**。三种 1% 破损，配色同图 1(a)。
- **图 5：按破损条件的误差**。用**点加 95% 区间的点图**，不用柱状图。横轴为六种条件，左右两个面板分别是两馆；纵轴用对数刻度，因为 SDXL 比其他模型高一个数量级；也可以给 SDXL 单独开一个小面板。
- **图 6：可用率**。横向条形图，两馆 × 四类画种，砖红部分表示被拦截，条上写 "55/90" 这类计数。

## 6. 图标

从开源、可商用、**不要求署名或许可宽松**的图标库下载 SVG。优先顺序：

1. [Tabler Icons](https://tabler.io/icons)（MIT）
2. [Lucide](https://lucide.dev)（ISC）
3. [Material Symbols](https://fonts.google.com/icons)（Apache-2.0）
4. [Phosphor Icons](https://phosphoricons.com)（MIT）

可以通过 [Iconify](https://icon-sets.iconify.design) 统一检索，但下载时要确认图标来自上面这几套。全图只用**一套**图标库，保证线宽和风格一致，首选 Tabler，缺的再从 Lucide 补。

**不要用**：Flaticon、Noun Project（需要署名或付费）；博物馆的 logo（商标）；AI 生成的图标。

**要找的图标**（括号里是建议关键词）：
- 博物馆（building-bank / landmark）、画架（easel）、木板（wood / panel）、水彩笔（brush）、毛笔（brush / pen-tool）、裂缝（bolt / cracked）
- 网格（grid-dots / layout-grid）、扩散模型（sparkles / wand）、盾牌（shield / shield-x）、锁（lock）
- GPU（cpu）、骰子（dice，表示种子）、表格（table）、对勾和叉（check / x）

**处理方式**
- SVG 统一改成深灰蓝 `#383848`，强调时用第 2 节的颜色，线宽统一 1.5 px。
- python-pptx 不能直接插入 SVG，先用 cairosvg 或 Inkscape 转成 600 dpi 透明 PNG 或 EMF 再插入。
- 原始 SVG 放进 `docs/paper/figures/icons/`；在 `docs/paper/figures/ICONS.md` 里逐个记录来源链接、图标名和许可证。

## 7. 交付与流程

1. **先出草图**：用 PowerPoint 只摆方框、占位缩略图和文字，导出低分辨率预览 PNG，放进 `docs/paper/figures/previews/`（进 Git，每张不超过 1 MB），开 PR 等 Claude 审查布局，确认后再做精修。这对应彭老师流程的第 1 步"先画草图"。
2. **精修版**交付以下内容：
   - `docs/paper/figures/figure-1-teaser.pptx`、`figure-2-pipeline.pptx`（进 Git，每个不超过 5 MB）；
   - 导出的 PDF（`soffice --headless --convert-to pdf`）和 300 dpi PNG 预览，都留在服务器；
   - 生成 PPT 的脚本 `experiments/make_ppt_figures.py`；
   - `ICONS.md`。
3. **自查**：
   - 字号在成图尺寸下不小于 7 pt；
   - 灰度打印时三种强调色仍能区分；
   - 所有数字与报告一致（列出来源）；
   - 图 1 每一栏都能单独说清一件事；
   - 用 PDF 而不是 PPT 截图来检查。
4. **最后的美化由 Claude 做**（作者决定）。Claude 会直接用 python-pptx 调整 `.pptx` 的构图、间距和配色，用 LibreOffice 导出 PDF 检查，再提 PR。所以 `.pptx` 里每个元素要分组、按"栏-元素"命名（如 `a-mask-original`、`c-waffle-cma`），不要把多个元素合成一张图片。
