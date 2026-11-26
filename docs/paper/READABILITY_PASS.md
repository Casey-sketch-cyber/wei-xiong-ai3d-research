# 可读性修订：减少正文里的数字

> Claude 起草，2026-11-26。作者反映正文数字太多、太密，读起来吃力。这一轮只改 `docs/paper/peerj-cs/manuscript.tex` 的行文，不改结论、表格和补充材料。

## 问题有多大

按节统计了每 100 个英文词里有多少个数字（表格和图注不计）：

| 部分 | 每 100 词的数字数 | 置信区间个数 |
| --- | --- | --- |
| Introduction、Related Work、Discussion、Conclusions | 1–7 | 0 |
| §3 Pinned models / Metrics | 9–10 | 0–2 |
| §4.1 Model rankings | 24 | 14 |
| §4.2 Mask under-coverage | 35 | 12 |
| §4.3 Prefill | 35 | 24 |
| §4.4 Safety checker | 25 | 5 |
| §4.5 Rankings by damage and medium | 17 | 2 |

Results 部分大约每三个词就有一个数字，置信区间一个接一个，而且多数数字表 1–7 里已经有了。比如 §4.3 第二段，在正文里逐个列出了五个指标的差值、区间和前后值。

## 第 0 步：讨论（已完成）

Gemini 已在 [`WRITING_DISCUSSION.md`](WRITING_DISCUSSION.md) 回答，Claude 汇总定稿（见该文件末尾“汇总与定稿”）。下面的改法已按讨论结果修订。

## 第 1 步：先补补充表（Codex，在 Gemini 删数字之前）

Gemini 指出，这些段落里的数字目前既不在表 1–7，也不在补充表 S1 里，只在 Supplemental Data 的压缩包中：§4.1 第三段（像素模型原掩码敏感性与两项排除）、§4.2 第四段（先导实验）、§4.3 第二、三段（60 幅环带敏感性、1024、空提示词），以及 §4.3 的 5% 广片缺失峰值和 LPIPS / 亮度 / mid-gray 三组配对区间。

请 Codex 从冻结的运行结果生成 **Table S2：敏感性与先导汇总**，放进 Supplemental Article S1。每行写明参照系、比较对象、n、主指标差值与 95% 区间，次要指标另列几栏。另外导出同样内容的小 CSV（`docs/paper/peerj-cs/figdata/protocol_effects.csv`，汇总数字可以入 Git），供 Claude 画 Figure S1 用。Table S2 合并以后，Gemini 才能删这些段落里的数。

## 改法（Gemini）

1. **每个结论在正文里最多给一个核心数字。** 一般是主指标 MAE 的差值，配一个 95% 置信区间。其余指标（LPIPS、DISTS、ΔE00、前后原值）改写成“见表 X”，或者用一句定性话概括，例如 “LPIPS, DISTS and ΔE00 moved in the same direction (Table 4)”。
2. **正文不再重复表里已有的数。** 正文负责讲“发生了什么、有多大”，具体数值留在表里。
3. **能用比例、倍数说清楚的，就不用四位小数。** 例如 “reduced masked MAE by about a third”“five to seven times the 0.01 margin”。**正文保留的精确数值，小数位与表格一致**，不截位，以免和表格看起来对不上（采纳 Gemini 意见）。差值写成 “lowered masked MAE (−0.0725 [−0.0998, −0.0475])”，不要写成 “lowered by −0.0725”。
4. **每个 §4.x 小节第一句就是结论**（小节标题已经是结论，可以与标题呼应），后面的句子再给证据。
5. **一句话最多放一个括号区间。** 两组对照的区间不要串在同一句里。
6. **§3 方法里的设定参数集中到一处。** 例如 SDXL 的 strength / CFG / 步数 / 分辨率 / 种子，统一放在 §3.3 第一次出现的地方；后文改写成 “the model-card example settings”，不再逐项重复。
7. **Introduction 的贡献列表**每条最多一个数量事实：一个数字，或者一组成对对比（如 21.9% vs 2.8%），不要把摘要里的数字再抄一遍。
9. **拆长句。** 一句话超过 40 个词、或者带两层以上括注和破折号的，拆开写。Gemini 点名的几处要先改：§3.1 第二句、§4.2 第二段第二句、§4.3 第三段第三句。
10. **在 §3.3 给每组实验起短名。** 用一句话锚定每组实验的队列、改变的因素和对应的表，例如 main setup、model-card setup、ring-prefill setup、native-scale pilot、center-masked pilot、safety replay。不加新表；后文一律用这些短名。
11. **稳健性检查放到每节最后一段**，用 “Robustness checks.” 之类的引导语开头，与主结果分开。
12. **§4.1–§4.5 之间加过渡句**，说明为什么接着查下一项，把五节串成一条排查链：差距从哪来 → 掩码 → 预填色 → 安全拦截 → 换破损和画材是否翻转。
13. **§5.3 的五条局限**拆成带粗体短标题的条目，内容不增不删。
14. **偶尔把数字落到直觉上**，例如“相当于实用阈值的 5–7 倍”“误差是 LaMa 的三倍以上”。§3.4 已经说明 0.01 MAE 约等于 2.55 个灰阶。
15. 在合适的位置引用补充材料里的 Figure S1（森林图）和 Table S2；正文 6 张图的编号不变。
8. **不动的部分：** 摘要（已按 PeerJ 分段并核对过）、图注、表格、Data Availability、各项声明；补充材料只由 Codex 加 Table S2。

目标：Results 各小节降到每 100 词 12 个数字以内，置信区间加起来不超过 20 个。自查方法：去掉表格、图环境和引用命令后，按节分别数数字和英文词的个数。

## 守住的底线

- 正文里删掉的每个数字，必须已经出现在**人能直接读的表**里，即表 1–7、补充表 S1 或 S2。只在 Supplemental Data 压缩包里的不算。如果哪里都没有，就不要删，或者先请 Codex 补进补充材料。
- 保留下来的数字一个都不能改值。结论范围和分母口径（41/60、54/60、计划分母）照旧。
- 不新增引文，不新增实验。

## 核对（Codex）

1. 逐句对照修订前后的正文，列出所有删掉的数字，并逐个注明它在哪个表或补充材料里，作为 PR 附表。找不到出处的，标出来交回 Gemini。
2. 核对保留的每个数字与表格一致，小数位相同。
3. 重新统计每节的数字密度，填进 PR 描述。
4. 重新编译 PDF 和投稿 ZIP，更新清单哈希。顺便检查图号、表号的引用顺序。

## 分支

顺序：Codex 先开 `codex/peerj-table-s2` 补 Table S2 和 CSV → Claude 画 Figure S1 → Gemini 开 `gemini/peerj-readability` 修订正文 → Codex 在同一个 PR 里追加核对提交，或者另开 `codex/peerj-readability-check` → 每一步都请 Claude 审查。
