# 04 论文改写方案

新稿从 `manuscripts/m03_jcde/01_manuscript/latex/main.tex` 复制到新目录 `manuscripts/m03_revision/latex/main.tex`，原 JCDE 稿保留不动。参考文献同理复制 `references.bib`。

**所有数字和结论以 E1–E5 的实际结果为准。** 本文档中带 `[ ]` 的位置是待填数据；凡写“预期”的地方，数据不支持就改结论，不要改数据。

写作流程沿用仓库约定：先用 `external/humanizer/SKILL.md` 起草，再用 `external/AI-Research-SKILLs/20-ml-paper-writing/ml-paper-writing/SKILL.md` 修改。英文正文，单一拼写体系（建议美式，投稿前按目标期刊统一）。

## 1. 定位

**一句话定位：** 一个同对象、同视角、已知 3D 真值的配对基准，测量四个开源 image-to-3D 模型面对草图和插画输入时几何如何变化，并把形状误差、姿态/尺度误差和网格可用性分开报告。

**和 Cue3D 的关系：** Cue3D 研究的是“各类图像线索对单图 3D 生成有多重要”，规模更大；本文研究的是“同一物体从照片换成设计常用的描绘方式时，模型选择会不会改变”，强调严格配对、实体与拓扑终点、配准协议的影响、种子可靠性。引言和相关工作要明说这一点，不回避。

## 2. 题目候选

最终措辞等数据出来再定。原则：陈述读者能得到什么，不以“假设被否定”为题。

1. *How robust are open image-to-3D generators to sketch and illustration inputs? A paired benchmark with known 3D ground truth*
2. *From photographs to sketches: A paired benchmark of geometric robustness in open image-to-3D generation*
3. 若 A3 显示明显的排名翻转：*Photo benchmarks do not transfer to sketches: Paired evaluation of four open image-to-3D generators*
4. 若 E1 显示配准协议显著改变结论：*Pose, scale or shape? Paired evaluation of image-to-3D generators on non-photographic inputs*

## 3. 摘要结构（200–250 词，一段）

1. 背景一句：image-to-3D 越来越多用于以草图和插画为输入的设计工作，但评测几乎只用照片。
2. 缺口一句：同一物体换描绘方式后几何怎么变，缺少有真值的配对测量。
3. 方法两句：120 个 GSO 对象，照片式渲染加 [6] 种配对描绘（含学习型线稿），四个开源模型，[6,240 + E4 数量] 次重建；逐样本配准后分别报告形状、姿态/尺度、实体、拓扑和六视角指标。
4. 结果三到四句，每句一个数字：最大退化（模型、风格、ΔF、ΔIoU）；稳定的模型；排名翻转或失败率；线索稀疏与退化的关系；种子可靠性。
5. 结论一句：给使用者的建议。

摘要里不出现：“pre-specified hypothesis was rejected”作为主结论、内部门槛名称、p 值堆叠。原 RG 结果在摘要中最多半句。

## 4. 关键词

image-to-3D generation; sketch-based modelling; geometric robustness; paired benchmark; 3D evaluation; computational design（按目标期刊上限删减）

## 5. 引言（5 段）

1. **场景**：单图 3D 生成已能在秒级产出网格，设计、游戏、文化遗产流程开始使用。早期设计输入常常是线稿、色块稿、插画，而非照片。
2. **评测缺口**：主流比较用照片或照片式渲染。Cue3D 等工作已说明去掉阴影、只给边缘、风格迁移会降低质量。但对设计者而言，更实际的问题是：同一物体换一种描绘方式后，该选哪个模型；生成的网格还能不能直接用；一次生成可不可靠。这需要同对象、同视角、已知真值的配对测量，以及把姿态误差和形状误差分开的评测协议。
3. **本文做法**：概述配对设计、四个模型、三种配准协议、指标族。
4. **主要发现**：用 3–4 个数字概括（待 E1–E4 结果）。
5. **贡献**（三条）：
   1. 一个可复现的配对基准：同对象、同视角、同遮罩的多种描绘方式，已知 3D 真值，形状误差与姿态/尺度误差分离报告；
   2. 四个主流开源模型在 [6] 种输入下的系统比较，涵盖形状、实体、拓扑和独立六视角诊断；
   3. 面向使用者的结论：照片排名能否迁移到草图、失败集中在何种输入、随机模型单次输出的可靠性，并给出选型与检查建议。

删去原引言中关于 RG 公式、冻结门槛的段落，RG 定义挪到 Methods。

## 6. 相关工作（4 小节）

1. **单图 3D 生成**：保留原内容，压缩约三分之一。
2. **草图与艺术化输入**：保留原内容；Art3D 补一句其做法（给扁平插画加明暗代理图再交给 TRELLIS）和局限（只有定性评测），作为“专用方法”与“通用模型基准”的区分。
3. **3D 生成的评测与鲁棒性**：把 Cue3D 写成最近的相关工作，用三四句说明它做了什么、结论是什么、本文与它的区别（见第 1 节）。保留 3DGen-Bench、3D Arena、SI23DCQA；可加 Hi3DEval 与 2026 年关于单图 3D 网格质量廉价代理指标可靠性的研究。
4. **配准与评测协议**（新增）：单图重建评测通常先逐样本对齐再算 Chamfer/F-score（如 SPAR3D 的旋转搜索加 ICP）；原生 3D 生成器在规范坐标空间生成，与输入视角不绑定（Pose-Aware Diffusion）。引出本文为什么同时报告对齐前后。

