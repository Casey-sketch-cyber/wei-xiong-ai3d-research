# M02 并行研究包

日期：2026-06-04  
Run ID：`ar-20260604-163404-directed`  
并行方向：M02  

## 工作题目

中文：

> 面向 AI 艺术资产生成的情感保持性评价：从二维绘画到三维风格化资产

英文：

> Emotion-Preserving 2D-to-3D Art Asset Generation: Evaluating Affective Consistency from Paintings to Stylized 3D Assets

## 当前定位

M02 不作为第一 GPU 主线，避免和 M03 抢远程算力。它先进入轻量准备阶段：

1. 明确和 ArtEmis / EmoArt / AGSR / Emo3D 的差异；
2. 建立公开数据可用性表；
3. 设计 emotion preservation 指标；
4. 准备后续小规模人工评价 rubric；
5. 等 M03 pilot 跑通后，再决定是否分配 GPU 资源。

## 不能这样写

不要把创新点写成：

- “首次研究 AI 艺术情感理解”；
- “首次做艺术情感解释”；
- “首次做 3D 情感 avatar”；
- “首次用 MLLM 评价艺术情感”。

这些方向已有明显相关工作：

- ArtEmis：2D 艺术情感标注和解释；
- EmoArt：emotion-aware artistic generation；
- AGSR：艺术情感理解中的属性证据和选择性推理；
- Emo3D / EmoTaG / EMOCA 系列：3D 人脸、avatar 或 talking head 情感表达。

## 可保留的新命题

> 二维绘画中的情感语义和解释性视觉证据，在生成或迁移到三维风格化资产之后，是否仍然保持？

关键差异：

- 研究对象不是 2D artwork understanding，而是 2D-to-3D art asset generation；
- 评价目标不是单张图像情感分类，而是多视角 3D 渲染后的情感一致性；
- 关注解释证据是否保留，例如色调、构图、孤立主体、压迫空间、明暗对比等；
- 可以同时服务 SCI 的 automatic evaluation 和 SSCI/AHCI 的艺术解释。

## 数据候选

| 数据 | 用途 | 优点 | 风险 |
|---|---|---|---|
| ArtEmis | 2D 绘画情感标签和解释 | 公开、经典、和题目高度相关 | 只覆盖 2D 艺术理解 |
| EmoArt | 2D 艺术情感生成/评价 | 更新、情绪维度更丰富 | 需要确认许可和下载流程 |
| WikiArt | 风格和画作来源 | 覆盖广 | 情感标签弱，需要配合 ArtEmis |
| Objaverse 子集 | 3D 资产对象 | 可作为通用 3D 资产来源 | 需要筛选适合艺术化的类别 |

## 指标草案

1. Emotion label consistency  
   2D 原画和 3D 多视角渲染的 emotion 分类是否一致。

2. Affective embedding similarity  
   使用艺术情感模型或 MLLM 输出的情感描述计算相似性。

3. Explanation evidence preservation  
   原画解释中提到的视觉证据，在 3D 渲染视角中是否仍可见。

4. Multi-view affective stability  
   同一 3D 资产不同视角是否给出一致情感判断。

5. Human-model agreement  
   小规模人工评价与自动指标是否一致。

## 最小可行实验

- 选择 30 张 ArtEmis / WikiArt 绘画，覆盖 5-6 类情绪；
- 为每张图生成或匹配一个 3D 风格化资产；
- 渲染 4-8 个视角；
- 用 MLLM / 情感分类器评估 2D 输入和 3D 输出的一致性；
- 人工标注 30 * 2 或 30 * 4 个样本作为 sanity check。

## 与 M03 的资源分工

- M03：先用远程 GPU，跑 3D baseline、渲染和几何评价；
- M02：先做本地文献表、数据表、指标和人工评价表；
- 等 M03 pilot 完成后，如果 M02 需要 3D 生成，再复用 M03 的 pipeline。

## 当前 verdict

`PARTIAL-OPEN`

M02 相关工作很多，但只要命题压到“2D 绘画情感语义在 3D 艺术资产中的保持性”，仍然有研究空间。它更适合偏 SSCI/AHCI 或数字人文，也可以通过自动指标和多视角评价转成 SCI Q2。
