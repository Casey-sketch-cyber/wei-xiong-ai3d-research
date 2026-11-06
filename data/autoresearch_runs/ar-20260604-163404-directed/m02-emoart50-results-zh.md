# M02 EmoArt-5k Results

日期：2026-06-04

## 方向

M02：二维绘画到三维风格化资产生成中的情感保持性评价。

ArtEmis 正式数据需要人工表单授权，因此本轮补做一个可全自动获取的替代正式实验：使用 HuggingFace 上公开可下载的 EmoArt-5k 图像和情感标注，抽取 50 张绘画，运行 painting-to-3D 重建，再用 CLIP zero-shot 代理指标比较原图与 3D 渲染后的情感分布。

这个实验不能替代 ArtEmis 的人工解释文本实验，但比 M03-output proxy 更接近严格 M02，因为输入是真实绘画图像且带有情感标签。

## 数据与样本

远程数据目录：

```text
/root/autodl-tmp/m03/datasets/emoart5k/
/root/autodl-tmp/m03/datasets/emoart5k_m02_sample50/
```

本地同步目录：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_emoart50_metrics\
```

EmoArt-5k 标注核验：

- 标注样本：5532；
- 可用图像：5532；
- 本轮抽样：50；
- 覆盖情感类别：8。

样本分布：

| dominant emotion | n |
|---|---:|
| Alarmed | 7 |
| Annoyed | 3 |
| Calm | 8 |
| Contentment | 8 |
| Excited | 8 |
| Frustrated | 6 |
| Happy | 3 |
| Sad | 7 |

## 3D 重建设置

- baseline：TripoSR；
- GPU：RTX 5090；
- mesh extraction：`mc-resolution=64`；
- 输入：EmoArt-5k 原始绘画图像；
- 输出：每张图像一个 mesh；
- 成功：50 / 50；
- 失败：0 / 50；
- 平均 forward 时间：0.0961 秒；
- 平均 mesh extraction 时间：0.0297 秒；
- 平均顶点数：4718.16；
- 平均 mesh 体积：0.1808。

远程输出：

```text
/root/autodl-tmp/m03/outputs/m02_emoart50/triposr_runs/
/root/autodl-tmp/m03/outputs/m02_emoart50/eval/
```

核心同步文件：

- `sample50_manifest.csv`
- `triposr_emoart50_summary.json`
- `render_manifest.csv`
- `emoart50_affect_consistency.csv`
- `emoart50_affect_aggregate.json`
- `emoart50_valence_arousal_consistency.csv`
- `emoart50_valence_arousal_aggregate.json`

## 人工审计材料

为后续 SSCI/AHCI 或审稿可信度补强，已自动生成 50 样本人工审计包：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_human_audit_pack\
```

包含：

- `annotation_web.html`：本地打开即可查看每个样本的原图、3D 渲染图、标签和自动代理结果；
- `annotation_items.csv`：50 个样本的元数据；
- `annotation_template.csv`：人工评分模板；
- `analyze_annotations.py`：评分完成后的自动汇总脚本；
- `README-zh.md`：评分说明；
- `images\`：50 对原图/3D 渲染图，共 100 张 PNG。

验证结果：

- `annotation_items.csv`：50 行；
- `annotation_template.csv`：50 行；
- HTML 样本块：50；
- 图像：100 张；
- 图像尺寸检查：全部 512 x 512，未发现坏图。
- 空模板运行 `analyze_annotations.py`：安全返回 `no_completed_scores`，不会生成假人评结论；
- 临时 3 行评分 smoke test：可正常输出总体均值和 item-level summary。

## 情感代理评估

细粒度标签使用 EmoArt-5k 的 8 类 dominant emotion：

```text
Calm, Excited, Contentment, Sad, Alarmed, Frustrated, Happy, Annoyed
```

评价方式：

1. 对原始绘画图像计算 CLIP zero-shot 情感分布；
2. 对 TripoSR mesh 渲染图计算 CLIP zero-shot 情感分布；
3. 比较原图、3D 渲染图和 EmoArt 标签之间的一致性；
4. 计算 render-to-original 的 JS divergence、entropy delta 和 top probability delta；
5. 将细粒度情感进一步映射到 valence/arousal 粗粒度轴，补充审计。

## 细粒度结果

总体结果：

| metric | value |
|---|---:|
| n | 50 |
| render ok | 50 |
| original vs GT top-label match | 0.12 |
| render vs GT top-label match | 0.06 |
| render vs original top-label match | 0.04 |
| JS divergence render-to-original mean | 0.1637 |
| render entropy delta mean | -0.2189 |
| render top probability delta mean | +0.1384 |

按情感类别的 render-to-original JS divergence：

| dominant emotion | n | orig-GT match | render-GT match | render-original match | JS mean |
|---|---:|---:|---:|---:|---:|
| Alarmed | 7 | 0.1429 | 0.0000 | 0.2857 | 0.1230 |
| Annoyed | 3 | 0.0000 | 1.0000 | 0.0000 | 0.1644 |
| Calm | 8 | 0.0000 | 0.0000 | 0.0000 | 0.1673 |
| Contentment | 8 | 0.1250 | 0.0000 | 0.0000 | 0.1864 |
| Excited | 8 | 0.0000 | 0.0000 | 0.0000 | 0.1858 |
| Frustrated | 6 | 0.5000 | 0.0000 | 0.0000 | 0.1604 |
| Happy | 3 | 0.3333 | 0.0000 | 0.0000 | 0.1573 |
| Sad | 7 | 0.0000 | 0.0000 | 0.0000 | 0.1542 |

## Valence/Arousal 粗粒度审计

由于 CLIP zero-shot 对 EmoArt 细粒度标签本身的原图命中率只有 0.12，细粒度结果应被视为弱代理，而不是可靠的人类情绪判断。为避免过度依赖具体 emotion word，补充将标签映射到正负性和唤醒度：

| metric | value |
|---|---:|
| original vs GT valence match | 0.72 |
| render vs GT valence match | 0.46 |
| render vs original valence match | 0.70 |
| original vs GT arousal match | 0.52 |
| render vs GT arousal match | 0.54 |
| render vs original arousal match | 0.94 |

解释：

- 原图 CLIP 对 valence 的粗粒度识别明显强于细粒度 top emotion；
- 3D 渲染后的 valence-GT 一致性从 0.72 降到 0.46，提示 painting-to-3D 会削弱情感正负性线索；
- arousal 的 render-original 一致性很高，但原图和渲染图对 GT 的一致性都一般，说明该代理模型更容易保持自身偏好，而不一定贴合 EmoArt 标注；
- 因此 M02 可以提出“3D 化导致情感线索重编码或丢失”的现象，但投稿前需要人工审计或更强的情感识别器确认。

## 判断

M02 当前已完成两类自动实验：

1. 复用 M03 main100 输出的 600-output affect proxy；
2. 使用 EmoArt-5k 的 50 张真实绘画图像做 painting-to-3D 情感保持实验。

证据足以说明 M02 具备可行的研究现象：从绘画到 3D 资产的转换可能改变情感语义，尤其会降低细粒度 emotion top-label 一致性和 valence 保持性。

但 M02 仍不应被表述为“正式 ArtEmis 论文实验已完成”。当前最稳妥定位是：

- 可作为 M03 的补充实验；
- 可作为 SSCI/AHCI 向的后续扩展方向；
- 若单独作为主线，必须补 ArtEmis/WikiArt 授权数据和人工评分。
