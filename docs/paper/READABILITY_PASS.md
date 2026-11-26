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

## 改法（Gemini）

1. **每个结论在正文里最多给一个核心数字。** 一般是主指标 MAE 的差值，配一个 95% 置信区间。其余指标（LPIPS、DISTS、ΔE00、前后原值）改写成“见表 X”，或者用一句定性话概括，例如 “LPIPS, DISTS and ΔE00 moved in the same direction (Table 4)”。
2. **正文不再重复表里已有的数。** 正文负责讲“发生了什么、有多大”，具体数值留在表里。
3. **能用比例、倍数说清楚的，就不用四位小数。** 例如 “reduced masked MAE by about a third”“five to seven times the 0.01 margin”。正文里的数值一律保留 2–3 位有效数字，例如 0.098，不写 0.0981；表里保持原来的精度。
4. **每个 §4.x 小节第一句就是结论**（小节标题已经是结论，可以与标题呼应），后面的句子再给证据。
5. **一句话最多放一个括号区间。** 两组对照的区间不要串在同一句里。
6. **§3 方法里的设定参数集中到一处。** 例如 SDXL 的 strength / CFG / 步数 / 分辨率 / 种子，统一放在 §3.3 第一次出现的地方；后文改写成 “the model-card example settings”，不再逐项重复。
7. **Introduction 的贡献列表**每条最多保留一个数字，不要把摘要里的数字再抄一遍。
8. **不动的部分：** 摘要（已按 PeerJ 分段并核对过）、图注、表格、补充材料、Data Availability、各项声明。

目标：Results 各小节降到每 100 词 12 个数字以内，置信区间加起来不超过 20 个。自查方法：去掉表格、图环境和引用命令后，按节分别数数字和英文词的个数。

## 守住的底线

- 正文里删掉的每个数字，必须已经出现在表 1–7、补充材料表 S1，或者 Supplemental Data 里。如果哪里都没有，就不要删，或者先请 Codex 补进补充材料。
- 保留下来的数字一个都不能改值。结论范围和分母口径（41/60、54/60、计划分母）照旧。
- 不新增引文，不新增实验。

## 核对（Codex）

1. 逐句对照修订前后的正文，列出所有删掉的数字，并逐个注明它在哪个表或补充材料里，作为 PR 附表。找不到出处的，标出来交回 Gemini。
2. 核对保留的每个数字与表格、Supplemental Data 一致；四舍五入后的值与原值一致。
3. 重新统计每节的数字密度，填进 PR 描述。
4. 重新编译 PDF 和投稿 ZIP，更新清单哈希。顺便检查图号、表号的引用顺序。

## 分支

Gemini 开 `gemini/peerj-readability`，Codex 在同一个 PR 里追加核对提交，或者另开 `codex/peerj-readability-check`。完成后请 Claude 审查。
