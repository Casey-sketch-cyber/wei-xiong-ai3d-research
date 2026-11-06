# Paper Claim-Evidence Matrix

日期：2026-06-04

用途：把 M03/M02 已完成实验转成论文写作时可安全使用的主张、证据、限制和图表入口。该文件不是论文正文，而是写作前的证据边界表。

## 推荐主线

建议以 M03 作为主线论文：

> Style-induced geometry collapse in single-image 3D reconstruction: artistic abstractions can improve conventional point metrics while degrading volumetric usability.

中文表述：

> 艺术化输入会诱导 image-to-3D 输出出现体积和厚度坍缩；传统 Chamfer/F-score 指标有时反而给出更好结果，从而掩盖 3D 资产可用性退化。

M02 建议作为补充实验或 discussion：

> Affective proxy signals suggest that geometry degradation and affective drift are not always aligned; painting-to-3D conversion may re-encode or weaken affective cues, but strict ArtEmis/WikiArt and human-rating evidence is still pending.

中文表述：

> 自动情感代理指标显示，几何退化和情感语义漂移并不总是同向；绘画到 3D 的转换可能削弱或重编码情感线索，但严格 ArtEmis/WikiArt 和真人评分证据尚未完成。

## 可安全声称的主张

| id | claim | evidence | strength | safe wording |
|---|---|---|---|---|
| C-M03-1 | M03 主实验中，风格化输入显著压缩 TripoSR 输出 mesh 的体积和 z 厚度。 | `m03_main100.csv`; `m03_main100_volume_z_ratios.svg`; `m03-main100-results-zh.md` | strong | On the curated Objaverse-100 benchmark, all artistic styles produce lower predicted volume than photo inputs, with Wilcoxon p-values around 1e-17 to 1e-18. |
| C-M03-2 | Chamfer/F-score 可能和 3D 资产可用性发生指标分歧。 | `m03_main100.csv`; `m03_main100_metric_paradox.svg` | strong | Several stylized inputs improve Chamfer or F-score relative to photo while simultaneously shrinking volume and z-extent. |
| C-M03-3 | 体积/厚度坍缩不是 `mc-resolution=64` 的单一抽 mesh 伪影。 | `m03_res128.csv`; `m03_res128_volume_z_ratios.svg` | moderate-to-strong | The res128 rerun on 30 objects preserves the same volume/z-extent shrinkage pattern. |
| C-M03-4 | 当前证据支持把 M03 写成评估/诊断型论文，而不是新生成模型论文。 | `experiment_summary_table.csv`; `experiment-completion-audit-zh.md` | strong | We propose an evaluation protocol and empirical diagnosis for style-induced geometry collapse. |
| C-M02-1 | M02 proxy 显示不同风格的 affect drift 和 geometry degradation 不完全同向。 | `m02_proxy.csv`; `m02_proxy_affect_drift.svg`; `m02-proxy-results-zh.md` | moderate | In the M03-output affect proxy, sketch has the largest affect drift, whereas edge/low_detail remain affect-stable but geometrically degraded. |
| C-M02-2 | EmoArt-5k/EmoArt-100 真实绘画到 3D 的自动代理实验发现细粒度情感一致性下降。 | `m02_emoart_summary.csv`; `m02_emoart100_summary.csv`; `m02_emoart50_affect_summary.svg`; `m02_emoart100_affect_summary.svg`; `m02-emoart50-results-zh.md`; `m02-emoart100-results-zh.md` | moderate proxy | On 50 and 100 EmoArt paintings, CLIP fine-label match is low after 3D rendering, but this should be interpreted as a proxy signal. |
| C-M02-3 | 粗粒度 valence 指标显示 3D 渲染相对 GT 的 valence match 在 50 和 100 样本上均下降到 0.46。 | `m02_emoart_va.csv`; `m02_emoart100_va.csv`; `m02_emoart50_affect_summary.svg`; `m02_emoart100_affect_summary.svg` | moderate proxy | The coarse valence audit suggests affective cues may be weakened or re-encoded by painting-to-3D conversion, with the 100-sample run strengthening robustness. |
| C-M02-4 | M02 已具备可执行的人评包和评分后统计脚本。 | `m02_human_audit_pack\`; `analyze_annotations.py`; `audit_pack_summary.json` | procedural strong | Human evaluation materials are prepared, but human scores are not yet collected. |

## 不能声称的内容

| id | unsafe claim | reason | required evidence before use |
|---|---|---|---|
| U-1 | “M02 已完成正式 ArtEmis/WikiArt 实验。” | ArtEmis 正式数据需要人工表单授权，当前未获得或未使用正式 ArtEmis 标注实验。 | ArtEmis/WikiArt 授权数据、样本清单、正式 2D-to-3D 结果、评估脚本输出。 |
| U-2 | “M02 已证明 3D 化会真实改变人类情绪感知。” | 当前主要是 CLIP zero-shot proxy，真人评分尚未完成。 | 至少 2 名评价者评分，评分统计与一致性检验。 |
| U-3 | “提出了新的 image-to-3D 模型。” | 当前使用 TripoSR baseline，贡献是评估和诊断，不是新模型。 | 新模型架构、训练或优化实验。 |
| U-4 | “结论适用于所有 3D 生成模型。” | 当前主实验只有 TripoSR，一个 baseline。 | 第二 baseline 或更多模型复现实验。 |
| U-5 | “SVG 图就是投稿最终图。” | 当前 SVG 是无依赖 fallback 草图。 | 投稿前按期刊格式转为高质量 PDF/PNG 并统一字体/线宽。 |

## 图表入口

| figure/table | purpose | main message |
|---|---|---|
| `experiment_summary_table.csv` | 总览 | 五个已完成自动实验及其规模、输出数、核心发现。 |
| `m03_main100_volume_z_ratios.svg` | M03 主图 | 所有风格相对 photo 都出现体积缩小，多个风格同时 z 厚度明显下降。 |
| `m03_main100_metric_paradox.svg` | M03 核心悖论图 | Chamfer/F-score 可改善，但 volume ratio 下降，说明常规指标可能掩盖可用性退化。 |
| `m03_res128_volume_z_ratios.svg` | M03 鲁棒性图 | 提高 mesh extraction 分辨率后，体积/厚度退化仍存在。 |
| `m02_proxy_affect_drift.svg` | M02 补充图 | affect proxy 漂移在 sketch 上最强，和 M03 几何退化模式不完全重合。 |
| `m02_emoart50_affect_summary.svg` | M02 替代正式实验图 | EmoArt-5k 真实绘画到 3D 后，细粒度情感一致性弱，valence proxy 下降。 |
| `m02_emoart100_affect_summary.svg` | M02 robustness 图 | 100 张 EmoArt 绘画复核 valence proxy 下降，增强 M02 公开数据代理证据。 |

## 写作结构建议

1. Introduction：提出艺术化输入在 image-to-3D 中可能带来“视觉指标好、几何资产差”的隐蔽失败。
2. Related Work：覆盖 single-image 3D reconstruction、stylized/abstract inputs、3D evaluation metrics、art affect datasets。
3. Method：说明 Objaverse-100 curated benchmark、style transforms、TripoSR baseline、GT rendering/sampling、geometry metrics 和 volumetric diagnostics。
4. Results M03：主打 main100 + res128，围绕 metric paradox 和 geometry collapse。
5. Supplement M02：报告 affect proxy、EmoArt-5k 与 EmoArt-100 自动代理实验，强调它是补充和未来人评方向。
6. Limitations：单 baseline、SVG 草图、人评未完成、ArtEmis 授权待完成。
7. Conclusion：强调评估协议和诊断发现，不声称新模型。

## 当前完成度判断

M03：实验完成，可进入论文草稿阶段。

M02：自动实验、EmoArt-5k/EmoArt-100 替代数据实验、人评材料、评分后统计脚本和图表均已完成；正式 ArtEmis/WikiArt 授权实验和真人评分仍是外部人工步骤。
