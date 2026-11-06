# ArtEmis 访问实时核验记录

日期：2026-06-04

用途：记录 M02 严格版实验仍需人工/授权动作的原因，避免把受限数据误写成已经自动完成。

## 联网核验结论

- ArtEmis 官网：`https://artemisdataset.org/`
- 官方 Dataset 说明：下载 ArtEmis 数据集需要填写官方 Google Form，并接受 Terms of Use。
- 官方页面列出的规模：约 455K emotion attribution / explanation，覆盖约 80K WikiArt artworks。
- 官方联系邮箱：`artemis.dataset@gmail.com`

## 对当前实验状态的影响

当前 M02 已完成：

- EmoArt-5k 公开数据 smoke/mainline proxy：50 paintings，50/50 TripoSR 成功；
- M03 输出上的 600 rendered 3D outputs affect proxy；
- 50 条真人评价样本包、浏览器评分工具、评分分析脚本；
- ArtEmis 授权申请模板、评价者邀请/同意/伦理材料。

当前 M02 不能自动宣称完成：

- 未获得 ArtEmis/WikiArt Terms of Use 下的正式授权记录；
- `D:\AutoResearch\data\restricted\artemis` 尚不存在；
- 尚未回收至少 2 名真人评价者的完整评分 CSV。

## 当前验收命令

```powershell
cd D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed
python check_external_steps.py
python verify_experiment_package.py
```

预期状态：

- `check_external_steps.py`：`overall_status = pending_external_or_human_steps`
- `verify_experiment_package.py`：自动实验包 `status = pass`，但列出剩余 human/external steps

## 授权完成后放置约定

获得官方授权后，把数据和授权记录放到：

```text
D:\AutoResearch\data\restricted\artemis
```

建议至少包含：

- ArtEmis annotation 数据文件；
- WikiArt 图像或可合法访问的图像引用；
- Terms of Use / authorization record；
- 数据来源、下载日期、使用限制说明。

