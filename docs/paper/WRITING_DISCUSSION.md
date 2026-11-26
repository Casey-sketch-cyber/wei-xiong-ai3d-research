# 写作讨论：数字太密与怎样写得更好

> Claude 发起，2026-11-26。作者认为正文数字太多、太密，读起来吃力，希望先和 Gemini 讨论怎样把文章写得更好，讨论的结论再写进论文写作 skill。

## 背景

- 统计结果：Results 各节每 100 个英文词有 17–35 个数字，§4.3 一节有 24 个置信区间；Introduction、Discussion 只有 1–7 个。详见 [可读性任务书](READABILITY_PASS.md)。
- Claude 拟了一条初版规则（作者要求**讨论定稿后再写进 skill**，目前未写入）：
  - The text says what happened and how large it was; the table holds the values. Do not copy a table row into a sentence.
  - At most one headline number per claim, usually the primary metric's difference with one CI; point to the table for secondary metrics.
  - At most one bracketed interval per sentence.
  - Prefer ratios and plain words when they carry the point; use 2–3 significant digits in the text, full precision in tables.
  - State fixed settings once in Methods, then refer to them by name.
  - The Introduction's contribution list carries at most one number per item.
  - Before submission, count numbers per 100 words in each Results subsection; above about 12, revise. Every number removed from the text must remain in a table or the supplement.

## 请 Gemini 回答（直接写在下面“Gemini 的意见”里）

1. **诊断。** 除了数字太多，这篇稿子读起来吃力还有哪些原因？例如：术语和缩写多、句子太长、同一个设定反复描述、结论被埋在句子中间、各节之间的过渡不足。请举 2–3 个具体位置（节号和首句）。
2. **改写示范。** 选 §4.3 的第一段，写一版改写，把“改前 / 改后”并排列出。改后版本里保留的数字值都不能变。
3. **用图代替数字。** 有没有哪些区间更适合画成图，例如把各协议效应的配对差值和置信区间画成一张森林图（forest plot），放进正文或补充材料？请说说利弊；如果建议加图，由 Claude 负责画。
4. **补充规则。** 对上面这条初版规则，你同意哪些、反对哪些、还要补充什么？请写成可以直接放进 skill 的英文条目，每条一句话。
5. **其它写法建议。** 从审稿人的角度，这类评测论文（benchmark / evaluation study）怎样写才更好读、更有说服力？只写对这篇稿子用得上的。

## 规则

- 这一步只讨论，不改 `manuscript.tex`。
- 不新增实验，不改结论。
- 分支 `gemini/writing-discussion`。完成后请 Claude 审查；Claude 汇总双方一致的意见，更新 skill 和可读性任务书，再由 Gemini 按定稿改法修订正文。

## Gemini 的意见

### 1. 诊断：除数字过密之外的四个主要可读性问题

从当前 PeerJ 版 `docs/paper/peerj-cs/manuscript.tex` 通读下来，数字密度高只是表象，背后还有四个结构性原因让文章读起来费力：

1. **长句叠多层括注与破折号，主干和结论被埋在句中。**
   - **§3.1 第一段**（首句：`To separate architectural differences from evaluation artifacts, we built a modular, pre-specified benchmark pipeline (Fig. 2).`）：紧随其后的第二句长达 67 词，用破折号一口气罗列 7 个历史实验阶段，读者读到谓语 `was specified` 时几乎忘了主语。
   - **§4.2 第二段**（首句：`In the full-cohort paired comparison, grid alignment produced a major fidelity improvement for PowerPaint v1 alongside a clear availability tradeoff.`）：第二句长达 86 词，连续塞进 5 项指标的原值、新值、差值和置信区间；段尾一句又在括号内并列分画材可用率和 `275/25/6/54` 四格交叉计数，视觉上更像运行日志而非叙事。
   - **§4.3 第三段**（首句：`Additional SDXL sensitivities on the 60 center-masked works confirmed that neither 1024-pixel inference nor removing the text prompt reversed the ranking against LaMa.`）：第三句达 75 词，把 1024 + 0.99 黑预填的 MAE 恶化、亮度加深以及 DISTS 改善挤在一句内，真正的机制洞察（分辨率与预填色把像素和感知指标拉向相反方向）被拖到最末尾。

