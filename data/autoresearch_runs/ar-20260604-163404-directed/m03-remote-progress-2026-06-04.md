# M03 Remote Progress

日期：2026-06-04  
远程工作区：`/root/autodl-tmp/m03`

## 已完成

### 环境

- RTX 5090 可用；
- PyTorch `2.8.0+cu128` 可用；
- 数据盘 `/root/autodl-tmp` 可用，约 750GB；
- 已使用 `source /etc/network_turbo` 和 GitHub proxy 获取 baseline 仓库；
- TripoSR 与 Stable Fast 3D 仓库均已克隆；
- TripoSR venv：`/root/autodl-tmp/m03/envs/triposr`。

### TripoSR 依赖

已安装：

- omegaconf
- Pillow
- einops
- transformers
- huggingface-hub
- rembg
- onnxruntime
- imageio
- xatlas
- moderngl
- trimesh / scipy / scikit-image / pandas / opencv-python-headless

`torchmcubes` 官方构建因远程镜像缺少真实 `nvcc` 无法编译。已创建 CPU fallback shim：

```text
/root/autodl-tmp/m03/shims/torchmcubes_shim
```

该 shim 使用 `skimage.measure.marching_cubes`，支持 CPU/CUDA 输入张量，但抽 mesh 在 CPU 完成。当前 pilot 使用 `mc-resolution=64`。

### 单图 smoke

输入：

```text
/root/autodl-tmp/m03/repos/TripoSR/examples/chair.png
```

输出：

```text
/root/autodl-tmp/m03/outputs/baseline_runs/triposr_smoke_chair/0/mesh.obj
```

结果：

- 成功导出 OBJ；
- vertices：3001；
- faces：5998；
- watertight：true；
- second run elapsed：约 11s；
- forward：约 0.78s；
- mesh extraction：约 0.057s。

### 跨风格 batch smoke

输入图像：

```text
/root/autodl-tmp/m03/datasets/style_smoke/chair/
```

生成 6 种输入：

- photo
- sketch
- flat
- watercolor
- edge
- low_detail

输出目录：

```text
/root/autodl-tmp/m03/outputs/baseline_runs/triposr_style_smoke_chair/
```

所有 6 个变体均成功导出 OBJ，且均为 watertight。

| style | vertices | faces | z extent | volume | note |
|---|---:|---:|---:|---:|---|
| photo | 3001 | 5998 | 0.514 | 0.094 | reference |
| sketch | 4859 | 9690 | 0.440 | 0.286 | geometry expands / volume rises |
| flat | 4524 | 9048 | 0.538 | 0.204 | surface and volume rise |
| watercolor | 3947 | 7890 | 0.463 | 0.227 | moderate drift |
| low_detail | 5794 | 11512 | 0.578 | 0.356 | strongest volume inflation |
| edge | 2685 | 5414 | 0.124 | 0.044 | severe thickness collapse |

## 初步观察

这个 smoke test 不是正式 benchmark，因为没有真实 3D GT；但它已经证明了 M03 的核心实验链路能运转：

1. 生成多风格 2D 输入；
2. 调用 image-to-3D baseline；
3. 导出 mesh；
4. 计算几何统计；
5. 观察到风格导致的几何退化差异。

尤其 `edge` 输入出现明显厚度塌缩，和 M03 的“style-induced geometry hallucination / degradation”假设一致。

## 下一步

1. 扩展 smoke 到多个 TripoSR example 对象，确认不是 chair 特例；
2. 开始 Objaverse 小子集访问检查；
3. 建立真实 GT 评价脚本：
   - point sampling；
   - Chamfer；
   - F-score；
   - normal / extents / volume drift；
4. 尝试第二 baseline：Stable Fast 3D 或更容易安装的替代 baseline；
5. 准备 30-object pilot。

## 追加进展：5 对象 × 6 风格 smoke

对象：

- chair
- hamburger
- horse
- robot
- teapot

每个对象生成 6 种输入：

- photo
- edge
- flat
- low_detail
- sketch
- watercolor

远程输出：

```text
/root/autodl-tmp/m03/outputs/baseline_runs/triposr_style_smoke_multi/
```

结果：

- 总重建数：30；
- 成功数：30；
- 失败数：0；
- 所有输出 mesh 均为 watertight；
- 汇总文件：`/root/autodl-tmp/m03/outputs/baseline_runs/triposr_style_smoke_multi/aggregate_summary.json`。

相对 photo 的风格均值：

| style | n | z_extent ratio mean | volume ratio mean | 初步解释 |
|---|---:|---:|---:|---|
| edge | 5 | 0.382 | 0.476 | 明显厚度塌缩 |
| sketch | 5 | 0.741 | 1.508 | 厚度降低但体积常膨胀 |
| flat | 5 | 0.999 | 1.252 | 厚度接近但体积偏大 |
| watercolor | 5 | 0.945 | 1.351 | 中等体积漂移 |
| low_detail | 5 | 1.011 | 1.776 | 强体积膨胀 |
| photo | 5 | 1.000 | 1.000 | reference |

