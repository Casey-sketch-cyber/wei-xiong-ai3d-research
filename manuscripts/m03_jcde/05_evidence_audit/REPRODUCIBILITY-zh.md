# Reproducibility Checklist

日期：2026-06-04

用途：说明本 run 的实验结果、图表、验证报告和外部步骤材料如何复核或重跑。

## 复核优先级

最推荐的复核顺序：

1. 读 `README.md`。
2. 读 `RUN_INDEX-zh.md`。
3. 运行 `python verify_experiment_package.py`。
4. 查看 `package_verification\verification_summary.md`。
5. 查看 `experiment-completion-audit-zh.md`。

## 本地一键验证

```powershell
cd D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed
python verify_experiment_package.py
```

当前预期：

- status：`pass`
- required checks：133 / 133
- boundary checks：7 / 7

该命令验证：

- M03/M02 指标文件存在且规模正确；
- 图表和 caption 表一致；
- M02 人评包完整；
- claim matrix 和总索引存在；
- artifact manifest 存在；
- remote inventory 本地报告存在；
- external steps pack 存在且 pending 状态正确；
- Hunyuan3D 2.1 小规模 shape 重跑报告、8 个 GLB、彩色投影 GLB/预览图和结果 zip 存在，并记录官方 PBR texture 未完成的边界。

该命令不会：

- 重新跑 GPU 实验；
- 重新下载数据集；
- 替你完成 ArtEmis/WikiArt 授权；
- 替真人评价者打分。

## 本地图表复现

```powershell
python generate_final_figures.py
```

输入：

- `m03_main100_metrics\eval_gt_relative_to_photo.json`
- `m03_res128_metrics\eval_gt_relative_to_photo.json`
- `m02_proxy_metrics\clip_affect_aggregate.json`
- `m02_emoart50_metrics\emoart50_affect_aggregate.json`
- `m02_emoart50_metrics\emoart50_valence_arousal_aggregate.json`
- `m02_emoart100_metrics\emoart100_affect_aggregate.json`
- `m02_emoart100_metrics\emoart100_valence_arousal_aggregate.json`

输出：

- `final_figures_tables\*.csv`
- `final_figures_tables\*.svg`
- `final_figures_tables\manifest.json`

说明：

- 当前本地环境没有 `matplotlib`，脚本会生成 SVG fallback。
- SVG 是论文草图级别；投稿前建议转为 PDF/PNG 并统一字体/线宽。

## 本地 SHA256 清单复现

```powershell
python generate_artifact_manifest.py
```

输出：

- `artifact_manifest\artifact_manifest_sha256.csv`
- `artifact_manifest\artifact_manifest_summary.json`

用途：

- 检查文件是否在移动/压缩/交接过程中损坏；
- 记录本地证据包中文件数量、大小和 hash。

## 轻量交接包复现

```powershell
python make_handoff_package.py
```

输出：

```text
handoff_package\
```

用途：

- 给合作者或写作者快速阅读；
- 包含状态看板、核心报告、图表、验证摘要、人评/授权说明；
- 不包含 100 张人评图片，也不包含远程 mesh/raw dataset。

## Hunyuan3D 2.1 小规模重跑和彩色投影复核

报告：

```text
m02-hunyuan21-smoke-results-zh.md
m02-hunyuan21-colorized-projection-results-zh.md
```

输入、shape 结果包和彩色投影预览：

```text
m02_hunyuan21_rerun\
m02_hunyuan21_rerun\hunyuan21_shape_smoke_results.zip
m02_hunyuan21_rerun\hunyuan21_colorized_projection_results.zip
m02_hunyuan21_rerun\remote_hunyuan21_shape_smoke_results\outputs\hunyuan21_shape_smoke\previews\hunyuan21_shape_contact_sheet.png
m02_hunyuan21_rerun\colorized_projection_results\previews\hunyuan21_colorized_projection_contact_sheet.png
```

当前状态：

- Hunyuan3D 2.1 shape pipeline：8 / 8 成功；
- 彩色投影后处理：8 / 8 成功；
- 结论：彩色投影明显改善视觉可读性，可作为最低成本 textured/colorized baseline；但 shape 语义错误、碎片化和侧面投影拉伸仍存在；
- 官方 PBR texture/paint：未完成，原因是当前可用的 Python 3.12 + torch 2.8/cu128 环境可跑 shape，但 paint 依赖 `bpy`，Python 3.12 下没有可用 pip wheel；因此不能声称 Hunyuan3D 2.1 官方带纹理实验已完成。

## 远程 artifact inventory 复现

前提：