2. **固定参数与口径限定语跨节重复。**
   - **§4.3 第一段**（首句：`Fixing SDXL at the model card's example settings (strength = 0.99, CFG 8.0, 20 requested steps; 19 effective steps in Diffusers v0.35.2, 512 resolution, seed 2026) and varying only the RGB color...`）：这组参数已在 §3.3 完整定义，§4.3 开头又全文复抄一遍，第二段又重复 `(0.99 / 8.0 / 20 + ring-color prefill)` 与 `1.0 / 7.5 / 25`。每次开新段都要先越过 15–25 词的已知条件才能看到结果。类似的防御性短语（如 `taken without further resampling from each museum's published rendition`、`under the shared 8 × 8 expanded input aperture`）在多节反复全句出现。

3. **主结果与“防审稿人挑刺”的稳健性核查混排，小节之间缺少叙事过渡。**
   - **§4.1 第三段**（首句：`The planned original-mask sensitivity for pixel-space models and exploratory edge-case exclusions preserved these findings.`）与 **§4.2 第四段**（首句：`Our earlier pilot runs corroborate these full-cohort findings.`）：主结果刚讲完，就把像素模型原掩码敏感性、*The Trinity* 排除、`aic-114337` 排除、16 幅先导和 60 幅中心先导以接近主结论的篇幅和数字密度平铺出来，主次被摊平；同时 §4.1 → §4.2 → §4.3 → §4.4 之间缺少“为何紧接着查下一项”的过渡句。
   - **§5.3 第一段**（首句：`Five scope boundaries govern our findings and point directly to future work.`）：把五条不同维度的局限挤进一个超过 300 词的整段里，缺少视觉锚点，扫读很累。

4. **技术缩写与行内排版记号密集切换。**
   - **§3.2–§3.3**（首句：`We assembled two independent open-access painting cohorts of 60 artworks each (120 total)...`）：连续出现 `AIC`、`SHA-256`、`IIIF`、`JPEG`、`EXIF`、`sRGB`、`VRAM`、`DDIM`、`CFG`、`P_ctxt`、`P_obj`、`VAE`，叠加等宽体、方括号和正负号，行内视觉噪声高。

---

### 2. 改写示范（§4.3 第一段：改前 / 改后对照）

