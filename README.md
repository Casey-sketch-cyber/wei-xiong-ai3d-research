# 熊伟 AI + 3D 研究交接仓库

本仓库供 Claude 接续优化熊伟相关研究、论文、图表和代码。整理日期：2026-11-06。材料保留原工作区的相对目录，原始数据、完整三维输出、模型权重、环境和凭据留在仓库之外。

先读 [CLAUDE.md](CLAUDE.md) 和 [当前状态](handoff/CURRENT_STATE.md)，再开始修改。

> **2026-11-09 更新：** M03 投 JCDE 被拒，当前工作是改稿。方案、诊断与逐步任务见 [revision_20261109/](revision_20261109/README.md)，执行清单为 [CODEX_TASKS.md](revision_20261109/CODEX_TASKS.md)，新代码在 [experiments/m03_revision_20261109/](experiments/m03_revision_20261109/)。

| 方向 | 当前内容 | 首选入口 |
| --- | --- | --- |
| M03，主线论文 | 四模型、120 个对象、6,240 次重建；已有论文、图表、投稿文件及确认实验代码 | [LaTeX 正文](manuscripts/m03_jcde/01_manuscript/latex/main.tex) |
| M02，探索记录 | 绘画到 3D 的情感代理实验、纹理尝试、授权及人评工具；尚无完成的人评证据 | [状态与边界](data/autoresearch_runs/ar-20260604-163404-directed/m02-data-access-and-rubric-zh.md) |
| M05，后续小优化 | RevealRepair3D：固定路线上的有符号可见性约束修复；已有方法代码和 480-case 正式实验记录 | [最终证据报告](data/autoresearch_runs/ar-20260903-m05-visrepair3d/05_audit/final_evidence_report.md) |

## M03 当前版本

论文标题：

**Cross-style robustness in image-to-3D generation is model-specific: A paired four-model benchmark with known 3D ground truth**

- [论文 PDF](manuscripts/m03_jcde/01_manuscript/latex/main.pdf)
- [最新投稿文件](manuscripts/m03_jcde/03_submission_materials/submission_updated_20260909_second_corresponding_no_orcid/)
- [四模型证据解释](manuscripts/m03_jcde/05_evidence_audit/four-model-confirmatory-evidence-20260729-zh.md)
- [实验代码](experiments/m03_q2_confirmatory_20260715/)
- [结果汇总与分析表](experiments/m03_q2_confirmatory_20260715/results_final/artifacts_20260729/analysis/)
- [可编辑图表](manuscripts/m03_jcde/02_figures_tables/publication_figures/)
- [期刊样本文献分析与写作计划](manuscripts/m03_jcde/04_reviews_revisions/)

最终结论为模型与风格的配对差异。早期 TripoSR 的普遍“指标悖论”叙事未通过后续跨模型确认检验；详细边界见当前状态。旧报告保留研究经过，不能覆盖确认实验。

## 接续工作

1. 按 [Claude 任务说明](handoff/CLAUDE_TASK.md) 检查证据、正文、图表和投稿材料的一致性。
2. 按 [本地复核说明](handoff/LOCAL_SETUP.md) 检查仓库完整性、编译论文并运行相应检查。
3. 需访问完整数据时，按 [远程存储说明](handoff/REMOTE_STORAGE.md) 配置连接；本仓库未验证服务器现时在线状态。

保留少量数值汇总表、结果摘要、对象索引和论文代表性图片，便于核对已有结论。没有上传原始数据集、逐样本三维文件、训练权重或完整生成布局。目录名中的 data 是历史工作区路径，其中只选入脚本、协议、文献记录与结果汇总。

来源清单见 [SOURCE_MANIFEST.json](handoff/SOURCE_MANIFEST.json)。外部写作技能保留各自许可证；本仓库未为研究正文或代码新增开源许可。
