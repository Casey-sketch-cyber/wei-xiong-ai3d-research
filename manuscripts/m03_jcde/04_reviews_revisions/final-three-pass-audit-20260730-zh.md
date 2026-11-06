# M03 JCDE 终稿三遍审查记录

> 本记录形成于作者责任信息补齐之前。当前状态请以 `final-author-complete-audit-20260730-zh.md` 为准。

审查日期：2026-07-30  
目标期刊：Journal of Computational Design and Engineering (JCDE)  
当前题目：Cross-style robustness in image-to-3D generation is model-specific: A paired four-model benchmark with known 3D ground truth

## 总体结论

论文的实验、统计、图表、正文、参考文献和初投稿文件已经完成技术性收口。当前科学结论与确认性实验一致：原先设想的“跨模型通用 sketch surface-solid gap”没有通过预设门槛，可信结论应是跨风格几何鲁棒性具有显著的 model-style specificity。

确认性实验共完成 6,240 次重建，无失败或静默剔除；C120 主实验的 5,040 个 mesh 均完成独立六视角渲染诊断。四个模型均未通过 1% Holm 校正后的主检验，因此主证据门槛为 0/4；同时，model-by-style interaction 在 F-score@0.05 上显著（Holm-adjusted p = 1.03e-8）。论文没有把失败的主假设改写成成功结果，而是将其作为研究结果报告。

技术和科学文件已经达到可交给作者终审的状态。正式点击投稿前仍需作者确认 CRediT、经费、APC 账单信息、特刊/预印本状态，以及通讯作者 ORCID 是否重新以期刊要求的方式出现在 manuscript title page。

## 第一遍：逐段内容、论证与证据边界

### 1. 研究问题与贡献

- Introduction 将问题限定为：同一真实 3D object、同一视角、同一 framing 下，photo 与五种 matched abstractions 是否引发系统性、模型相关的几何变化。
- 贡献不再宣称发现通用 metric paradox，而是贡献 paired known-GT protocol、完整四模型比较、失败主假设的透明报告，以及 model-style specific robustness 的实证证据。
- Related work 覆盖单图 3D、艺术/草图输入和 3D 评价三个必要分支，没有用“无人研究”或“首次”之类无法证实的绝对表述。

### 2. 方法与可复现性

- C120 对象来自公开 Google Scanned Objects，选择、修复、视角和输入变换均在确认性推理前冻结。
- 模型为 TripoSR、InstantMesh、Hunyuan3D 2.1 和 TRELLIS。
- 主实验、V30 viewpoint、S30 severity 和 paired-seed 工作量在 Table 1 中分开列出，总数与运行记录一致。
- 同时报告 surface、solid occupancy、topology 和 six-view render diagnostics，避免以单一指标代表完整几何质量。
- 鲁棒性 gap、bootstrap、Holm multiplicity rule 和主证据门槛均在 Results 前定义。
- 文中准确表述为 “pre-specified/frozen evidence boundary”，并明确说明不是 formally pre-registered。

### 3. 结果与数值一致性

- 主检验：TripoSR sketch RG = 0.0089，99% CI [0.0001, 0.0180]，raw p = 0.00944，Holm p = 0.0378；InstantMesh = 0.0222，99% CI [-0.0124, 0.0583]；Hunyuan3D 2.1 = -0.0041；TRELLIS = -0.0091。四者均未通过 1% 校正阈值。
- 绝对退化：InstantMesh 在 sketch 下 ΔF-score@0.05 = -0.208、ΔIoU = -0.230，并由 silhouette、normal-render 和 topology 诊断复现。
- Hunyuan3D 2.1 与 TRELLIS 的 canonical-sketch 均值变化较小，99% 区间跨零；论文没有将其写成“完全不受影响”。
- View、severity 和 seed 分析均用于限制外推，而不是制造第二个主结论。
- Exploratory morphology 结果明确标为 exploratory，没有被包装成因果机制。

### 4. 图表与叙事链

- Figure 1：真实 matched inputs、同一重建流程、四模型输出和评价逻辑。
- Figure 2：主定量结果、主 gate 和 gap 的两个组成部分。
- Figure 3：对象级 case 与 aggregate metric 之间的关系，解释正负 gap 都可能出现。
- Figure 4：view、severity、seed robustness checks。
- Table 1：实验设计与工作量；Table 2：photo baseline；Table 3：主检验。
- 图表按首次引用顺序出现，正文先提出问题，再给 aggregate result，随后解释 case 和 robustness boundary。

### 5. 主张边界

- 支持：跨风格鲁棒性取决于 model-style pairing；photo baseline 不能单独决定 non-photographic robustness；solid 和 multi-view diagnostics 有必要与 surface metric 联合报告。
- 不支持：艺术化输入普遍改善或普遍破坏所有 image-to-3D 模型；RG 等于视觉质量；当前四模型结果可外推到所有生成系统；本研究证明了具体网络内部因果机制。
- 未使用真人评分，也未编造主观评价或统计结果。

第一遍结论：通过。论文逻辑与确认性证据一致，负结果被如实保留，未发现关键数字与主张冲突。

## 第二遍：期刊结构、篇幅和文件要求

