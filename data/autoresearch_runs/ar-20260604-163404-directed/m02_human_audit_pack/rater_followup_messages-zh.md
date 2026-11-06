# M02 评价者联系模板

日期：2026-06-05

## 发送评分包

你好，我这里有一个小规模学术研究评分任务，内容是比较 50 组绘画原图和 AI 生成的 3D 渲染图，判断情感、风格和视觉证据是否被保留。

请解压 `M02_rater_package.zip`，先阅读 `RATER_QUICKSTART-zh.md` 和 `rater_consent_template-zh.md`，然后用浏览器打开 `rating_tool.html` 开始评分。

完成后点击 `Export CSV`，导出文件请命名为：

```text
annotation_raterXX.csv
```

其中 `XX` 是你的评价者编号。请把导出的 CSV 发回给我。

## 催收提醒

你好，提醒一下 M02 绘画到 3D 的评分 CSV。完成后请从 `rating_tool.html` 点击 `Export CSV`，把导出的 `annotation_raterXX.csv` 发回即可。

如果中途关闭了浏览器，评分工具会保存本地进度；重新打开 `rating_tool.html` 后可以继续。

## 回收后放置

收到 CSV 后放到：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_human_audit_pack\rater_exports\
```

然后运行：

```powershell
cd D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed
python check_external_steps.py
python run_m02_strict_followup.py
```

当至少 2 份 CSV 完整时，`run_m02_strict_followup.py` 会自动运行人评统计。

