# AutoResearch Run Index

Run ID：`ar-20260604-163404-directed`

日期：2026-06-04

## 当前状态

M03：实验完成，可作为主线论文方向。

M02：自动实验、EmoArt-5k 50 样本、EmoArt-100 robustness、人评材料、评分后统计脚本、图表、claim 边界、远程/本地校验均已完成；Hunyuan3D 2.1 小规模 shape 重跑 8/8 成功，彩色投影后处理 8/8 成功，视觉可读性明显强于灰模，但官方 PBR texture 未完成；严格 ArtEmis/WikiArt 授权实验和真人评分仍需人工完成。

一键验证：

```powershell
cd D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed
python verify_experiment_package.py
```

最新状态：

- `status: pass`
- required checks：133 / 133
- boundary checks：7 / 7

## 最先阅读

| purpose | file |
|---|---|
| 当前状态看板 | `status_dashboard\status_dashboard.md` |
| 轻量交接包 | `handoff_package\HANDOFF_README.md` |
| 最终完成度和边界 | `experiment-completion-audit-zh.md` |
| 论文主张和证据边界 | `paper-claim-evidence-matrix-zh.md` |
| 图表和汇总表 | `final_figures_tables\` |
| 一键验证报告 | `package_verification\verification_summary.md` |
| 复现清单 | `REPRODUCIBILITY-zh.md` |
| 本地 SHA256 清单 | `artifact_manifest\artifact_manifest_sha256.csv` |
| 远程 artifact inventory | `remote_artifact_inventory\remote_artifact_inventory.md` |
| Hunyuan3D 2.1 小规模重跑 | `m02-hunyuan21-smoke-results-zh.md` |
| Hunyuan3D 2.1 彩色投影 | `m02-hunyuan21-colorized-projection-results-zh.md` |

## M03 主线

核心结论：艺术化/风格化输入会诱导 TripoSR image-to-3D 输出出现体积和厚度坍缩；Chamfer/F-score 有时反而改善，因此传统点云指标可能掩盖 3D 资产可用性退化。

关键文件：

| artifact | role |
|---|---|
| `m03-main100-results-zh.md` | M03 100-object 主实验报告 |
| `m03-pilot30-results-zh.md` | M03 pilot30 报告 |
| `m03-remote-progress-2026-06-04.md` | 远程实验历程和 res128 鲁棒性记录 |
| `m03_main100_metrics\` | main100 指标 |
| `m03_res128_metrics\` | res128 鲁棒性指标 |
| `final_figures_tables\m03_main100_volume_z_ratios.svg` | M03 主图 |
| `final_figures_tables\m03_main100_metric_paradox.svg` | 指标悖论图 |
| `final_figures_tables\m03_res128_volume_z_ratios.svg` | 鲁棒性图 |

## M02 补充方向

核心结论：M02 自动实验支持“绘画到 3D 可能削弱或重编码情感线索”的代理现象，但不能声称正式 ArtEmis/WikiArt 人类情感实验已完成。

关键文件：

| artifact | role |
|---|---|
| `m02-proxy-results-zh.md` | M03 output affect proxy 报告 |
| `m02-emoart50-results-zh.md` | EmoArt-5k 50 样本真实绘画实验报告 |
| `m02-emoart100-results-zh.md` | EmoArt-100 robustness 报告 |
| `m02-data-access-and-rubric-zh.md` | 数据访问、人评 rubric 和 M02 总状态 |
| `m02_proxy_metrics\` | M02 proxy 指标 |
| `m02_emoart50_metrics\` | EmoArt-5k 指标 |
| `m02_emoart100_metrics\` | EmoArt-100 robustness 指标 |
| `m02_human_audit_pack\` | 人工评价材料和分析脚本 |
| `m02_rater_distribution\` | 可直接发给评价者的自包含评分 zip |
| `m02_artemis_access_package\` | ArtEmis/WikiArt 授权申请和留档 zip |
| `m02_external_steps_pack\` | ArtEmis 授权和真人评分执行材料 |
| `m02-hunyuan21-smoke-results-zh.md` | Hunyuan3D 2.1 小规模 shape 重跑结论 |
| `m02-hunyuan21-colorized-projection-results-zh.md` | Hunyuan3D 2.1 彩色投影后处理结论 |
| `m02_hunyuan21_rerun\` | Hunyuan3D 2.1 shape 输入、mesh、彩色投影预览和结果 zip |
| `final_figures_tables\m02_proxy_affect_drift.svg` | M02 proxy 图 |
| `final_figures_tables\m02_emoart50_affect_summary.svg` | EmoArt-5k 图 |
| `final_figures_tables\m02_emoart100_affect_summary.svg` | EmoArt-100 robustness 图 |

## 图表与表格

生成脚本：

```powershell
python generate_final_figures.py
```

输出目录：

```text
final_figures_tables\
```

核心文件：

- `experiment_summary_table.csv`
- `figure_caption_table.csv`
- `m03_main100.csv`
- `m03_res128.csv`
- `m02_proxy.csv`
- `m02_emoart_summary.csv`
- `m02_emoart_va.csv`
- `m02_emoart100_summary.csv`
- `m02_emoart100_va.csv`
- 6 张 SVG 图。

本地没有 `matplotlib` 时，脚本会自动生成无依赖 SVG fallback。

## 人工评价

材料目录：

```text
m02_human_audit_pack\
```

评价者打开：

```text
m02_human_audit_pack\rating_tool.html
```

只读展示页：

```text
m02_human_audit_pack\annotation_web.html
```

每位评价者可以从评分工具导出，或手工复制并填写：

```text
m02_human_audit_pack\annotation_template.csv
```

评分后统计：

```powershell
cd D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_human_audit_pack
python analyze_annotations.py rater_exports\annotation_rater01.csv rater_exports\annotation_rater02.csv
```

评价者分发包：

```powershell
python make_m02_rater_distribution.py
```

人评执行说明见：

```text
m02_external_steps_pack\human_evaluation_protocol-zh.md
m02_external_steps_pack\rater_invitation_template-zh.md
m02_external_steps_pack\rater_consent_template-zh.md
m02_external_steps_pack\human_evaluation_ethics_checklist-zh.md
```

## ArtEmis/WikiArt 授权

授权申请材料：

```text
m02_external_steps_pack\artemis_access_request_template-zh.md
m02_external_steps_pack\artemis_authorization_record_template-zh.md
m02_external_steps_pack\artemis_access_live_check-zh.md
m02_external_steps_pack\post_artemis_data_plan-zh.md
```

授权申请分发包：

```powershell
python make_m02_artemis_access_package.py
```

当前边界：

- ArtEmis 官方数据下载需要填写官方表单并接受 Terms of Use；
- 未授权前，不得声称 M02 已完成正式 ArtEmis/WikiArt 实验；
- 当前 EmoArt-5k/EmoArt-100 只能作为可自动获取的替代/代理实验。

外部步骤完成度检查：

```powershell
python check_external_steps.py
python run_m02_strict_followup.py
```

输出：

```text
m02_external_steps_pack\external_step_checks\external_completion_check.json
m02_external_steps_pack\external_step_checks\external_completion_check.md
```

## 本地与远程完整性

本地 SHA256 manifest：

```powershell
python generate_artifact_manifest.py
```

输出：

```text
artifact_manifest\artifact_manifest_sha256.csv
artifact_manifest\artifact_manifest_summary.json
```

远程 inventory：

```powershell
$env:REMOTE_PW='<password>'
uv run python generate_remote_inventory.py
```

输出：

```text
remote_artifact_inventory\remote_artifact_inventory.json
remote_artifact_inventory\remote_artifact_inventory.md
```

当前远程 inventory 会记录 11 个关键目录，包括新增 EmoArt-100 输入、TripoSR 输出和 eval 目录；精确文件数以 `remote_artifact_inventory\remote_artifact_inventory.md` 为准。

## 不能过度声称

不要写：

- M02 已完成正式 ArtEmis/WikiArt 实验；
- M02 已证明真人情绪感知改变；
- 本研究提出了新的 image-to-3D 模型；
- 结果适用于所有 image-to-3D 模型。

可以写：

- M03 已完成公开数据上的主实验和鲁棒性实验；
- M03 支持 style-induced geometry collapse / metric paradox；
- M02 自动代理实验发现 affect drift 和 geometry degradation 可能不同步；
- M02 人评和 ArtEmis 授权材料已准备好，但人工步骤仍待完成。
