# M03 Main100 Results

日期：2026-06-04

## 实验设置

方向：M03，AI 艺术风格输入对 image-to-3D 几何重建的影响。

本轮从 30-object pilot 扩展到 100-object 主实验：

- 数据源：Objaverse；
- 样本：curated 100 objects；
- 许可证：仅保留 `by` / `by-sa`；
- 样本筛选：剔除过大 mesh、极低复杂度 mesh、明显 IP/商标/人物/场景/集合类样本；
- baseline：TripoSR；
- 风格输入：`photo`、`edge`、`flat`、`low_detail`、`sketch`、`watercolor`；
- 总重建数：100 objects × 6 styles = 600；
- 成功重建：600；
- 失败：0；
- 输出 mesh：全部 watertight。

## 文件

远程：

```text
/root/autodl-tmp/m03/datasets/objaverse_main100/main100_manifest.json
/root/autodl-tmp/m03/datasets/objaverse_main100_gt_curated/summary.json
/root/autodl-tmp/m03/outputs/baseline_runs/triposr_objaverse_main100_curated_600/
```

本地同步：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m03_main100_metrics\
```

核心指标文件：

- `main100_manifest.json`
- `main100_gt_summary.json`
- `triposr_main100_summary.json`
- `eval_gt_metrics.csv`
- `eval_gt_aggregate.json`
- `eval_gt_relative_to_photo.json`

## 全局聚合

| style | n | Chamfer L2 mean | F-score@0.05 | F-score@0.1 | volume mean | z extent mean |
|---|---:|---:|---:|---:|---:|---:|
| edge | 100 | 0.0435 | 0.3087 | 0.5163 | 0.0868 | 0.3136 |
| flat | 100 | 0.0398 | 0.3030 | 0.5398 | 0.1360 | 0.5876 |
| low_detail | 100 | 0.0464 | 0.2940 | 0.4953 | 0.0803 | 0.3013 |
| photo | 100 | 0.0467 | 0.2524 | 0.4665 | 0.2790 | 0.6849 |
| sketch | 100 | 0.0366 | 0.3449 | 0.5757 | 0.0685 | 0.5755 |
| watercolor | 100 | 0.0386 | 0.3281 | 0.5496 | 0.0930 | 0.4322 |

## 相对 photo 的配对结果

| style | Chamfer Δ | F@0.05 Δ | volume ratio | z extent ratio | volume Wilcoxon p |
|---|---:|---:|---:|---:|---:|
| edge | -0.0032 | +0.0564 | 0.332 | 0.471 | 3.90e-18 |
| flat | -0.0069 | +0.0506 | 0.500 | 0.879 | 3.75e-17 |
| low_detail | -0.0003 | +0.0416 | 0.305 | 0.451 | 6.44e-18 |
| sketch | -0.0100 | +0.0925 | 0.257 | 0.868 | 4.14e-18 |
| watercolor | -0.0081 | +0.0757 | 0.343 | 0.635 | 3.90e-18 |

`low_detail` 的 volume 检验使用 99 个有效配对样本，因为其中 1 个样本存在 volume NaN。

## 主结论

100-object 主实验支持 30-object pilot 的核心发现：

1. 风格化输入显著压缩 TripoSR 输出 mesh 的体积；
2. `edge`、`low_detail`、`watercolor` 明显降低 z extent，表现为厚度/深度偏差；
3. Chamfer 和 F-score 反而经常优于 `photo` 输入，说明点云距离可能奖励“更薄、更贴近可见轮廓”的错误重建；
4. 因此 M03 的论文叙事应聚焦在“传统几何指标掩盖艺术风格诱发的体积与厚度偏差”。

推荐题目方向：

```text
Style-Induced Volumetric Bias in Image-to-3D Reconstruction:
A Controlled Benchmark on Artistic Input Transformations
```

中文题目：

```text
图像到三维重建中的风格诱导体积偏差：基于艺术化输入变换的受控基准研究
```

## 完成度判断

M03 目前已经具备主实验雏形：

- 公开数据；
- 可复现实验管线；
- 100-object 主实验；
- 显著配对统计；
- 现象有解释性；
- 可以继续补：第二 baseline、视觉/人工可用性评价、多视角渲染检查。

在没有第二 baseline 的情况下，M03 更适合写成“benchmark + phenomenon analysis”论文，而不是“新模型”论文。

## 稳健性实验：mc-resolution=128

为排除 `mc-resolution=64` 低分辨率 mesh extraction 造成假象，额外从 main100 中抽取 30 个对象，使用 TripoSR `mc-resolution=128` 重跑：

- 样本：30 objects；
- 风格：6；
- 重建：180；
- 成功：180；
- 失败：0。

本地同步：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m03_res128_metrics\
```

相对 photo 的配对结果：

| style | Chamfer Δ | F@0.05 Δ | volume ratio | z extent ratio | volume Wilcoxon p |
|---|---:|---:|---:|---:|---:|
| edge | +0.0027 | +0.0301 | 0.377 | 0.461 | 2.98e-08 |
| flat | -0.0029 | +0.0293 | 0.588 | 0.962 | 6.56e-07 |
| low_detail | +0.0062 | +0.0191 | 0.300 | 0.412 | 3.73e-09 |
| sketch | -0.0024 | +0.0685 | 0.340 | 0.918 | 8.94e-08 |
| watercolor | -0.0020 | +0.0493 | 0.390 | 0.675 | 3.73e-09 |

结论：提高 mesh extraction 分辨率后，体积压缩和厚度偏差仍然存在，说明主现象不是 `mc-resolution=64` 的单纯抽 mesh 伪影。