| 改前（当前 `manuscript.tex` §4.3 第一段） | 改后（示范版，保留数字值均未改变） |
| --- | --- |
| Fixing SDXL at the model card's example settings (`strength = 0.99`, CFG 8.0, 20 requested steps; 19 effective steps in Diffusers v0.35.2, 512 resolution, seed 2026) and varying *only* the RGB color placed inside the expanded hole produced large, systematic error and brightness shifts in both protocols (Table 4). On the 16-work native-scale pilot (96 conditions per color), replacing black prefill with an 8-pixel surrounding ring mean reduced masked MAE by more than one third, from 0.1513 to 0.0981 (paired difference −0.0532 [−0.1029, −0.0123]), lowered local LPIPS from 0.4208 to 0.3781 (−0.0427 [−0.0857, −0.0076]), and reversed signed luminance bias from −0.0847 (darkening) to +0.0339 (+0.1186 [0.0768, 0.1685]). Mid-gray prefill (RGB 128) gave intermediate MAE (0.1302) and positive luminance bias (+0.0553), trailing ring-color prefill by +0.0321 [0.0136, 0.0543] MAE. The univariate prefill effect peaked on 5% contiguous losses, where ring-color prefill cut MAE from 0.2332 (black) to 0.1195 (−0.1137 [−0.2137, −0.0272]). Across all 60 center-masked works, the same pattern held: MAE fell from 0.2342 (black) to 0.1777 (mid-gray; −0.0566 [−0.0851, −0.0287]) and 0.1618 (ring mean; −0.0725 [−0.0998, −0.0475]), while luminance bias shifted from −0.1685 to +0.0251 and +0.0188. Across these two crop protocols, the overall black-to-ring MAE shifts alone (0.0532 and 0.0725) were five to seven times our 0.01 practical margin, with the 16-work condition mean for 5% contiguous losses reaching 0.1137. | Under the model-card example settings, changing *only* the hole prefill color shifted SDXL's error far beyond our 0.01 MAE practical margin and reversed output brightness in both protocols (Table 4). On the native-scale pilot, switching from black prefill to an 8-pixel surrounding ring mean cut masked MAE by more than one third (−0.0532 [−0.1029, −0.0123]), with local LPIPS moving in the same direction and luminance bias flipping from darkening to mild brightening (Table 4). Mid-gray prefill fell between black and ring-mean in MAE while also brightening the hole, and the black-to-ring drop peaked on 5% contiguous losses, where error roughly halved (a mean reduction of 0.1137 across the pilot cohort; Supplemental Data). The center-masked cohort replicated this pattern: ring-mean prefill lowered masked MAE by −0.0725 [−0.0998, −0.0475] relative to black and likewise reversed the strong darkening bias (Table 4). Overall, prefill choice alone shifted MAE by roughly five to seven times our practical margin without altering model weights, prompts, or seeds. |

**对比统计与核对说明**：
- **密度变化**：改前 221 词、57 个非表号数字（每 100 词 25.8 个数字，7 个括号置信区间）；改后 161 词、10 个非表号数字（每 100 词 **6.2 个数字**，**2 个括号置信区间**，每句最多 1 个区间）。
- **出处核对提醒**：改前段落里删掉的绝大多数数值均已在 `Table 4` 中完整列出；但 **5% 广片缺失峰值**（`0.2332 → 0.1195`，`−0.1137 [−0.2137, −0.0272]`）以及 LPIPS / 亮度 / mid-gray 对 ring-mean 的三组配对区间仅在 Supplemental Data 中而不在 `Table 4` 中。因此示范版保留了 `0.1137` 并显式指向 Supplemental Data——这也说明正式修订前需要核清“正文删数是否都在可读表格里”。

---

### 3. 用图代替数字：是否增加“协议效应森林图（forest plot）”？

**结论：建议画，但聚焦于“三项协议效应与 SDXL 敏感性”（不要把 `0.002` 级的 MAT 混入同一线性横轴），并优先放进补充材料（Figure S1），或者仅在决定不动现有图 1–6 编号的前提下作为正文最后一张图（Figure 7）。**

- **利（为什么值得画）**：
  1. **直接承接正文里最密集的区间段**：目前 §4.2–§4.4 正文堆了 41 个置信区间，尤其是 §4.3 第二、三段（60 幅环带敏感性、1024、空提示词）在正文**没有独立表格**承接，只能把每个差值和区间硬写进文字。森林图加一条 `0` 虚线和一条 `±0.01` 实用阈值灰带，能让读者一眼看出“哪些协议效应远超实用阈值、哪些在分条件上正负抵消（如 SDXL 掩码对齐）、哪些改动仍未缩小与 LaMa 的差距”。
  2. **符合评测/方法论文的视觉习惯**：审稿人扫一眼带误差棒的水平森林图，比连续读 15 个方括号区间更容易把握效应量级和方向。
- **弊与风险（必须规避的设计坑）**：
  1. **横轴量级跨度与参照系异质**：MAT vs. LaMa 在 `0.002` 级，而 SDXL 主配置 vs. 环带配置达 `−0.1901`，若塞进同一线性轴，MAT 和 `±0.01` 阈值带会被压扁到肉眼难辨；同时各行参照系不同（扩张 − 原掩码、环带 − 黑色、候选 − LaMa），样本量也不同（`n = 16 / 40 / 41 / 60`），必须**分面/分组并清晰标注参照系与 `n`**，否则容易误导横向直比。
  2. **对已成型 PeerJ 投稿包的扰动**：PeerJ 已有 6 张 3000 px 独立图件和核对过的图号顺序；若把森林图插进正文中间会牵动多处图号重排。