这个结果仍不是正式 benchmark，因为没有真实 3D GT；但它提供了 M03 的第一批实验证据：艺术化/边缘化/低细节输入会系统性改变 TripoSR 输出的几何统计。

## 追加进展：Objaverse 真实 3D GT 访问检查

已完成 Objaverse 小子集访问检查。`objaverse` 包的默认 HuggingFace 直连曾返回 HTTP 503；改用 `hf-mirror.com` 下载索引和 metadata 后，可以在远程数据盘正常读取 annotation 和 GLB 文件。

远程缓存：

```text
/root/autodl-tmp/m03/datasets/objaverse_cache/hf-objaverse-v1/
```

已下载并验证 3 个 GLB：

| uid | name | size | vertices | faces | 备注 |
|---|---|---:|---:|---:|---|
| 94db219c315742909fee67deeeacae15 | knife | 3.7MB | 1032 | 1724 | 小模型，适合作为渲染/评测 smoke |
| fc1339e225b7408caec82681be2746c5 | Medieval Punishment | 1.5MB | 5018 | 4672 | 中等复杂度，适合作为第二 smoke |
| 7b56f2bdfd2845588f6bde0c5362fd0d | Bull sculpin head | 44.3MB | 784271 | 1074221 | 复杂模型，暂不作为首轮 pilot 主样本 |

关键远程文件：

```text
/root/autodl-tmp/m03/datasets/objaverse_access_sample.json
/root/autodl-tmp/m03/datasets/objaverse_candidate_rows.json
/root/autodl-tmp/m03/datasets/objaverse_subset/load_stats.json
```

正式 benchmark 的下一步从这 3 个 GLB 开始：先做 canonical mesh、GT point sampling 和 headless 渲染；如果渲染环境可用，再扩到 30-object pilot。

## 追加进展：真实 GT smoke benchmark 已跑通

已完成第一版 M03 真实 GT smoke benchmark：

- 样本：2 个 Objaverse GLB；
- 风格：每个对象 6 种输入，合计 12 个 TripoSR 重建；
- 主视角：`iso` 视角；
- 渲染：使用纯软件三角面片渲染器，避免远程系统 EGL 缺失问题；
- GT：从 canonical mesh 采样 50K surface points；
- 评价：对 TripoSR 输出 mesh 采样 30K points，bbox 归一化后计算 Chamfer / F-score，并记录 extents、surface area、volume。

远程脚本：

```text
/root/autodl-tmp/m03/scripts/objaverse_gt_pipeline.py
/root/autodl-tmp/m03/scripts/evaluate_objaverse_gt.py
```

远程输出：

```text
/root/autodl-tmp/m03/datasets/objaverse_gt_smoke/
/root/autodl-tmp/m03/datasets/objaverse_gt_smoke_inputs_2x6/
/root/autodl-tmp/m03/outputs/baseline_runs/triposr_objaverse_gt_smoke_2x6/
```

所有 12 个重建均成功，且 TripoSR 输出 mesh 均为 watertight。

风格聚合结果：

| style | n | Chamfer L2 mean | F-score@0.05 mean | F-score@0.1 mean | volume mean | z extent mean |
|---|---:|---:|---:|---:|---:|---:|
| edge | 2 | 0.0506 | 0.2186 | 0.4151 | 0.0688 | 0.2726 |
| flat | 2 | 0.0892 | 0.2257 | 0.3794 | 0.0408 | 0.5027 |
| low_detail | 2 | 0.0584 | 0.1808 | 0.3538 | 0.0560 | 0.2143 |
| photo | 2 | 0.0519 | 0.2278 | 0.4324 | 0.1175 | 0.3997 |
| sketch | 2 | 0.0715 | 0.2621 | 0.4414 | 0.0259 | 0.7332 |
| watercolor | 2 | 0.0536 | 0.2226 | 0.4185 | 0.0442 | 0.2769 |

初步解释：

- 正式 GT 评测链路已经闭环；
- `low_detail` 的 F-score@0.05 最低，且 z extent 明显偏小，符合低细节输入造成几何退化的假设；
- `flat` 的 Chamfer 明显升高，说明扁平化/海报化输入会破坏局部几何；
- 当前 n=2 只是 smoke，不做论文级结论；下一步需要扩大到约 30 个经过筛选的 Objaverse 对象。

## 追加进展：30-object pilot 完成

已完成 curated 30-object pilot：

- Objaverse 候选尝试：50；
- 接受样本：30；
- 风格输入：6；
- TripoSR 重建：180；
- 成功：180；
- 失败：0；
- 输出 mesh：全部 watertight。

远程输出：

```text
/root/autodl-tmp/m03/datasets/objaverse_pilot30/pilot30_manifest.json
/root/autodl-tmp/m03/datasets/objaverse_pilot30_gt_curated/summary.json
/root/autodl-tmp/m03/outputs/baseline_runs/triposr_objaverse_pilot30_curated_180/
```

