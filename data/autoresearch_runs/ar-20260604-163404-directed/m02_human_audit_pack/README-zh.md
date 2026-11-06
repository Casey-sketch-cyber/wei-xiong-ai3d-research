# M02 Human Audit Pack

日期：2026-06-04

用途：对 EmoArt-5k 真实绘画到 TripoSR 3D 渲染结果做小规模人工评价。

## 文件

- `annotation_web.html`：本地打开，逐项查看原图、3D 渲染图、标签和自动代理结果。
- `rating_tool.html`：本地交互式评分工具，可点击 1-5 分并导出 CSV。
- `RATER_QUICKSTART-zh.md`：给评价者的最短操作说明。
- `annotation_items.csv`：样本元数据和图像路径。
- `annotation_template.csv`：人工评分模板。
- `analyze_annotations.py`：评分完成后的自动汇总脚本。
- `generate_rating_tool.py`：从 `annotation_items.csv` 重新生成 `rating_tool.html`。
- `images/`：50 个样本的原图和 3D 渲染图。
- `rater_exports/`：建议放置评价者导出的 CSV。
- `rater_tracking.csv`：评价者发送、同意、CSV 回收状态追踪表。
- `rater_followup_messages-zh.md`：发送评分包和催收 CSV 的中文消息模板。

## 评分建议

- 每个维度 1-5 分，1 表示完全不保留或不可用，5 表示明显保留或可用。
- 至少 2 名评价者，各自填写一份模板。
- 当前包不包含 ArtEmis 正式 explanation，因为 ArtEmis 数据需要人工表单授权。这里使用 EmoArt-5k 的 `description` 和 `emotional_impact` 字段作为替代审计依据。

## 推荐流程

1. 每位评价者打开 `rating_tool.html`。
2. 填写自己的 `annotator_id`，例如 `rater01`。
3. 查看每个样本并点击 1-5 分，可选填写文字说明。
4. 点击 `Export CSV`，导出 `annotation_rater01.csv`、`annotation_rater02.csv` 等，并放入 `rater_exports/`。
5. 如需手工填写，也可以复制一份 `annotation_template.csv`。
6. 在 `annotation_web.html` 中查看只读样本展示。
7. 所有分数字段必须完整填写；脚本会拒绝只填一部分分数的样本，避免统计口径混乱。
8. 评分完成后，在本目录运行：

```powershell
python analyze_annotations.py rater_exports\annotation_rater01.csv rater_exports\annotation_rater02.csv
```

## 输出

- `analysis_outputs/human_annotation_summary.json`：总体均值、标准差、评分者数、与自动 JS divergence 的 Spearman 相关。
- `analysis_outputs/human_annotation_item_summary.csv`：逐样本均值和标准差，可用于画图或论文表格。

如果直接对空模板运行脚本，它会安全退出并提示 `no_completed_scores`，不会生成假结果。