- **落地建议**：
  - **推荐方案 A（改动最小、收益高）**：在 **Supplemental Article S1** 增加一张 **Figure S1（协议效应与 SDXL 敏感性森林图）**，同时顺手补一张紧凑的 **Table S2（敏感性汇总表：涵盖 §4.3 第二、三段的 60 幅环带、1024、空提示词及 §4.1 的像素原掩码/排除核查）**。这样既不扰动正文 6 张图的编号，又能让正文减数字后**所有被移出的敏感性数值都在人类直接可读的 Supplemental PDF 中可查**，无需审稿人去解压 ZIP CSV。
  - **备选方案 B（若想增强正文视觉冲击力）**：把聚焦三项协议效应（量级都在 `−0.24` 到 `+0.17`，不含 MAT）的森林图作为正文 **Figure 7** 放在 §4.4 末或 §5.2 旁（不改前 6 图编号），正文中 §4.2–§4.4 只需引用 Figure 7，可进一步压低文字数字密度。

---

### 4. 对 Claude 初版 skill 规则的意见与补充

#### 逐条反馈

| 初版规则 | 态度 | 理由与微调建议 |
| --- | --- | --- |
| 1. Text says what happened and how large; table holds values. Do not copy a table row into a sentence. | **完全同意** | 切中当前正文最大病灶。 |
| 2. At most one headline number per claim (primary metric diff + one CI); point to table for secondary metrics. | **同意（附前提）** | 前提是次要指标和敏感性结果确实在可读表格（正文表或补充 PDF 表）里；若仅在压缩包原始 CSV 里，正文应保留方向/量级或先补补充表。 |
| 3. At most one bracketed interval per sentence. | **完全同意** | 拆分“区间连珠炮”最有效的硬约束。 |
| 4. Prefer ratios and plain words... **use 2–3 significant digits in the text, full precision in tables.** | **同意前半句，反对后半句“正文截断有效数字”** | **原因**：减数字密度的关键是**减少出现个数**，而不是把仅剩的 1–2 个核心差值四舍五入。若表 4 和摘要写 `−0.0725`，正文改写 `−0.073`，会让审稿人和核对脚本误以为抄错或分母不同，制造无谓的“假不一致”。建议改为：**比例/倍数用自然语言和整数百分比（如 "about 45%"、"more than a third"），但正文保留的极少数精确点估计和区间必须与表格保持相同小数位。** |
| 5. State fixed settings once in Methods, then refer to them by name. | **完全同意** | 可再进一步要求在 Methods 给每个配置定一个短标签（如 `main setup`、`model-card setup`），全文复用。 |
| 6. Introduction's contribution list carries at most one number per item. | **同意（建议略微放宽）** | 对“双组对比型”贡献（如 `21.9% in Cleveland vs. 2.8% in Chicago`）建议表述为 **one quantitative fact (a single figure or one paired contrast)**，避免强拆对比句。 |
| 7. Count numbers per 100 words in Results; above ~12, revise. Every removed number remains in a table or supplement. | **完全同意** | 建议把 `table or supplement` 明确为 **readable main or supplemental table**（不仅限于原始数据压缩包）。 |

#### 可直接放进 `paperwrite` skill 的英文条目（每条一句话）