本地同步：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m03_remote_metrics\
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m03-pilot30-results-zh.md
```

全局聚合：

| style | n | Chamfer L2 mean | F-score@0.05 | F-score@0.1 | volume mean | z extent mean |
|---|---:|---:|---:|---:|---:|---:|
| edge | 30 | 0.0423 | 0.3137 | 0.5286 | 0.0948 | 0.3323 |
| flat | 30 | 0.0390 | 0.3204 | 0.5497 | 0.1351 | 0.5937 |
| low_detail | 30 | 0.0457 | 0.3055 | 0.5151 | 0.0922 | 0.3367 |
| photo | 30 | 0.0442 | 0.2743 | 0.4999 | 0.2729 | 0.6783 |
| sketch | 30 | 0.0370 | 0.3511 | 0.5752 | 0.0613 | 0.6130 |
| watercolor | 30 | 0.0398 | 0.3218 | 0.5411 | 0.0960 | 0.4287 |

相对 photo 的关键配对结果：

| style | Chamfer Δ | F@0.05 Δ | volume ratio | z extent ratio | volume Wilcoxon p |
|---|---:|---:|---:|---:|---:|
| edge | -0.0019 | +0.0394 | 0.375 | 0.510 | 3.73e-09 |
| flat | -0.0052 | +0.0461 | 0.460 | 0.890 | 2.61e-08 |
| low_detail | +0.0016 | +0.0312 | 0.350 | 0.517 | 1.86e-09 |
| sketch | -0.0072 | +0.0768 | 0.203 | 0.943 | 1.86e-09 |
| watercolor | -0.0044 | +0.0476 | 0.343 | 0.634 | 1.86e-09 |

当前最有价值的结论不是“风格化一定让 Chamfer 变差”，而是：

- 风格化输入显著压缩重建 mesh 的体积；
- edge / low_detail / watercolor 会明显降低 z extent；
- sketch 会强烈降低体积和 mesh 复杂度，但点云 F-score 反而可能提高；
- 因此传统 Chamfer / F-score 可能掩盖艺术风格导致的 3D 资产可用性退化。

建议将 M03 的核心创新点收窄为：

```text
Style-induced volumetric and thickness bias in image-to-3D reconstruction.
```

## 追加进展：100-object 主实验完成

已完成 M03 main100 主实验：

- Objaverse 候选尝试：165；
- 接受样本：100；
- 许可证：`by` / `by-sa`；
- 风格输入：6；
- TripoSR 重建：600；
- 成功：600；
- 失败：0；
- 输出 mesh：全部 watertight。

远程输出：

```text
/root/autodl-tmp/m03/datasets/objaverse_main100/main100_manifest.json
/root/autodl-tmp/m03/datasets/objaverse_main100_gt_curated/summary.json
/root/autodl-tmp/m03/outputs/baseline_runs/triposr_objaverse_main100_curated_600/
```

本地同步：

```text
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m03_main100_metrics\
D:\AutoResearch\data\autoresearch_runs\ar-20260604-163404-directed\m03-main100-results-zh.md
```

全局聚合：

| style | n | Chamfer L2 mean | F-score@0.05 | F-score@0.1 | volume mean | z extent mean |
|---|---:|---:|---:|---:|---:|---:|
| edge | 100 | 0.0435 | 0.3087 | 0.5163 | 0.0868 | 0.3136 |
| flat | 100 | 0.0398 | 0.3030 | 0.5398 | 0.1360 | 0.5876 |
| low_detail | 100 | 0.0464 | 0.2940 | 0.4953 | 0.0803 | 0.3013 |
| photo | 100 | 0.0467 | 0.2524 | 0.4665 | 0.2790 | 0.6849 |
| sketch | 100 | 0.0366 | 0.3449 | 0.5757 | 0.0685 | 0.5755 |
| watercolor | 100 | 0.0386 | 0.3281 | 0.5496 | 0.0930 | 0.4322 |

相对 photo 的关键配对结果：

| style | Chamfer Δ | F@0.05 Δ | volume ratio | z extent ratio | volume Wilcoxon p |
|---|---:|---:|---:|---:|---:|
| edge | -0.0032 | +0.0564 | 0.332 | 0.471 | 3.90e-18 |
| flat | -0.0069 | +0.0506 | 0.500 | 0.879 | 3.75e-17 |
| low_detail | -0.0003 | +0.0416 | 0.305 | 0.451 | 6.44e-18 |
| sketch | -0.0100 | +0.0925 | 0.257 | 0.868 | 4.14e-18 |
| watercolor | -0.0081 | +0.0757 | 0.343 | 0.635 | 3.90e-18 |

main100 结果支持 pilot 结论：艺术化/风格化输入会显著压缩 image-to-3D 输出的体积和厚度，而 Chamfer/F-score 经常反而优于 photo。这说明传统点云距离可能掩盖艺术风格导致的 3D 资产可用性退化。

## 追加进展：mc-resolution=128 稳健性实验完成

为排除 `mc-resolution=64` 低分辨率 mesh extraction 造成假象，额外抽取 main100 中 30 个对象，使用 TripoSR `mc-resolution=128` 重跑。

结果：

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

结论：提高 mesh extraction 分辨率后，体积压缩和厚度偏差仍然存在；主现象不是 `mc-resolution=64` 的单纯抽 mesh 伪影。
