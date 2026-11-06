# M02 Proxy Results

日期：2026-06-04

## 方向

M02：二维绘画到三维风格化资产生成中的情感保持性评价。

严格版 M02 需要 ArtEmis / WikiArt 的绘画情感标签和解释文本。当前核验结果是：ArtEmis 官方数据需要填写表单并接受 Terms of Use，无法在全自动流程里直接绕过。因此本轮做的是 M02 的自动化 proxy 实验，目标是验证评价链路和初步现象，而不是声称已完成 ArtEmis 正式实验。

## Proxy 实验设置

复用 M03 main100 的 3D 输出：

- 样本：100 个 Objaverse 对象；
- 风格：`photo`、`edge`、`flat`、`low_detail`、`sketch`、`watercolor`；
- baseline：TripoSR；
- 3D 输出渲染：600 张；
- 情感代理模型：CLIP zero-shot；
- 情感标签：`amusement`、`awe`、`contentment`、`excitement`、`fear`、`sadness`、`anger`、`disgust`；
- prompt：`a 3D object render that evokes {emotion}`。

远程输出：

```text
/root/autodl-tmp/m03/outputs/m02_proxy/main100_triposr_renders/
```

本地同步：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_proxy_metrics\
```

核心文件：

- `render_manifest.csv`
- `clip_affect_predictions.csv`
- `clip_affect_relative_to_photo.csv`
- `clip_affect_aggregate.json`

## 结果

相对 `photo` 风格的 affect proxy 漂移：

| style | n | top emotion match rate | JS divergence mean | entropy Δ mean | top prob Δ mean |
|---|---:|---:|---:|---:|---:|
| edge | 100 | 0.94 | 0.0210 | +0.0061 | -0.0038 |
| flat | 100 | 0.75 | 0.0240 | +0.0104 | -0.0199 |
| low_detail | 100 | 0.96 | 0.0185 | +0.0188 | -0.0127 |
| sketch | 100 | 0.43 | 0.0404 | +0.0462 | -0.0534 |
| watercolor | 100 | 0.80 | 0.0210 | +0.0447 | -0.0472 |

## 解释

这个 proxy 结果和 M03 的几何结果形成互补：

1. `edge` 和 `low_detail` 在情感 top label 上较稳定，但 M03 显示它们会强烈压缩体积和厚度；
2. `sketch` 的情感 proxy 漂移最大，top emotion match rate 只有 43%；
3. `watercolor` 的 top label 保持率较高，但 top probability 明显下降，说明情感判断置信度降低；
4. 这提示 M02 可以和 M03 形成双指标叙事：同一风格变换可能在几何可用性和情感语义保持上造成不同类型的退化。

## 当前状态

M02 已完成：

- 评价指标草案；
- 人工评价 rubric；
- ArtEmis 数据访问核验；
- 600-output proxy 渲染；
- CLIP affect proxy 指标；
- 相对 photo 的 affect drift 聚合。

M02 未完成：

- ArtEmis 正式绘画情感标注实验；
- WikiArt 原画抽样；
- 人工评价；
- 2D painting → 3D asset 的严格配对实验。

原因：ArtEmis 数据需要人工表单授权，这一步不能由全自动流程替代。

## 判断

M02 可以作为 M03 的补充方向或后续 SSCI/AHCI 扩展，但不建议现在作为主线论文。当前主线应继续 M03，因为 M03 已有公开数据、真实 GT、100-object 主实验和显著统计。
