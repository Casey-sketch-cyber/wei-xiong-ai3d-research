# Experiment Completion Audit

日期：2026-06-04

## 总结

当前已完成所有可全自动执行的 M03/M02 实验，并已同步本地证据文件。

严格意义上，M03 已达到主线论文候选的实验完成状态；M02 已完成 proxy、EmoArt-5k 50 样本和 EmoArt-100 robustness 三类自动实验，但 ArtEmis/WikiArt 正式情感标注实验仍受人工表单授权和人工评价限制，不能被描述为完全完成。

总入口：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\RUN_INDEX-zh.md
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\README.md
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\REPRODUCIBILITY-zh.md
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\status_dashboard\status_dashboard.md
```

## M03 完成度

状态：完成，可作为主线方向继续写作和补充图表。

已完成实验：

| experiment | scale | status | local evidence |
|---|---:|---|---|
| TripoSR style smoke | 5 objects x 6 styles | completed | `m03-remote-progress-2026-06-04.md` |
| Objaverse GT smoke | 2 objects x 6 styles | completed | `m03-remote-progress-2026-06-04.md` |
| pilot30 | 30 objects x 6 styles | completed | `m03_remote_metrics\`, `m03-pilot30-results-zh.md` |
| main100 | 100 objects x 6 styles | completed | `m03_main100_metrics\`, `m03-main100-results-zh.md` |
| mc-resolution=128 robustness | 30 objects x 6 styles | completed | `m03_res128_metrics\`, `m03-remote-progress-2026-06-04.md` |

关键结论：

- main100 中 600 个 TripoSR 输出全部成功；
- 相对 photo，艺术化/风格化输入显著压缩 mesh 体积和厚度；
- Chamfer/F-score 经常反而优于 photo，说明传统几何距离可能掩盖风格导致的 3D 可用性退化；
- mc-resolution=128 重跑后仍保留同类体积压缩现象，主结论不是低分辨率 mesh extraction 的单一伪影。

主报告：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m03-main100-results-zh.md
```

## M02 完成度

状态：自动实验完成；严格 ArtEmis/WikiArt + 人工评价未完成。

已完成实验：

| experiment | scale | status | local evidence |
|---|---:|---|---|
| ArtEmis data access and rubric | design/audit | completed | `m02-data-access-and-rubric-zh.md` |
| M03-output affect proxy | 600 renders | completed | `m02_proxy_metrics\`, `m02-proxy-results-zh.md` |
| EmoArt-5k painting-to-3D | 50 paintings | completed | `m02_emoart50_metrics\`, `m02-emoart50-results-zh.md` |
| valence/arousal coarse audit | 50 paintings | completed | `m02_emoart50_metrics\emoart50_valence_arousal_aggregate.json` |
| EmoArt-100 robustness | 100 paintings | completed | `m02_emoart100_metrics\`, `m02-emoart100-results-zh.md` |
| EmoArt-100 valence/arousal audit | 100 paintings | completed | `m02_emoart100_metrics\emoart100_valence_arousal_aggregate.json` |
| human audit pack | 50 painting/render pairs | completed | `m02_human_audit_pack\` |
| human annotation analysis script | post-rating analysis | completed | `m02_human_audit_pack\analyze_annotations.py` |

M02 proxy 关键结果：

- `sketch` 对 affect proxy 漂移最大，top emotion match rate 为 0.43；
- `edge` 和 `low_detail` 的 affect top label 较稳定，但 M03 显示它们在几何上退化明显；
- 该结果支持 M02 与 M03 形成双指标叙事：几何退化和情感语义漂移并不总是同向。

M02 EmoArt-5k 关键结果：

- EmoArt-5k 抽样 50 张真实绘画；
- TripoSR 重建成功 50 / 50；
- 细粒度 original vs GT top-label match 为 0.12；
- 细粒度 render vs GT top-label match 为 0.06；
- render vs original top-label match 为 0.04；
- render-to-original JS divergence mean 为 0.1637；
- original vs GT valence match 为 0.72；
- render vs GT valence match 为 0.46；
- render vs original arousal match 为 0.94。

M02 EmoArt-100 robustness 关键结果：

- EmoArt-5k 追加抽样 100 张真实绘画；
- TripoSR 重建成功 100 / 100；
- 渲染成功 100 / 100；
- 细粒度 original vs GT top-label match 为 0.17；
- 细粒度 render vs GT top-label match 为 0.06；
- render vs original top-label match 为 0.04；
- render-to-original JS divergence mean 为 0.1687；
- original vs GT valence match 为 0.67；
- render vs GT valence match 为 0.46；
- render vs original arousal match 为 0.91；
- 该结果与 50 样本 valence drop 方向一致，增强 M02 公开数据代理证据。

边界：

- CLIP zero-shot 对 EmoArt 细粒度标签本身命中率较低，因此不能过度声称情绪识别准确；
- 现有结果更适合表述为“自动代理指标发现 3D 化可能改变绘画情感线索”；
- 若 M02 单独成文，需要补 ArtEmis/WikiArt 授权数据、人工评分和更强情感识别器。

人工审计材料：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_human_audit_pack\
```