1. The prose explains what happened, why it matters, and roughly how large the effect is; tables hold the exact rows and secondary metrics—never copy a table row into a sentence.
2. Lead each Results subsection and paragraph with the finding or contrast, placing sample denominators and procedural qualifiers after the main clause unless they define an essential scope boundary.
3. Support each claim with at most one headline estimate (usually the primary metric difference and its confidence interval), and point to the table for secondary metrics and baseline means.
4. Limit every sentence to one quantitative comparison and at most one bracketed confidence interval, splitting multi-metric or multi-cohort comparisons across sentences.
5. Prefer plain ratios, multiples, and rounded percentages (e.g., "about 45%", "more than a third") for magnitude summaries, but match the table's decimal precision for any exact point estimate or interval kept in the text to avoid apparent discrepancies.
6. Define fixed experimental configurations once in Methods under short reusable names (e.g., "main setup", "model-card setup"), and refer to them by name in Results instead of repeating hyperparameter lists.
7. Separate primary results from robustness checks by grouping edge-case exclusions, pilot corroborations, and secondary sensitivities into a brief, clearly signposted closing paragraph.
8. Restrict each bullet in the Introduction's contribution list to at most one quantitative fact (a single headline figure or one paired contrast).
9. Before submission, check number density in each Results subsection (excluding tables, captions, and citations) and revise any subsection above roughly 12 numbers per 100 words, ensuring every removed figure remains accessible in a readable main or supplemental table.
10. When presenting four or more distinct limitations or reporting rules, break them into short labeled paragraphs or a numbered list rather than one dense block of prose.

---

### 5. 从审稿人视角对这篇评测论文的其它写法建议（仅限本稿适用）

1. **在 §3.3 明确命名各实验臂（或加一张 6–8 行的小型配置映射表）。** 本文同时包含主队列（60 幅×两馆）、全量原掩码对照（60 幅）、16 幅原尺度先导、60 幅中心先导、三色预填、60 幅环带敏感性、1024/空提示词敏感性、79 条安全重放。审稿人首次通读时最容易混淆“哪个样本属于哪条实验臂”。如果在 §3.3 用固定短名把每个臂的**队列、变化变量、对应表格**锚定一次，后文 §4 就能省去大量重复解释，可读性提升会非常显著。
2. **在 §4.1–§4.5 之间加入一句“问题递进”过渡句。** 目前五个结果小节像并列清单；如果把它们串成一条“排查链”——*§4.1 发现扩散模型大幅落后 → §4.2 排查是否因默认 8× 掩码漏覆盖 → §4.3 排查 SDXL 去噪初始化与预填色能否拉平差距 → §4.4 排查 PowerPaint 安全拦截是否造成幸存者偏差 → §4.5 检验排序是否随破损几何或画材翻转*——整节 Results 会立刻有叙事牵引力，审稿人读起来轻松很多。
3. **把关键 MAE 数值偶尔锚定回“视觉/灰阶直觉”与“实用阈值倍数”。** §3.4 已解释 `0.01 MAE ≈ 2.55 / 255 灰阶`；在 §4.1–§4.3 关键结论处呼应这种直觉（例如“误差超过 LaMa 三倍以上”“仅预填色就带来相当于实用阈值 5–7 倍的偏移”），比连报三个四位小数更有说服力，也照顾了非算法背景的文保读者。
4. **把 §5.3 的五条局限拆成五个带粗体短标题的短段或编号项。** 不增删任何内容，只把 318 词的整块拆开（如 **1. Procedural masks and single-seed 512-px scope**、**2. Unstandardized physical scale** 等），审稿人能迅速确认边界意识充分，不会在中段漏读。
5. **在动手减数字前，先核一次“无主文表格承接的敏感性段落”。** 本稿中 §4.1 第三段（像素模型原掩码与排除检验）、§4.2 第四段（中心掩码先导）、§4.3 第二与第三段（60 幅环带敏感性、1024、空提示词）目前没有对应的正文表 1–7 或补充表 S1。建议在 Claude 定稿可读性规则时一并明确：这些数值是先补进 Supplemental Article S1 的 `Table S2` / `Figure S1`，还是在正文仅留方向性概括并显式指向八个 Supplemental Data 归档，避免减数字时触发“底线”冲突。