## 7. 方法（压缩到约 1,800 词）

保留并精简：对象与实体真值（原 3.2）、配对描绘（原 3.3，加 lineart 一条）、模型与推理（原 3.4，表 1 加 E4 行）。

新增或改写：

- **配准协议**：三种协议的定义、对齐算法（候选旋转、对称 ICP、尺度范围）、为何以 sim 为主、姿态/尺度终点如何计算。一张小表列三种协议。
- **指标**：表面、实体、拓扑、六视角；多阈值与多分辨率作为敏感性。
- **输入线索量**：四个指标的定义与“近乎空白”的预定义阈值。
- **统计**：独立单位、bootstrap、Holm 族、失败的定义。

删去：冻结门槛的两段细节（移到补充材料一段说明即可），“publication evidence gate”等内部用语。保留一句：分析计划与发现/确认拆分在推理前已确定，协议在发现配准问题后修订，原协议结果完整报告于补充材料。

## 8. 结果（按 03_ANALYSIS.md 的 A1–A8 排序）

每小节第一句给结论和数字，再展开。小节标题直接写问题的答案，例如“Sketch and edge inputs degrade InstantMesh far more than the native 3D generators”（以实际数据为准）。

原 RG 检验成为 A7 一节：说明原协议下 0/4 模型通过，新协议下结果为 [ ]，并解释表面与实体指标在什么情况下分歧。

## 9. 讨论（4 小节）

1. **对模型选择的意义**：一张“使用建议”表，行是输入类型（照片、线稿、扁平色块、低细节、水彩），列是“相对稳健的模型”“主要风险”“建议检查的指标”“建议的种子数”。内容只来自本文数据。
2. **评测协议的影响**：配准方式如何改变绝对分数和结论；建议基准同时报告对齐前后。
3. **为什么模型反应不同**：架构差异作为假设，不写因果；线索量的关联结果在这里讨论。
4. **与 Cue3D 等工作的一致与不同**。

## 10. 局限

保留原稿的局限条目（GSO 物体类别、合成描绘、两颗种子、无人评、本地冻结未公开注册），加上：

- 逐样本相似变换会掩盖尺度误差，因此单独报告了姿态/尺度终点；
- 旋转对称物体的姿态角不可辨识；
- lineart 条件仍是由渲染图生成，不等于真人手绘。

## 11. 要删的句子与段落

在新稿中查找并删除或改写：

- “The displayed meshes and inputs are experimental outputs rather than AI-drawn placeholders.”（图 1 图注）
- “but no such human scores are fabricated or inferred here”（原 4.3 节末段，整段删去）
- 引言第 6 段中“tests and rejects a pre-specified ... rather than replacing it with a favourable post hoc claim”的贡献表述
- 讨论 5.1 节整节（“The negative primary result changes the scientific claim”），其中有用的内容并入 A7 和讨论第 2 小节
- 所有 “gate”“frozen evidence boundary” 的出现，改为普通的方法描述

## 12. 参考文献

- 保持 35–45 条，近三年占一半左右。
- 修正现有条目：`li2025cue3d` 已发表于 NeurIPS 2025，venue 从 arXiv 改为会议论文集；`jiang2025threedgenbench` 的 key 与第一作者（Yuhan Zhang）不符，核实后更正 key 或作者。
- 新增候选（每条必须打开原文核实作者、题名、年份、正式出处后再加）：

| 文献 | 用途 | 核实状态 |
| --- | --- | --- |
| SPAR3D, arXiv 2501.04689 | 逐样本旋转搜索 + ICP 的评测惯例 | 已打开 PDF 确认其对齐描述 |
| Pose-Aware Diffusion for 3D Generation, arXiv 2605.00345 | 原生 3D 生成器在规范空间生成 | 已打开 PDF 确认相关表述 |
| A Cross-Model VLM-Judge Protocol for Single-Image 3D Mesh Quality, arXiv 2606.18451 | 廉价代理指标的可靠性 | 已打开 PDF |
| Hi3DEval, arXiv 2508.05609 | 3D 生成评测 | 仅见检索标题，需核实 |
| Deep Sketch-Based 3D Modeling: A Survey, arXiv 2603.03287 | 草图建模综述（可能就是已有的 `tono2026sketchsurvey`，先比对） | 需核实 |
| SF3D | Cue3D 采用的对齐方法来源 | 需核实 |

## 13. 图表

见 03_ANALYSIS.md 的图表清单。图 1 改编现有可编辑源文件；其余用新数据重新生成。每张图的图注第一句写结论。

## 14. 篇幅目标

正文（不含参考文献）6,000–7,000 词；正文图 6 张、表 4 张以内；其余进补充材料。
