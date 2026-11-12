# Codex 执行清单

按顺序执行。每完成一项，在本文件对应复选框打勾，并在 `revision_20261109/DECISIONS.md`（第一次时新建）追加一条：日期、做了什么、实际运行的命令、结果数字、遇到的问题。只写实际运行过的检查，不要把计划写成已完成。

开始前先读：`README.md`（本目录）、`01_DIAGNOSIS.md`、`02_EXPERIMENTS.md`，以及仓库根目录 `AGENTS.md`、`CLAUDE.md`。

## 全局规则

- 在新分支 `revision-20261109` 上工作；每个阶段一个提交，提交信息写清做了什么。每完成一个阶段就推送，并保持一个从该分支到 `main` 的 PR。不要自己合并，也不用等作者：Claude 审查通过后合并，没通过就在 PR 里写明要改什么（见根目录 `AGENTS.md` 的 Branches and merging）。
- 冻结目录和冻结脚本只读：`experiments/m03_q2_confirmatory_20260715/` 及服务器 `/root/autodl-tmp/m03_q2_confirmatory_20260715/` 下原有子目录。新服务器输出只写 `/root/autodl-tmp/m03_q2_confirmatory_20260715/revision_20261109/`。
- 网格、权重、原始数据、凭据不进 Git。服务器连接信息从环境变量读取（见 `handoff/REMOTE_STORAGE.md`）。
- 服务器上运行 Python 用 `python -I`。
- 不伪造任何数字、文献、人评。数据和预期不符时，改结论，不改数据，并在 DECISIONS.md 记录。
- 遇到本文档没覆盖的判断，先在 DECISIONS.md 写下选项和理由，选最保守的做法继续。

## 阶段 0：准备（约半天）

- [ ] 0.1 建分支 `revision-20261109`。
- [ ] 0.2 本地运行 `python -I experiments/m03_revision_20261109/diagnose_photo_baselines.py`，确认输出与 `01_DIAGNOSIS.md` 的 D1 表一致。
- [ ] 0.3 服务器上核对路径：`ls /root/autodl-tmp/m03_q2_confirmatory_20260715/`，找到推理结果 JSON（`<model>_results.json`）、每个模型的 `calibration.json`、真值 `solid_gt_view.ply`。把实际路径写进 DECISIONS.md，后续命令都用实际路径。
- [ ] 0.4 把 `experiments/m03_revision_20261109/` 同步到服务器的仓库副本，运行 `python -I experiments/m03_revision_20261109/tests/test_alignment_core.py`，6 项 PASS。
- [ ] 0.5 在 DECISIONS.md 中预先写下（在看任何新结果之前）：E3 的“近乎空白”阈值（`ink_coverage < 0.05` 且 `edge_density < 0.02`）、A3 的失败定义、关口 1 的判断标准（sim 与 camera 的 IoU@128 中位数差 ≥ 0.15）、代表性案例选择规则。

## 阶段 1：E1 小试与关口 1（约 1 天）

- [ ] 1.1 按 `02_EXPERIMENTS.md` E1 步骤 2，对四个模型跑小试（主实验、照片、前 20 个对象），输出到 `revision_20261109/reeval_pilot`。
- [ ] 1.2 运行 `merge_and_check.py`（`--reeval-root` 指向小试目录，`--frozen-root` 指向服务器上冻结的评估目录或仓库内 `results_final/artifacts_20260729/evaluation`）。`camera_` 指标必须逐条复现冻结值。不复现就停下排查，不要继续。
- [ ] 1.3 汇总小试：每个模型 camera 与 sim 协议下 F@0.05、IoU@128 的中位数，sim 对齐的旋转角与尺度中位数。写进 DECISIONS.md，并给出关口 1 的结论。
- [ ] 1.4 抽 8 个小试任务按 E5 的方式做三联图目检，确认对齐方向正确。
- [ ] 1.5 提交：脚本修正（如有）+ DECISIONS.md。

**若关口 1 未通过**（sim 与 camera 差别很小）：照常继续阶段 2，但在 DECISIONS.md 写明“camera 为主协议，sim 为敏感性”，并在 03/04 文档的相应位置按此调整。

## 阶段 2：全量重评估与其余实验（约 3–4 天，可并行）

