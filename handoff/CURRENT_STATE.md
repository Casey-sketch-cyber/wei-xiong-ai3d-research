# 当前研究状态与版本选择

交接日期：2026-11-06。本页来自当日对本地文件的核对；没有重新连接服务器或重跑完整 GPU 实验。

## M03：现有主线论文

最终标题为 Cross-style robustness in image-to-3D generation is model-specific: A paired four-model benchmark with known 3D ground truth。

当前 LaTeX 在 manuscripts/m03_jcde/01_manuscript/latex/。最新完整作者信息包在 manuscripts/m03_jcde/03_submission_materials/submission_updated_20260909_second_corresponding_no_orcid/。

| 次序 | 作者 | 单位号 | 联系信息 |
| --- | --- | --- | --- |
| 1 | Wei Xiong | 1 | xiongwei@guit.edu.cn |
| 2 | Wei Meng | 2 | mengwei@mail.glnc.edu.cn |
| 3 | Chu Qiu | 4 | 第一通讯，appamm94@gmail.com |
| 4 | ShuWen Li | 1 | lishuwen@guit.edu.cn |
| 5 | Zhanhao Liang | 3 | 第二通讯，lyon@cumt.edu.cn；无 ORCID |

单位 1 为 Guilin Institute of Information Technology，单位 2 为 Guilin Normal College，单位 3 为 School of Materials Science and Engineering, South China University of Technology，单位 4 为 Guilin Life and Health Career Technical College。详细地址以标题页为准。

### 研究演变

2026 年 6 月发现实验只有 TripoSR 等较早基线，发现了体积/厚度退化和表面指标变化之间不一致的案例。2026 年 7 月经方法及真实几何基准改进后，完成四模型确认实验，原先的普遍指标悖论假设未确认，研究观点改为模型与风格配对下的几何鲁棒性差异。

权威证据解释为 manuscripts/m03_jcde/05_evidence_audit/four-model-confirmatory-evidence-20260729-zh.md。早期 RUN_INDEX、main100 报告、paper-claim-evidence-matrix 与旧论文归档只记录历史阶段。

### 确认实验

- C120：120 个公开 GSO 对象，排除发现集 D30。
- 六输入条件：photo-like reference、edge、flat colour、low detail、sketch、watercolour。
- 四模型：TripoSR、InstantMesh、Hunyuan3D 2.1、TRELLIS。
- 共 6,240 次重建，主条件有 5,040 项六视角渲染诊断。
- 对照已修复水密 ground truth，报告表面、占据实体、拓扑、六视角渲染指标。
- 50,000 次对象聚类 bootstrap，99% 区间，四模型主检验经 Holm 校正。
- 四模型均未通过 sketch RG 的 0.01 主检验。
- 模型与风格交互显著，F-score@0.05 定义下 Holm p 约 1.03e-8；@0.10 的敏感性检验约 0.0586。
- InstantMesh 在 sketch 下退化最明显；Hunyuan3D 2.1 与 TRELLIS 在主视角 sketch 条件下变化较小、区间跨零。

完整性验证中的 all_pass=true 与预设研究门槛 q2_gate_passes=false 并存，二者含义不同。标题和摘要已经采用后续模型特定结论。

## M02：探索材料

本仓库保留 6 月方向扫描、EmoArt-50/100 情感代理报告、TripoSR 评估代码、Hunyuan3D 形状与投影颜色尝试报告，以及旧人评工具和 ArtEmis 授权说明。

这些材料不能证明真人感知改变。ArtEmis/WikiArt 正式授权实验和真人评分在此归档中仍未完成。后续用户明确偏好不依赖真人评分的研究，不应默认重启旧人评计划。

M02 结果不能与 M03 的已知真实几何四模型确认实验混合统计。

## M05：RevealRepair3D

材料位于 data/autoresearch_runs/ar-20260903-m05-visrepair3d/。已有 2026-09-04 的 480-case 正式实验、优化器、基线、消融、稳健性、局部 oracle 和完整性审查记录，尚未发现本地完整投稿论文。

窄创新是已有布局的后处理修复：固定参观路线、有符号的 hide/show 计划、first-hit 归因、局部平移/yaw 编辑，以及已编码硬约束的保持。

最终报告记录 476/480 达到规定容差，hard-valid 为 100%，中位编辑实体数为 1，中位评估次数为 99。无稀疏性消融结果相同的负结果、8 个 compound 样本的局部网格重合、四个失败案例和受限 oracle 的范围都必须披露。

这项研究不依赖人评，但没有证明人类叙事体验、美学提升、真实场馆泛化或全局最优。M05 是另一项研究方向；不能继承 M03 的数据、作者声明或发表状态。

## 本次交接的范围

纳入：论文/参考文献源文件、当前 PDF 与 DOCX 投稿材料、可编辑 PPTX、图表、生成与评估代码、协议、审查说明、公开文献元数据、数字结果摘要和已用写作技能。

排除：原始数据集、完整艺术输入图像集、mesh、权重、逐病例几何/完整布局、缓存、环境、凭据、重复分发 ZIP、大型 TIFF 和临时渲染。

原工作区为 D:/AutoResearch；本仓库是独立筛选的快照，不是该工作区的全部备份。
