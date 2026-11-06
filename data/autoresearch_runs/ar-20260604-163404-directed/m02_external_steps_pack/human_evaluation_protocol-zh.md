# M02 真人评价执行协议

日期：2026-06-04

## 目的

评估 EmoArt-5k 真实绘画经 TripoSR 转换为 3D 渲染后，是否保留原图的情感、视觉证据、风格和几何可用性。

## 材料

评价材料位于：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_human_audit_pack\
```

评价者需要打开：

```text
rating_tool.html
```

评分工具可直接导出自己的一份 CSV：

```text
annotation_rater01.csv
annotation_rater02.csv
```

建议把导出的 CSV 放入：

```text
m02_human_audit_pack\rater_exports\
```

如果不使用评分工具，也可以从 `annotation_template.csv` 复制一份手工填写。

评价前请提供：

```text
rater_consent_template-zh.md
rater_metadata_template.csv
human_evaluation_ethics_checklist-zh.md
```

## 评价者数量

最低建议：

- 2 名评价者：可计算均值、分歧和初步一致性。
- 3 名评价者：更适合作为论文补充实验。

## 评分维度

每项 1-5 分：

| 字段 | 含义 |
|---|---|
| `emotion_preservation_1_5` | 3D 渲染是否保留原图主要情绪。 |
| `visual_evidence_preservation_1_5` | 原图描述和情感影响中提到的视觉证据是否仍可见。 |
| `style_preservation_1_5` | 3D 渲染是否保留原图的艺术风格/氛围。 |
| `geometry_usability_1_5` | 3D 结果是否像可用资产，而不是贴片、碎片或变形物。 |
| `multiview_stability_1_5` | 多视角下情绪/风格是否稳定。当前包只有一张主渲染图，因此该项可按“从现有渲染能否推断稳定资产”谨慎评分，或后续补多视角图后再正式使用。 |
| `overall_acceptability_1_5` | 综合是否可接受。 |

## 评分规则

- 1：完全不保留/不可用。
- 2：多数关键线索丢失。
- 3：部分保留，但有明显问题。
- 4：大体保留，仅有小问题。
- 5：明显保留且可用。

## 质量控制

- 每行 6 个分数字段必须全部填写。
- 不允许只填部分分数；分析脚本会拒绝 partial scoring。
- 每位评价者独立评分，不要互相讨论后再填写。
- 可选文字字段应尽量简短，记录最影响判断的视觉因素或 3D 化后丢失/新增的线索。
- 评价者应使用匿名 ID，例如 `rater01`，不要记录真实姓名。

## 评分后统计

在 `m02_human_audit_pack` 目录运行：

```powershell
python analyze_annotations.py rater_exports\annotation_rater01.csv rater_exports\annotation_rater02.csv
```

也可以先在 run 根目录运行 `python check_external_steps.py`。当至少 2 份完整评分 CSV 被放入 `rater_exports\` 后，检查器会显示 `ready_for_analysis`。

输出：

- `analysis_outputs/human_annotation_summary.json`
- `analysis_outputs/human_annotation_item_summary.csv`

结果可写入论文 supplement 或 M02 后续独立论文。