审计包已验证：

- `annotation_web.html` 含 50 个样本块；
- `rating_tool.html` 含 50 个样本，可交互评分并导出 CSV；
- `annotation_items.csv` 含 50 行；
- `annotation_template.csv` 含 50 行；
- `RATER_QUICKSTART-zh.md` 已提供评价者最短操作说明；
- `rater_exports\README-zh.md` 已提供评分 CSV 回收目录说明；
- `m02_rater_distribution\M02_rater_package.zip` 已生成，可直接发给评价者；
- rater zip 含 108 个文件，其中 100 张 PNG，无重复文件名；
- `rater_tracking.csv` 已提供 rater01/rater02/rater03 的发送和回收状态追踪；
- `rater_followup_messages-zh.md` 已提供发送评分包和催收 CSV 的中文消息模板；
- `analyze_annotations.py` 可在评分完成后输出总体均值、逐样本均值和与自动 JS divergence 的 Spearman 相关；
- `images\` 含 100 张 PNG；
- 100 张 PNG 均为 512 x 512，未发现坏图。
- 空模板验证返回 `no_completed_scores`，不会生成假人评结论；
- 临时 3 行评分 smoke test 已通过。
- `rating_tool.html` 内嵌 JavaScript 语法检查通过。

这意味着人工评价的材料准备已完成，但评分本身仍需要人类评价者执行。

## 最终图表与汇总表

为把已完成的自动实验转成可审计的论文材料，已新增统一图表/表格生成脚本：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\generate_final_figures.py
```

输出目录：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\final_figures_tables\
```

写作边界与主张证据矩阵：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\paper-claim-evidence-matrix-zh.md
```

已生成并验证的表格：

| file | rows |
|---|---:|
| `experiment_summary_table.csv` | 5 |
| `figure_caption_table.csv` | 6 |
| `m03_main100.csv` | 5 |
| `m03_res128.csv` | 5 |
| `m02_proxy.csv` | 5 |
| `m02_emoart_summary.csv` | 1 |
| `m02_emoart_va.csv` | 1 |
| `m02_emoart_by_emotion.csv` | 8 |
| `m02_emoart100_summary.csv` | 1 |
| `m02_emoart100_va.csv` | 1 |
| `m02_emoart100_by_emotion.csv` | 8 |

已生成并验证的图：

| file | status |
|---|---|
| `m03_main100_volume_z_ratios.svg` | valid SVG |
| `m03_main100_metric_paradox.svg` | valid SVG |
| `m03_res128_volume_z_ratios.svg` | valid SVG |
| `m02_proxy_affect_drift.svg` | valid SVG |
| `m02_emoart50_affect_summary.svg` | valid SVG |
| `m02_emoart100_affect_summary.svg` | valid SVG |

本地环境没有 `matplotlib`，因此脚本自动使用无依赖 SVG fallback。图表为论文草图级别；如需投稿版位图，可后续由 SVG 转 PNG/PDF。

## 一键验证脚本

为让实验包可以独立复查，已新增本地验证脚本：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\verify_experiment_package.py
```

运行结果：

```text
python verify_experiment_package.py
```

输出报告：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\package_verification\verification_summary.json
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\package_verification\verification_summary.md
```

验证状态：

- status：`pass`；
- required checks：112 / 112；
- boundary checks：5 / 5；
- 识别出的剩余人工/外部步骤：
  - ArtEmis/WikiArt authorization and formal data use；
  - Human evaluators filling annotation CSV files。

这说明当前本地证据包中的自动实验、图表、caption、claim matrix、人评材料和评分后统计脚本均已通过一致性检查；但验证脚本不会、也不能把外部授权和真人评分判定为完成。

## External Steps Pack