### 1. 正文规模

- 主文档：26 页。
- 估算总词数：7,567；正文约 6,914 词。
- Abstract：240 词，单段，无引用、无公式。
- Keywords：6 个。
- Figures：4；Tables：3。
- Displayed mathematics：5 组；正文另有必要的 inline mathematical notation。
- References：正文实际引用并输出 39 条，高于用户要求的 30 条。

### 2. 结构与格式

- 正文章节为 Introduction、Related work、Material and methods、Results、Discussion、Limitations、Conclusion。
- 声明部分包括 Conflicts of interest 和 Data availability。
- 题名页包含四位作者、单位、通讯作者和邮箱。
- 用户明确要求删除的 “ORCID iDs:” 汇总行未出现在当前 PDF。
- “Material and methods” 比仅写 “Methods” 更清楚地覆盖数据、重建与统计流程，也符合工程计算论文的常见组织方式。

### 3. 图文摘要与 Highlights

- Graphical abstract：3000 x 1200 px，5:2，300 dpi；使用真实实验输入和真实模型输出，不是概念占位图。
- 图文摘要表达 matched photo/sketch 输入、四模型响应和 0/4 universal gate 的核心发现，不重复 Figure 1 的完整方法流程。
- Highlights 共 5 条；每条 10-12 个英文单词，均不超过 15 词和 100 个字符。
- Alt text 已作为条件性辅助文件单独提供。

### 4. JCDE 样本文献与引文策略

- 已参考期刊模板、checklist 和录用样本文献的结构、图表密度与论证方式。
- Checklist 对近期本刊相关文献属于建议性检查，不应为了形式性满足而加入与本研究不直接相关的引用。
- 当前未识别到必须取代现有核心文献的直接相关 JCDE 文章，因此没有人为增加不相关自引。后续若编辑指出特定本刊工作，再按实质相关性补充。

第二遍结论：正文篇幅、摘要、关键词、图表和参考文献数量满足当前模板所体现的研究论文规模。五份初投稿文件已经生成。作者贡献和财务声明属于作者责任，不能由写作代理代填。

## 第三遍：全文编译、参考文献与交付完整性

### 1. 编译与视觉检查

- LaTeX 主源在当前环境中完整编译为 26 页 PDF。
- 最终 log 无 overfull、underfull、undefined citation 或 undefined reference 警告。
- 从 source ZIP 解压到独立目录后再次编译成功，仍为 26 页。
- 逐页渲染检查未发现图表越界、正文遮挡、异常空白页或 Figure 3 标签重叠。
- Main Document、Graphical Abstract、Highlights、Checklist 和 Alt Text 均完成独立视觉检查。

### 2. 引用真实性

- BibTeX 数据库共 42 条；正文使用 39 条。
- 39/39 条正文引用均通过至少两个元数据来源交叉核对。
- 0 条 citation key 缺失，0 条需要人工补查。
- Objaverse、One-2-3-45++、Wonder3D、Wonder3D++、M-LRM、ArtiScene、Google Scanned Objects、TRELLIS 等核心条目的作者、年份、页码或 DOI 已校正。
- 对 2025-2026 新模型采用当前可验证的正式论文或预印本元数据，没有将未正式发表的版本伪装成期刊论文。

### 3. 数据与实验包

- 确认性实验包：m03_q2_confirmatory_artifacts.zip。
- 文件大小：10,988,489 bytes。
- SHA256：9cebe579d1ea770cf2c647d8da9ffaeaecf0db1f9fd03ebca90754e0f353809f。
- 包内保存冻结协议、对象清单、运行计划、聚合结果、分析脚本、图表生成代码和验证记录；受原数据条款约束的源资产不重复分发。

### 4. 初投稿文件

1. Main Document PDF。
2. Graphical Abstract PDF。
3. Highlights DOCX。
4. JCDE Submission Checklist DOCX。
5. LaTeX Source ZIP。

另附 confirmatory artifacts、Alt Text、中文交付说明和校验值，便于作者终审与归档。

第三遍结论：编译、视觉、引用和文件完整性检查通过。最终 SHA256 以 clean handoff 目录中的 SHA256SUMS.txt 为准。

## 投稿前必须由作者确认

1. 四位作者各自的 CRediT roles。
2. 是否存在研究资助；如有，提供 funding agency 和 grant number。
3. APC 付款作者、单位、完整账单地址和邮编。
4. 是否投 special issue，以及是否已发布 preprint。
5. 公开复现包的 DOI 或稳定仓库链接；若暂无，可维持 “available from the corresponding author during peer review” 的表述，但建议录用前存入持久仓库。
6. JCDE checklist 将通讯作者 ORCID 列为 manuscript 检查项，而用户此前明确要求删除 ORCID 汇总行。正式投稿前需在以下两者中作出选择：在 title page 以通讯作者脚注/链接重新加入 Chu Qiu ORCID，或仅保留在 checklist/投稿系统中并接受格式检查风险。

## 最终状态

**科学与技术材料：完成。**  
**作者责任信息：待作者确认。**  
**正式投稿状态：完成上述六项确认后即可生成无待办项的最终上传版本。**
