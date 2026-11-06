# M02 数据访问表与人工评价 Rubric

日期：2026-06-04  
方向：M02，二维绘画到三维风格化资产生成中的情感保持性评价

## 数据访问表

| 数据源 | 角色 | 获取方式 | 公开性 | 预期规模 | 许可/注意事项 | 当前决策 |
|---|---|---|---|---|---|---|
| ArtEmis | 核心 2D 绘画情感标签和解释 | 官方站点 / GitHub / 论文附属数据 | 公开研究数据 | 约 80K+ artwork-emotion-explanation 标注 | 需核对原始 WikiArt 图像使用条款；论文中引用 ArtEmis | 首选 |
| WikiArt | 画作图像和风格/流派来源 | WikiArt 或 ArtEmis 引用索引 | 公开可访问但需注意使用条款 | 按 ArtEmis 子集抽样 | 图像版权/使用条款需谨慎，只做研究评估 | 首选但不大规模再分发 |
| EmoArt | 更现代的情感艺术生成/评价参照 | arXiv / 项目页待核实 | 公开程度待确认 | 待核实 | 需确认下载链接、标注字段、许可证 | 备选 |
| Objaverse 子集 | 3D 资产来源或类别锚点 | Objaverse / curated subset | 公开研究数据 | 30-300 objects pilot/main | 数据量大，必须只取小子集 | 与 M03 复用 |
| M03 渲染资产 | M02 的 3D 多视角输出 | 从 M03 pipeline 产生 | 自建衍生数据 | 30 paintings/assets 起步 | 记录生成模型、prompt、seed、视角 | 后续复用 |

## 最小验证集设计

目标不是马上证明完整论文，而是判断 M02 是否有稳定现象：

- 画作数量：30 张；
- 情感类别：至少 5 类，例如 awe、contentment、sadness、fear、amusement 或 ArtEmis 中高频类别；
- 每张画作保留：
  - artwork id；
  - emotion label；
  - human explanation；
  - style/genre 元数据，如果可用；
  - 图像路径或 URL；
  - 生成 3D asset 的 prompt / pipeline / seed；
  - 4-8 个 3D 渲染视角。

## 自动指标草案

| 指标 | 输入 | 输出 | 用途 |
|---|---|---|---|
| Emotion label consistency | 原画 + 多视角渲染 | 原情感标签是否保持 | 主指标之一 |
| Affective explanation similarity | ArtEmis explanation + MLLM 生成解释 | 文本相似度 / entailment | 判断解释语义是否保留 |
| Visual-evidence preservation | explanation 中的视觉证据 + 渲染图 | 证据是否仍可见 | 防止“情绪词套话” |
| Multi-view affective stability | 同一 3D asset 的多视角 | 视角间情绪预测方差 | 检查 3D 资产是否稳定表达情感 |
| Human-model agreement | 人工评分 + 自动评分 | 相关性 / 一致率 | 支撑 SSCI/AHCI 或审稿可信度 |

## 人工评价 Rubric

每个样本给评价者展示：

1. 原始二维绘画；
2. 原始情感标签；
3. 原始 ArtEmis 解释；
4. 3D 资产的 4 个固定视角渲染。

评价者回答以下问题，建议 1-5 分：

| 维度 | 问题 | 评分含义 |
|---|---|---|
| 情感保持 | 3D 资产是否保留了原画的主要情绪？ | 1 完全不保留，5 明显保留 |
| 解释证据保持 | 原解释中提到的视觉证据是否仍能在 3D 视角中看到？ | 1 看不到，5 很清楚 |
| 风格保持 | 3D 资产是否保留原画的主要艺术风格/氛围？ | 1 不像，5 很像 |
| 几何可用性 | 3D 资产是否像一个可用的三维对象，而不是只像贴图或碎片？ | 1 不可用，5 可用 |
| 多视角稳定 | 不同视角下的情绪和风格是否一致？ | 1 强烈不一致，5 稳定一致 |

可选开放问题：

- 哪个视觉因素最影响你的情绪判断？
- 3D 化之后丢失了什么？
- 3D 化之后新增了什么不该有的情绪或风格线索？

## 与 M03 的接口

M03 产生：

- 3D 重建或生成输出；
- 多视角渲染；
- 几何稳定性指标；
- 风格导致的几何退化类型。

M02 使用：

- 同一套渲染工具；
- 多视角图像；
- 可能复用 M03 的 style variants；
- 但评价目标换成 emotion / affective semantics。

## 当前状态

M02 尚未进入 GPU 实验。已完成实时数据可得性核验：

- ArtEmis 官方页面显示数据集约含 455K annotation / 80K artworks；
- ArtEmis 原始数据下载需要填写官方表单并接受 Terms of Use，不能在当前全自动流程里直接绕过；
- ArtEmis 代码仓库公开，可用于后续 preprocess、emotion classifier、speaker/evaluation 工具；
- 因此 M02 的可自动部分先推进为：数据使用方案、替代数据路径、评价表、自动指标脚本；原始 ArtEmis 标注下载需要人工表单步骤。

核验来源：

- `https://artemisdataset.org/`
- `https://github.com/optas/artemis`

当前完成的是实验前置设计，下一步是：

1. 获取 ArtEmis metadata；
2. 抽取 30 张画作的候选清单；
3. 建立评价表 CSV；
4. 等 M03 渲染/重建工具稳定后生成 3D 输出。

备注：如果暂不做人工表单，M02 可以先复用 M03 的 Objaverse/style pipeline 做方法学原型；但严格的“绘画情感保持”实验仍需要 ArtEmis/WikiArt 标注。

## 追加进展：M02 proxy 实验已完成

在 ArtEmis 正式数据需要人工表单授权的限制下，已完成一个不依赖受限数据的 M02 proxy 实验。