为把剩余外部/人工步骤转成可执行材料，已新增：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_external_steps_pack\
```

包含：

- `artemis_access_request_template-zh.md`：ArtEmis 官方表单/Terms of Use 申请说明和中英文研究说明草稿；
- `artemis_access_live_check-zh.md`：2026-06-04 联网核验后的 ArtEmis 访问边界记录；
- `human_evaluation_protocol-zh.md`：真人评价执行协议；
- `rater_invitation_template-zh.md`：评价者邀请模板；
- `rater_consent_template-zh.md`：评价者参与说明与同意模板；
- `rater_metadata_template.csv`：匿名评价者背景信息记录表；
- `human_evaluation_ethics_checklist-zh.md`：伦理与审稿检查清单；
- `post_artemis_data_plan-zh.md`：获得 ArtEmis/WikiArt 授权数据后的接入计划；
- `external_steps_status.json`：外部步骤状态。
- `m02_artemis_access_package\M02_ArtEmis_access_package.zip`：可直接用于 ArtEmis/WikiArt 授权申请和留档；
- ArtEmis access zip 含 7 个文件，且 `contains_restricted_data=false`。

联网复核来源：

- ArtEmis 官网显示数据约含 455K emotion attribution/explanation，覆盖约 80K WikiArt artworks，下载需要填写表单并接受 Terms of Use；
- ArtEmis GitHub 仓库也说明需要先通过表单下载数据，再使用 preprocess 工具。

当前状态：

- ArtEmis/WikiArt authorization：`pending_human_action`；
- human evaluation：`pending_human_evaluators`；
- automatic experiment package：`pass`。

`verify_experiment_package.py` 已纳入 external steps pack 检查，并通过；pending 状态作为边界检查保留，避免误判为已完成。

## Handoff Package

为方便合作者或写作者快速接手，已新增轻量交接包生成脚本：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\make_handoff_package.py
```

输出：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\handoff_package\
```

当前 handoff package：

- packaged files：65；
- total files on disk：67；
- size：约 224 KB；
- 包含状态看板、核心报告、claim matrix、图表/表格、验证摘要、人评/授权材料；
- 不包含 `m02_human_audit_pack\images\` 和远程 mesh/raw dataset。

`verify_experiment_package.py` 已纳入 handoff package 检查，并通过。

外部步骤完成度检查器：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\check_external_steps.py
```

输出：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_external_steps_pack\external_step_checks\external_completion_check.json
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_external_steps_pack\external_step_checks\external_completion_check.md
```

当前检查结果：

- overall status：`pending_external_or_human_steps`；
- ArtEmis/WikiArt authorization：`pending_human_action`；
- human evaluation：`pending_human_evaluators`；
- expected restricted ArtEmis dir：`D:\AutoResearch\data\restricted\artemis`。

## Artifact Manifest

为便于交接、压缩和后续复核，已新增本地证据包校验清单生成脚本：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\generate_artifact_manifest.py
```

输出：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\artifact_manifest\artifact_manifest_sha256.csv
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\artifact_manifest\artifact_manifest_summary.json
```

当前 manifest：

- total files：213；
- total bytes：约 49.0 MB，精确值以 `artifact_manifest_summary.json` 为准；
- categories：
  - run_metadata：20 files；
  - figures_tables：18 files；
  - m02：152 files；
  - m03：19 files；
  - verification：3 files；
  - claim_evidence：1 file。

已验证：

- CSV 行数与 summary 的 `total_files` 一致；
- 5 个关键文件重新计算 SHA256 均匹配；
- `verify_experiment_package.py` 已纳入 artifact manifest 检查，并通过。

## Remote Artifact Inventory

为记录远程服务器上的大型实验输出，已新增远程 artifact inventory 脚本：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\generate_remote_inventory.py
```

输出：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\remote_artifact_inventory\remote_artifact_inventory.json
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\remote_artifact_inventory\remote_artifact_inventory.md
```

当前远程盘点：

- key remote directories：11；
- existing directories：11；
- total remote files：3265；
- total remote bytes：1,424,501,026；
- remote root：`/root/autodl-tmp/m03`。

覆盖的关键远程目录包括：

- M03 main100 TripoSR outputs；
- M03 res128 robustness outputs；
- M02 proxy renders；
- M02 EmoArt-5k TripoSR outputs and eval renders；
- M02 EmoArt-100 TripoSR outputs and eval renders；
- Objaverse main100 raw subset；
- Objaverse main100 curated GT；
- EmoArt-5k sample50 inputs；
- EmoArt-5k sample100 inputs。

`verify_experiment_package.py` 已纳入 remote inventory 检查，并通过。

## 远程状态

审计时未发现相关实验进程仍在运行。

远程主要输出保留在：

```text
/root/autodl-tmp/m03/
```

本地证据包保留在：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\
```

## 论文路线建议

建议主线选择 M03：

- 公开数据更顺；
- 指标更客观；
- 100-object 主实验和 res128 鲁棒性实验已经完成；
- 现象清晰：style-induced geometry collapse under image-to-3D metrics。

M02 建议作为：

- 论文 discussion / supplementary；
- 或后续 SSCI/AHCI 扩展；
- 或在获得 ArtEmis/WikiArt 授权后再作为独立论文主线。
