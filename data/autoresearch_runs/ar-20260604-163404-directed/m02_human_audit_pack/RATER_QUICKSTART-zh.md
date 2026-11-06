# M02 评价者快速说明

日期：2026-06-04

## 你需要做什么

请打开本目录中的：

```text
rating_tool.html
```

在浏览器中逐项比较原图和 3D 渲染图，并对 6 个维度打 1-5 分。

## 评分含义

- 1：几乎完全不保留，或明显不可用。
- 3：部分保留，但有明显问题。
- 5：保留较好，或整体可用。

请按自己的直观判断评分，不需要追求和其他评价者一致。

## 导出结果

完成后点击页面里的 `Export CSV`。

建议文件名：

```text
annotation_rater01.csv
annotation_rater02.csv
annotation_rater03.csv
```

请把导出的 CSV 放到：

```text
rater_exports\
```

如果浏览器自动下载到了其他位置，也可以把 CSV 移到这个目录。

## 注意

- 每个样本 6 个分数字段都需要填写。
- 可以填写文字说明，但不是必填。
- 不要修改 `sample_id`、`request_id` 等元数据列。
- 如果评分中途暂停，`rating_tool.html` 会用浏览器 localStorage 保存进度。

