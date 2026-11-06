# AutoResearch Run ar-20260604-163404-directed

目标：中科院 SCI/SSCI/AHCI Q2，方向为 AI + 3D 建模 / AI + 艺术 / AI + 绘画。

## 当前结论

- M03 已完成自动实验，可作为主线论文方向。
- M02 已完成自动实验、EmoArt-5k 50 样本实验、EmoArt-100 robustness、人评材料、评分后统计脚本和外部步骤包；Hunyuan3D 2.1 小规模 shape 重跑 8/8 成功，彩色投影后处理 8/8 成功，视觉可读性明显强于灰模，但官方 PBR texture 未完成；严格 ArtEmis/WikiArt 授权实验和真人评分仍待人工完成。

## 从这里开始

请先读：

```text
status_dashboard\status_dashboard.md
RUN_INDEX-zh.md
```

然后读：

```text
experiment-completion-audit-zh.md
paper-claim-evidence-matrix-zh.md
REPRODUCIBILITY-zh.md
m02-hunyuan21-smoke-results-zh.md
m02-hunyuan21-colorized-projection-results-zh.md
```

## 一键验证

```powershell
cd D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed
python verify_experiment_package.py
```

最近验证状态：

- `status: pass`
- required checks：133 / 133
- boundary checks：7 / 7

## 核心目录

- `final_figures_tables\`：论文图表和汇总表。
- `m03_main100_metrics\`：M03 主实验指标。
- `m03_res128_metrics\`：M03 鲁棒性指标。
- `m02_emoart50_metrics\`：M02 EmoArt-5k 自动实验指标。
- `m02_emoart100_metrics\`：M02 EmoArt-100 robustness 指标。
- `m02_human_audit_pack\`：M02 真人评价材料。
- `m02_rater_distribution\`：可直接发给评价者的自包含评分 zip。
- `m02_artemis_access_package\`：可直接用于 ArtEmis/WikiArt 授权申请和留档的 zip。
- `m02_external_steps_pack\`：ArtEmis 授权和真人评价执行材料。
- `m02_hunyuan21_rerun\`：Hunyuan3D 2.1 小规模 shape 重跑输入、mesh、彩色投影预览和结果 zip。
- `run_m02_strict_followup.py`：外部授权/评分材料到位后的 strict M02 一键续跑入口。
- `m02_external_steps_pack\external_step_checks\`：外部步骤完成度检查报告。
- `artifact_manifest\`：本地 SHA256 manifest。
- `remote_artifact_inventory\`：远程 artifact inventory。
- `package_verification\`：一键验证报告。
- `status_dashboard\`：M03/M02 当前状态看板。
- `handoff_package\`：轻量交接包，不含人评图片和远程 mesh。
