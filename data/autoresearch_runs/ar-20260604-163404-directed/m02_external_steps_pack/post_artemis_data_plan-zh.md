# ArtEmis 授权数据接入计划

日期：2026-06-04

## 前提

只有在完成 ArtEmis 官方表单、接受 Terms of Use 并获得数据访问权限后，才执行本计划。

## 建议数据放置

不要把 ArtEmis 原始数据提交到公开仓库。建议放置在受控本地或远程目录：

```text
D:\AutoResearch\data\restricted\artemis\
```

或远程：

```text
/root/autodl-tmp/m03/restricted/artemis/
```

## 接入步骤

1. 保存官方 Terms of Use 和授权记录。
2. 放置 ArtEmis raw CSV / annotations 文件。
3. 记录 WikiArt 图像路径或访问方式。
4. 使用 ArtEmis 官方代码仓库中的 preprocess 工具生成研究子集。
5. 抽取 30-100 个 artwork，覆盖至少 5 类 emotion。
6. 对每个 artwork 生成或选择 3D 输出及渲染图。
7. 计算：
   - emotion label consistency；
   - explanation evidence preservation；
   - image/text affect proxy；
   - human-model agreement。
8. 将正式 ArtEmis 结果与当前 EmoArt-5k proxy 结果分开报告。

## 需要新增的产物

授权后建议新增：

```text
m02_artemis_authorized_metrics\
m02-artemis-authorized-results-zh.md
m02_artemis_human_audit_pack\
```

## 论文表述边界

授权完成前：

> We use EmoArt-5k as an automatically accessible proxy and prepare ArtEmis-based evaluation as future authorized work.

授权完成后：

> We further validate the affect-preservation protocol on an authorized ArtEmis/WikiArt subset with human explanations.

