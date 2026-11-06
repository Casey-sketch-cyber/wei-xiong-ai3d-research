# ArtEmis 数据访问申请模板

日期：2026-06-04

## 官方入口

- ArtEmis 官网：`https://artemisdataset.org/`
- 数据下载入口：官网 Dataset 小节中的表单链接，需要接受 Terms of Use。
- 联系邮箱：`artemis.dataset@gmail.com`
- 代码仓库：`https://github.com/optas/artemis`

## 填写表单时的研究说明草稿

中文草稿：

> 我们正在开展一项关于二维艺术图像到三维资产生成的研究，目标是评估绘画情感语义在 3D 转换过程中的保持性。我们希望使用 ArtEmis 的 artwork-emotion-explanation 标注作为研究评估信号，抽取小规模研究子集，比较原始二维绘画、生成的三维资产渲染图，以及人类情感标签/解释之间的一致性。数据仅用于非商业学术研究，不会公开再分发 ArtEmis 原始数据、WikiArt 图像或受限标注文件。论文中会按 ArtEmis 官方要求引用数据集和相关论文，并遵守 Terms of Use。

English draft:

> We are conducting a non-commercial academic study on emotion preservation when two-dimensional artworks are converted into three-dimensional assets. We would like to use the ArtEmis artwork-emotion-explanation annotations as evaluation signals for a small research subset, comparing the original 2D artworks, rendered views of generated 3D assets, and human emotion/explanation annotations. The data will be used only for academic research. We will not redistribute the original ArtEmis data, WikiArt images, or restricted annotation files. We will cite ArtEmis and comply with the official Terms of Use.

## 项目信息建议

- Project title: `Affective Preservation and Geometry Collapse in Artwork-to-3D Asset Generation`
- Dataset use: evaluation only, small research subset, no redistribution.
- Data storage: local/remote research workspace under controlled access.
- Planned outputs: aggregate metrics, anonymized/aggregated statistics, no raw dataset redistribution.
- Citation: ArtEmis: Affective Language for Visual Art.

## 风险边界

- 不要把未授权 ArtEmis 数据放入公开仓库。
- 不要公开再分发 WikiArt 原图或 ArtEmis 原始标注文件。
- 未拿到授权前，论文中只能把当前 EmoArt-5k 实验表述为替代/代理实验。
- 若表单或 Terms of Use 要求额外限制，以官方条款为准。