设置：

- 复用 M03 main100 的 TripoSR 输出；
- 将 600 个 3D 输出 mesh 重新渲染为 2D 图像；
- 使用 CLIP zero-shot 情感提示词估计 affect distribution；
- 情感标签：`amusement`、`awe`、`contentment`、`excitement`、`fear`、`sadness`、`anger`、`disgust`；
- 相对 `photo` 计算 top emotion match、JS divergence、entropy delta、top probability delta。

远程输出：

```text
/root/autodl-tmp/m03/outputs/m02_proxy/main100_triposr_renders/
```

本地同步：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_proxy_metrics\
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02-proxy-results-zh.md
```

结果：

| style | n | top emotion match rate | JS divergence mean | entropy Δ mean | top prob Δ mean |
|---|---:|---:|---:|---:|---:|
| edge | 100 | 0.94 | 0.0210 | +0.0061 | -0.0038 |
| flat | 100 | 0.75 | 0.0240 | +0.0104 | -0.0199 |
| low_detail | 100 | 0.96 | 0.0185 | +0.0188 | -0.0127 |
| sketch | 100 | 0.43 | 0.0404 | +0.0462 | -0.0534 |
| watercolor | 100 | 0.80 | 0.0210 | +0.0447 | -0.0472 |

解释：

- `sketch` 对 affect proxy 漂移最大；
- `edge` / `low_detail` 在 affect top label 上较稳定，但 M03 显示它们在几何上强烈压缩体积和厚度；
- 这说明 M02 可以作为 M03 的补充扩展：同一风格变换在几何可用性和情感语义保持上可能有不同退化模式。

严格 M02 仍未完成，因为 ArtEmis 正式绘画情感标注需要人工表单授权。

## 追加进展：EmoArt-5k 替代正式实验完成

在 ArtEmis 正式数据仍需人工表单授权的情况下，已补做一个可全自动获取的真实绘画数据实验。

设置：

- 数据：HuggingFace `printblue/EmoArt-5k`；
- 标注核验：5532 条标注，5532 张图像可用；
- 本轮抽样：50 张真实绘画；
- 覆盖情感：`Calm`、`Excited`、`Contentment`、`Sad`、`Alarmed`、`Frustrated`、`Happy`、`Annoyed`；
- painting-to-3D baseline：TripoSR；
- 成功重建：50 / 50；
- 失败：0 / 50；
- 评价：CLIP zero-shot 细粒度 emotion proxy + valence/arousal 粗粒度审计。

远程输出：

```text
/root/autodl-tmp/m03/datasets/emoart5k/
/root/autodl-tmp/m03/datasets/emoart5k_m02_sample50/
/root/autodl-tmp/m03/outputs/m02_emoart50/triposr_runs/
/root/autodl-tmp/m03/outputs/m02_emoart50/eval/
```

本地同步：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_emoart50_metrics\
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02-emoart50-results-zh.md
```

核心结果：

| metric | value |
|---|---:|
| original vs GT top-label match | 0.12 |
| render vs GT top-label match | 0.06 |
| render vs original top-label match | 0.04 |
| JS divergence render-to-original mean | 0.1637 |
| original vs GT valence match | 0.72 |
| render vs GT valence match | 0.46 |
| render vs original valence match | 0.70 |
| render vs original arousal match | 0.94 |

解释：

- EmoArt-5k 实验比 M03-output proxy 更接近严格 M02，因为输入是真实绘画图像且有情感标签；
- CLIP zero-shot 对原图细粒度 EmoArt 标签本身只有 0.12 命中率，因此细粒度指标只能作为弱代理；
- 粗粒度 valence 从原图 0.72 降到渲染图 0.46，提示 3D 化会削弱或重编码绘画中的情感正负性线索；
- M02 当前已具备可行现象，但若单独作为主线论文，仍需要 ArtEmis/WikiArt 授权数据和人工评价。

## 追加进展：M02 人工审计包已生成

为把人工评价 rubric 变成可直接执行的材料，已基于 EmoArt-5k 的 50 个样本生成审计包：

## 追加进展：EmoArt-100 robustness 完成

为检查 50 样本结果是否稳定，已追加 100 张真实绘画的公开数据 robustness run：

- 数据：HuggingFace `printblue/EmoArt-5k`；
- 抽样：100 张真实绘画，覆盖 8 个 dominant emotion；
- TripoSR：100 / 100 成功；
- 渲染：100 / 100 成功；
- 细粒度 CLIP proxy：original-vs-GT top match 0.17，render-vs-GT top match 0.06；
- 粗粒度 valence proxy：original-vs-GT 0.67，render-vs-GT 0.46；
- 结论：与 50 样本 0.72 -> 0.46 的 valence drop 方向一致，可作为 M02 自动代理证据的 robustness。

本地结果：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_emoart100_metrics\
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02-emoart100-results-zh.md
```

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_human_audit_pack\
```

包含：

- `annotation_web.html`：逐样本展示原图、3D 渲染图、标签、描述、情感影响文本和自动代理结果；
- `annotation_items.csv`：样本元数据；
- `annotation_template.csv`：人工评分模板；
- `analyze_annotations.py`：评分完成后的自动统计脚本；
- `README-zh.md`：评分说明；
- `images\`：50 对原图和 3D 渲染图。

验证：

- 样本块：50；
- CSV 模板行数：50；
- 图像：100 张；
- 图像尺寸：全部 512 x 512；
- 坏图：0。
- 空模板运行分析脚本：返回 `no_completed_scores`；
- 临时 3 行评分 smoke test：通过。

这一步完成的是人工评价材料准备；真正的人工评分仍需要评价者填写 `annotation_template.csv`。
