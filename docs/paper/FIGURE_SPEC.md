# 论文配图设计说明

> 给 Codex 的配图任务书，Claude 起草于 2026-11-21。先读完全文再动手。正文图注由 Gemini 按本说明重写。

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
| 结果网格每列一个方法、每行一个案例，列标题在顶上，放大框标出细节 | 补全论文的定性对比图（LaMa、MAT、PowerPaint 等） | 图 3 |

动手前，Codex 先找出上面三篇论文的对应图，各截一张缩略图，放在服务器的 `paper/figure-refs/`（不进 Git），作为风格参考。

## 2. 全文统一的视觉规范

**配色**：用 Okabe–Ito 色盲友好色板，每种颜色只表示一种含义，全文所有图一致。

| 含义 | 颜色 | 色值 |
| --- | --- | --- |
| LaMa | 蓝 | `#0072B2` |
| MAT | 天蓝 | `#56B4E9` |
| PowerPaint v1 | 橙 | `#E69F00` |
| SDXL Inpainting | 紫 | `#CC79A7` |
| 问题：漏掉的像素、被拦截的条件、偏差 | 朱红 | `#D55E00` |
| 修正后：整格扩张、可评分 | 绿 | `#009E73` |
| 像素空间底块 | 暖灰 | `#F3EEE7` |
| 潜空间底块 | 冷灰蓝 | `#E6EEF5` |
| 文字 / 线条 / 次要元素 | 深灰 / 中灰 | `#333333` / `#8C8C8C` |

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
  2. 8×8 最邻近取样后的覆盖：覆盖到的像素用绿色，**漏掉的用朱红**，背景画出浅灰网格线。
  3. 整格扩张后：全部覆盖，扩张多出的格子用浅绿。
- 三块之间用箭头连接，箭头上写 "8× downsample" 和 "grid-aligned"；第 2 块放在冷灰蓝底块上，表示潜空间。
- **标注数字**："59.5% of crack pixels missed"（60 幅，1% 裂缝）；栏底一行小字："PowerPaint MAE −45% after alignment"。
- **图片来源**：用 FIGURES.md 里图 4（原图 3）的 1% 裂缝选例，选例规则不变；覆盖图由脚本导出透明底 PNG。

### (b) 洞里先填什么：*What fills the hole first*（SDXL，strength 0.99）
- **元素**：左边是同一个洞的三种预填充色块，即黑、中灰、洞外环带均色，各配一个小方块。
- 中间一个"扩散模型"图标块，标 "SDXL, strength 0.99"。
- 右边是三张对应的输出缩略图，下方各标亮度偏移：−0.085 / +0.055 / +0.034。
- 黑色那一行用朱红边框标出，表示"变暗"。
- **图片来源**：SDXL_PREFILL 原尺度 16 幅中，按固定规则（同一盐值、按条件 ID 的 SHA-256 排序取第一个）选一个条件，三种颜色用同一个条件，不挑效果最好的。

### (c) 谁被算进分母：*Which outputs get scored*（PowerPaint v1 安全检查）
- **元素**：两个方块图（waffle chart），每个 360 个小方格，排成 18 × 20。
  - 克利夫兰：281 格灰色，79 格朱红。
  - 芝加哥：350 格灰色，10 格朱红。
- 两个方块图上方各放一个盾牌图标，标 "safety checker"；下方标馆名缩写 "CMA 78%" 和 "AIC 97%"。
- 方块图用 PowerPoint 原生小方格生成（python-pptx 可以批量画），不要贴图。

### (d) 底栏：*Under the controlled protocol*
- **元素**：
  - 一排四个模型色块，按 LaMa ≈ MAT < PowerPaint v1 < SDXL 排；"≈" 和 "<" 用大号符号。
  - 右侧三组小图标加数字："2 museums"（博物馆建筑图标）、"4 media"（画架、木板、水彩笔、毛笔图标）、"6 loss conditions"（裂缝图标）。
- 底块用很浅的绿，表示"已控制"。

## 4. 图 2：方法流程图（PowerPoint，双栏 17.4 × 约 6 cm）

从左到右六个模块，每个模块一个圆角矩形，加一个图标和一行短语。

1. **Open-access cohorts**：博物馆图标 ×2，写 "CMA 60 + AIC 60, 4 media × 15"。
2. **512 crop + 6 masks**：一张裁片缩略图，旁边 2×3 的小掩码缩略图（裂缝、剥落、缺失，1% 和 5%）。
3. **Shared input**：裁片加扩张掩码的缩略图，标 "8×8-aligned aperture"。
4. **Four pinned models**：两个底块，暖灰（像素空间）放 LaMa、MAT，冷灰蓝（潜空间）放 PowerPaint v1、SDXL。模型名用第 2 节的模型色。旁边放 GPU 图标，标 "RTX 3090, seed 2026"。
5. **Composite in original hole**：输出缩略图，原洞轮廓用细虚线。
6. **Score + ledger**：上半部分是四个指标标签（MAE、ΔE₀₀、LPIPS、DISTS）；下半部分是一个"台账"小表，三行 planned / scored / withheld。
- 模块 1–6 上方贯穿一条细时间线，起点放锁图标，写 "protocol committed before inference"。
- 图 1 已经讲过的三个细节，在这里只用朱红小圆点标出所在模块（a 在模块 3，b 在模块 4，c 在模块 6），不再展开。

## 5. 数据图（脚本生成，套用第 2 节的配色和字体）

先写一个共用的 Matplotlib 样式文件 `experiments/paper_style.mplstyle`，定义字体、字号、线宽和模型颜色，所有数据图都用它。

- **图 3：示例对比**。行是三个案例（裂缝、剥落、缺失），列依次为原图、掩码、LaMa、MAT、PowerPaint、SDXL。列标题用模型色的小色条加名字；每格右下角标该格 MAE；放大框统一用细白边。可以在 PowerPoint 里排版，图块由脚本导出。
- **图 4：漏覆盖示意**。三种 1% 破损，配色同图 1(a)。
- **图 5：按破损条件的误差**。用**点加 95% 区间的点图**，不用柱状图。横轴为六种条件，左右两个面板分别是两馆；纵轴用对数刻度，因为 SDXL 比其他模型高一个数量级；也可以给 SDXL 单独开一个小面板。
- **图 6：可用率**。横向条形图，两馆 × 四类画种，朱红部分表示被拦截，条上写 "55/90" 这类计数。

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
- SVG 统一改成深灰 `#333333`，强调时用第 2 节的颜色，线宽统一 1.5 px。
- python-pptx 不能直接插入 SVG，先用 cairosvg 或 Inkscape 转成 600 dpi 透明 PNG 或 EMF 再插入。
- 原始 SVG 放进 `docs/paper/figures/icons/`；在 `docs/paper/figures/ICONS.md` 里逐个记录来源链接、图标名和许可证。

## 7. 交付与流程

1. **先出草图**：用 PowerPoint 只摆方框、占位缩略图和文字，导出 PNG。在 PR 里贴出来，等 Claude 和作者确认布局，再做精修。这对应彭老师流程的第 1 步"先画草图"。
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
4. 作者主业是绘画，精修后可能会在 PowerPoint 里亲自调整构图和配色。所以 `.pptx` 里每个元素要分组、命名，方便手动编辑。
