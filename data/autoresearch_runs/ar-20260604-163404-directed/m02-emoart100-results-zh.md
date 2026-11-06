# M02 EmoArt-100 Robustness Results

日期：2026-06-04

## 目的

在原 M02 EmoArt-5k 50 样本实验基础上，追加一个 100 张真实绘画的公开数据 robustness run，检查“painting-to-3D 后情感线索被削弱或重编码”的代理现象是否仍然成立。

该实验仍然是自动代理实验，不等同于正式 ArtEmis/WikiArt 授权实验，也不替代真人评分。

## 数据与路径

数据源：

```text
HuggingFace: printblue/EmoArt-5k
```

远程路径：

```text
/root/autodl-tmp/m03/datasets/emoart5k/
/root/autodl-tmp/m03/datasets/emoart5k_m02_sample100/
/root/autodl-tmp/m03/outputs/m02_emoart100/triposr_runs/
/root/autodl-tmp/m03/outputs/m02_emoart100/eval/
```

本地指标：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m02_emoart100_metrics\
```

## 抽样

100 张样本按 8 类 dominant emotion 分层抽样：

| emotion | n |
|---|---:|
| Calm | 16 |
| Excited | 16 |
| Contentment | 16 |
| Sad | 14 |
| Alarmed | 14 |
| Frustrated | 12 |
| Happy | 6 |
| Annoyed | 6 |

抽样脚本：

```text
remote_scripts\m02_prepare_emoart_sample100.py
```

## 3D 重建与渲染

TripoSR 设置：

- model：`stabilityai/TripoSR`
- mc-resolution：64
- chunk-size：4096
- GPU：RTX 5090
- 输入：100 张 512x512 方形白底绘画图像

结果：

| item | value |
|---|---:|
| input paintings | 100 |
| TripoSR success | 100 |
| render success | 100 |

## 细粒度情感代理结果

CLIP zero-shot 使用 8 个 EmoArt dominant emotion prompt，对原图和 3D 渲染图分别预测 top emotion。

| metric | value |
|---|---:|
| original vs GT top-emotion match | 0.17 |
| render vs GT top-emotion match | 0.06 |
| render vs original top-emotion match | 0.04 |
| mean JS divergence, render vs original | 0.1687 |
| mean entropy delta, render - original | -0.2283 |
| mean top-prob delta, render - original | 0.1495 |

按 emotion 分组：

| emotion | n | orig-GT | render-GT | render-orig | mean JS |
|---|---:|---:|---:|---:|---:|
| Alarmed | 14 | 0.2857 | 0.0000 | 0.2143 | 0.1323 |
| Annoyed | 6 | 0.0000 | 1.0000 | 0.0000 | 0.2063 |
| Calm | 16 | 0.0625 | 0.0000 | 0.0000 | 0.1673 |
| Contentment | 16 | 0.1875 | 0.0000 | 0.0000 | 0.1939 |
| Excited | 16 | 0.0625 | 0.0000 | 0.0000 | 0.1764 |
| Frustrated | 12 | 0.3333 | 0.0000 | 0.0833 | 0.1603 |
| Happy | 6 | 0.6667 | 0.0000 | 0.0000 | 0.1869 |
| Sad | 14 | 0.0000 | 0.0000 | 0.0000 | 0.1524 |

## Valence/Arousal 粗粒度审计

为降低对细粒度 emotion word 的依赖，将 8 类 emotion 映射到 valence/arousal 轴。

| metric | value |
|---|---:|
| original vs GT valence match | 0.67 |
| render vs GT valence match | 0.46 |
| render vs original valence match | 0.69 |
| original vs GT arousal match | 0.53 |
| render vs GT arousal match | 0.54 |
| render vs original arousal match | 0.91 |

关键观察：

- 100 样本中，原图对 GT 的 valence match 为 0.67，3D 渲染对 GT 的 valence match 为 0.46；
- 这与 50 样本实验的 0.72 -> 0.46 方向一致，说明 valence drop 不是 50 样本偶然现象；
- render-vs-original arousal match 为 0.91，说明该代理模型容易保持自己的高/低唤醒偏好，但不一定贴合 GT 情感标签；
- 细粒度 render-vs-original top-emotion match 只有 0.04，说明 3D 化后的情感 top label 大幅漂移。

## 结论边界

可以支持：

- M02 的公开数据代理证据增强：100 张真实绘画经 TripoSR 3D 化后，自动情感代理指标显示 valence 保持性下降；
- M02 与 M03 主线互补：M03 关注几何坍缩与指标悖论，M02 补充说明艺术/绘画到 3D 还可能带来情感语义漂移。

不能声称：

- 不能声称 ArtEmis/WikiArt 正式授权实验已经完成；
- 不能把 CLIP zero-shot 结果等同于真人情感判断；
- 不能声称已经完成投稿级人类评价。

下一步仍然是：

1. 回收至少 2 名评价者的人评 CSV；
2. 获得 ArtEmis/WikiArt 授权后，按 `m02_external_steps_pack\post_artemis_data_plan-zh.md` 跑正式数据实验。