- 远程服务器仍可访问；
- 设置 SSH 密码环境变量；
- 本地使用 `uv run python`，因为普通 Python 可能没有 `paramiko`。

命令：

```powershell
$env:REMOTE_HOST='connect.bjb2.seetacloud.com'
$env:REMOTE_PORT='13288'
$env:REMOTE_USER='root'
$env:REMOTE_PW='<password>'
uv run python generate_remote_inventory.py
```

输出：

- `remote_artifact_inventory\remote_artifact_inventory.json`
- `remote_artifact_inventory\remote_artifact_inventory.md`

当前远程 inventory 记录：

- 11 个关键目录全部存在；
- 精确远程文件数和大小以 `remote_artifact_inventory\remote_artifact_inventory.md` 为准；
- 新增覆盖 EmoArt-100 sample、TripoSR outputs 和 eval outputs。

说明：

- 该脚本只读远程目录，不移动、不清理、不修改文件。
- 如果远程服务器释放或目录迁移，inventory 只能证明上次盘点时的状态。

## 人工评价复现

材料：

```text
m02_human_audit_pack\
```

评价前说明与记录：

```text
m02_external_steps_pack\rater_consent_template-zh.md
m02_external_steps_pack\rater_metadata_template.csv
m02_external_steps_pack\human_evaluation_ethics_checklist-zh.md
```

评价者打开：

```text
m02_human_audit_pack\rating_tool.html
```

评分工具会保存本地进度，并导出 CSV。

只读展示页：

```text
m02_human_audit_pack\annotation_web.html
```

每位评价者复制：

```text
m02_human_audit_pack\annotation_template.csv
```

命名示例：

```text
rater_exports\annotation_rater01.csv
rater_exports\annotation_rater02.csv
```

评分后运行：

```powershell
cd D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_human_audit_pack
python analyze_annotations.py rater_exports\annotation_rater01.csv rater_exports\annotation_rater02.csv
```

输出：

- `analysis_outputs\human_annotation_summary.json`
- `analysis_outputs\human_annotation_item_summary.csv`

当前状态：

- 空模板验证会返回 `no_completed_scores`；
- 真人评分尚未完成。

## ArtEmis/WikiArt 正式实验复现

当前不能全自动复现正式 ArtEmis/WikiArt 实验，因为：

- ArtEmis 官方数据下载需要填写表单并接受 Terms of Use；
- WikiArt 图像使用需遵守相关条款；
- 当前未把 ArtEmis 原始数据放入本地证据包。

准备材料：

```text
m02_external_steps_pack\artemis_access_request_template-zh.md
m02_external_steps_pack\artemis_access_live_check-zh.md
m02_external_steps_pack\post_artemis_data_plan-zh.md
```

授权完成后，按 `post_artemis_data_plan-zh.md` 新增正式 ArtEmis 子实验。

检查外部步骤是否已从 pending 变成 ready：

```powershell
python check_external_steps.py
python run_m02_strict_followup.py
```

输出：

```text
m02_external_steps_pack\external_step_checks\external_completion_check.json
m02_external_steps_pack\external_step_checks\external_completion_check.md
```

当前预期状态为：

```text
pending_external_or_human_steps
```

## 脚本目录

| script | purpose |
|---|---|
| `verify_experiment_package.py` | 一键验证本地证据包完整性和边界状态。 |
| `generate_final_figures.py` | 从指标 JSON/CSV 生成汇总表和 SVG 图。 |
| `generate_artifact_manifest.py` | 生成本地证据包 SHA256 清单。 |
| `generate_remote_inventory.py` | 只读盘点远程关键输出目录。 |
| `check_external_steps.py` | 检查 ArtEmis 授权数据和真人评分 CSV 是否到位。 |
| `run_m02_strict_followup.py` | 外部授权/评分材料到位后自动续跑人评分析并生成 strict M02 状态报告。 |
| `make_m02_rater_distribution.py` | 生成可直接发给评价者的自包含评分 zip。 |
| `make_m02_artemis_access_package.py` | 生成 ArtEmis/WikiArt 授权申请和留档 zip。 |
| `make_handoff_package.py` | 生成轻量交接包。 |
| `m02_human_audit_pack\analyze_annotations.py` | 汇总真人评分 CSV。 |

## 不可复现或需人工介入的部分

- ArtEmis/WikiArt 授权；
- 真人评价者评分；
- 若远程服务器被释放，则远程 mesh/raw 文件不可从本地完整恢复；
- 当前只有 Hunyuan3D 2.1 shape 小规模对照和彩色投影后处理，官方 PBR texture 未完成；不能声称完整跨模型、官方带纹理复现。
