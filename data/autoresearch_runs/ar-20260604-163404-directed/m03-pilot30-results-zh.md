# M03 30-Object Pilot Results

日期：2026-06-04

## 实验设置

方向：M03，AI 艺术风格输入对 image-to-3D 几何重建的影响。

远程工作区：

```text
/root/autodl-tmp/m03
```

数据与模型：

- 3D GT：Objaverse curated 30-object pilot；
- 渲染：纯软件三角面片渲染器，生成 `iso` 主视角；
- 风格输入：`photo`、`edge`、`flat`、`low_detail`、`sketch`、`watercolor`；
- baseline：TripoSR；
- 总重建数：30 objects × 6 styles = 180；
- 成功重建数：180；
- 失败数：0；
- TripoSR mesh：全部 watertight。

## 远程与本地文件

远程：

```text
/root/autodl-tmp/m03/datasets/objaverse_pilot30/pilot30_manifest.json
/root/autodl-tmp/m03/datasets/objaverse_pilot30_gt_curated/summary.json
/root/autodl-tmp/m03/outputs/baseline_runs/triposr_objaverse_pilot30_curated_180/
```

本地同步：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m03_remote_metrics\
```

核心文件：

- `pilot30_manifest.json`
- `pilot30_gt_summary.json`
- `triposr_pilot30_summary.json`
- `eval_gt_metrics.csv`
- `eval_gt_aggregate.json`
- `eval_gt_relative_to_photo.json`

## 全局聚合

| style | n | Chamfer L2 mean | F-score@0.05 | F-score@0.1 | volume mean | z extent mean |
|---|---:|---:|---:|---:|---:|---:|
| edge | 30 | 0.0423 | 0.3137 | 0.5286 | 0.0948 | 0.3323 |
| flat | 30 | 0.0390 | 0.3204 | 0.5497 | 0.1351 | 0.5937 |
| low_detail | 30 | 0.0457 | 0.3055 | 0.5151 | 0.0922 | 0.3367 |
| photo | 30 | 0.0442 | 0.2743 | 0.4999 | 0.2729 | 0.6783 |
| sketch | 30 | 0.0370 | 0.3511 | 0.5752 | 0.0613 | 0.6130 |
| watercolor | 30 | 0.0398 | 0.3218 | 0.5411 | 0.0960 | 0.4287 |

## 相对 photo 的配对结果

| style | Chamfer Δ | F@0.05 Δ | volume ratio | z extent ratio | volume Wilcoxon p |
|---|---:|---:|---:|---:|---:|
| edge | -0.0019 | +0.0394 | 0.375 | 0.510 | 3.73e-09 |
| flat | -0.0052 | +0.0461 | 0.460 | 0.890 | 2.61e-08 |
| low_detail | +0.0016 | +0.0312 | 0.350 | 0.517 | 1.86e-09 |
| sketch | -0.0072 | +0.0768 | 0.203 | 0.943 | 1.86e-09 |
| watercolor | -0.0044 | +0.0476 | 0.343 | 0.634 | 1.86e-09 |

## 关键判断

这个 pilot 的结果不是简单的“艺术风格让 Chamfer 变差”。更有论文价值的现象是：

1. 风格化输入会显著改变 TripoSR 输出 mesh 的几何体量和厚度；
2. 这种体量/厚度漂移在 30 个对象上是配对显著的；
3. Chamfer/F-score 有时反而更好，说明传统点云距离可能掩盖了艺术风格导致的资产可用性退化；
4. M03 的创新点可以从“style-induced geometric degradation”收窄为“style-induced volumetric and thickness bias in image-to-3D reconstruction”。

## 当前结论

M03 已经从概念验证推进到可写实验雏形：

- 数据公开可得；
- 3090/5090 级单卡可跑；
- baseline 已跑通；
- GT benchmark 链路已闭环；
- 30-object pilot 有稳定现象；
- 下一步应扩到 100-300 objects，并加入第二 baseline 或更强视觉质量/可用性指标。

## 风险

- 当前渲染器是软件简化渲染，不是物理真实渲染；
- 部分 Objaverse 样本名称含 IP/角色/商标元素，正式论文数据需要重新筛许可证与内容；
- Stable Fast 3D 可能需要 HuggingFace gated 权限，不适合作为当前无 token 的第二 baseline；
- 目前结论更适合投 SCI/SSCI/AHCI 二核心交叉方向的“评价基准/现象分析”，不宜包装成新生成模型。