- [ ] 2.1 E1 全量：四个模型、全部 6,240 个任务，每个模型 4 个分片并行。完成后 `merge_and_check.py` 要求 `all_pass: true`。
- [ ] 2.2 编写 `experiments/m03_revision_20261109/render_diagnostics_aligned.py`（规格见 02 的 E1“对齐后的六视角渲染”），对主实验 5,040 个网格跑 sim 协议渲染诊断。先用 `--limit 20` 检查，再全量。
- [ ] 2.3 E3：运行 `input_cue_stats.py`，得到 1,020 个输入的线索量表。
- [ ] 2.4 E2：核对 InstantMesh 冻结提交的官方预处理代码，写进 DECISIONS.md；编写 `run_instantmesh_official_preproc.py`；先跑 5 个任务看输出，再跑 1,440 个；用 `reevaluate_aligned.py` 评估。
- [ ] 2.5 E4：安装 `controlnet_aux`，生成 120 个 lineart 输入（先看 10 张确认样子正常，存缩略图到 `revision_20261109/assets/lineart_examples/`）；建新调度表；四个模型推理；重评估；对新输入跑 `input_cue_stats.py --extra-inputs`。
- [ ] 2.6 E5：按 02 的规则抽样做对齐目检图，拼图存到 `revision_20261109/assets/alignment_qc.png`，结论写进 DECISIONS.md。
- [ ] 2.7 把所有对象级结果 CSV（不含网格）复制回仓库 `experiments/m03_revision_20261109/results/`，提交。

## 阶段 3：分析与作图（约 3–4 天）

- [ ] 3.1 编写 `analyze_revision.py`，实现 `03_ANALYSIS.md` 的 A1–A8。可以 import 原 `analyze_confirmatory.py` 的函数。输出到 `experiments/m03_revision_20261109/results/analysis/`。
- [ ] 3.2 A7 的 camera 协议 RG 结果必须与原稿表 2 一致（TripoSR 0.0089、InstantMesh 0.0222、Hunyuan3D 2.1 −0.0041、TRELLIS −0.0091），作为分析代码正确性的检查。
- [ ] 3.3 编写 `make_revision_figures.py`，生成 03 文档图表清单中的图 2–6；图 1 改编 `manuscripts/m03_jcde/02_figures_tables/` 中的可编辑源文件。
- [ ] 3.4 按预先写下的规则选代表性案例，生成图 4。
- [ ] 3.5 写一份 `experiments/m03_revision_20261109/results/analysis/REVISION_RESULTS_REPORT.md`：每个 A 小节的主要数字与结论，标出与原稿结论不同的地方。
- [ ] 3.6 关口 2：逐条对照 `04_MANUSCRIPT.md` 中的预期主张，在 DECISIONS.md 写下“成立 / 不成立 / 需改写”。选定论文题目。提交。

## 阶段 4：改写论文（约 1–1.5 周）

- [ ] 4.1 复制 `manuscripts/m03_jcde/01_manuscript/latex/` 到 `manuscripts/m03_revision/latex/`，原稿不动。
- [ ] 4.2 按 `04_MANUSCRIPT.md` 逐节改写：题目、摘要、引言、相关工作、方法、结果、讨论、局限、结论。所有数字来自 3.5 的报告。
- [ ] 4.3 删除 04 文档第 11 节列出的语句。
- [ ] 4.4 核实并增补参考文献（04 文档第 12 节），每条新文献打开原文确认；修正 `li2025cue3d` 与 `jiang2025threedgenbench`。
- [ ] 4.5 写补充材料：原 camera 协议全部结果、形态学分析、E2 对照、阈值与分辨率敏感性、对齐目检图。
- [ ] 4.6 编译 PDF，逐页看图表是否清晰、编号是否连续、引用是否全部解析。
- [ ] 4.7 写一个数字核对表：正文中每个数字 → 来源 CSV 的文件与行列。提交。

## 阶段 5：发布与投稿准备（约 2–3 天）

- [ ] 5.1 按 `05_RELEASE_AND_SUBMISSION.md` 建干净的发布仓库并整理 README；调度表中的服务器绝对路径改为相对路径。
- [ ] 5.2 跑完 05 文档的投稿前检查清单，逐项打勾。
- [ ] 5.3 起草 cover letter（不指定期刊名，留占位）。
- [ ] 5.4 最终提交，并在 DECISIONS.md 写一段总结：完成了什么、哪些结论变了、还剩哪些需要作者决定的事项。

## 需要作者决定、Codex 不要自行决定的事

- 目标期刊；
- 是否把当前交接仓库改回私有；
- 发布仓库的名称和许可证；
- 若关口 1 或关口 2 的结果使论文主张发生大的改变，最终题目和主结论由作者确认。
