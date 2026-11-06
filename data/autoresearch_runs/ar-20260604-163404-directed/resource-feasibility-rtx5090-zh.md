# RTX 5090 资源可行性评估

日期：2026-06-04  
Run ID：`ar-20260604-163404-directed`  
候选：M03，跨风格 Image-to-3D 几何幻觉 benchmark。

## 用户提供配置

- GPU：RTX 5090 * 1
- CPU：16 核
- 内存：90GB
- 系统盘：30GB
- 数据盘：免费 50GB SSD + 付费 700GB
- 镜像：PyTorch 2.8.0 / Python 3.12 / Ubuntu 22.04 / CUDA 12.8

## 结论

可以使用，而且比原先的 RTX 3090 24GB 更适合本课题。

M03 的核心工作不是从头训练大型 3D foundation model，而是：

1. 下载和筛选公开 3D 对象；
2. 渲染同一对象的多种 2D 风格输入；
3. 跑若干 image-to-3D baseline 的推理；
4. 对输出 mesh / view / depth / silhouette / normal 做评估；
5. 做轻量 preprocessing 或 reranking 修正。

这类工作主要消耗 GPU 推理、CPU 渲染、磁盘和文件管理。RTX 5090 + 700GB 数据盘足够支撑 pilot 和中等规模主实验。

## 兼容性判断

RTX 5090 属于 Blackwell 代际。Blackwell 需要 CUDA 12.8+ 才是稳妥路线；用户镜像已经是 CUDA 12.8 和 PyTorch 2.8，方向正确。

风险不是 PyTorch 主体，而是某些旧 3D 项目的自定义 CUDA extension：

- 如果项目只依赖 PyTorch / diffusers / transformers / open3d / trimesh / pytorch3d 的可用轮子，问题较少。
- 如果项目带老的 custom CUDA op，且没有 `sm_120` / Blackwell 支持，可能需要重新编译或更换 baseline。
- 优先选择安装路径短、维护活跃、推理脚本明确的 baseline。

## 建议实验规模

### Pilot

- 对象数：30
- 风格数：5
- baseline：2 个
- 总推理：30 * 5 * 2 = 300 次
- 目标：验证是否存在稳定的 style-induced geometry degradation。

### Main

- 对象数：100-300
- 风格数：5-7
- baseline：2-4 个
- 总推理：约 1000-8400 次
- 目标：形成可发表的统计结果和错误类型 taxonomy。

## 数据盘建议

700GB 数据盘足够，但必须规划目录：

```text
/root/autodl-tmp/m03/
  datasets/
    objaverse_subset/
    renders/
    stylized_inputs/
  models/
    sf3d/
    triposr/
    wonder3d_or_alternative/
  outputs/
    baseline_runs/
    meshes/
    rendered_views/
  metrics/
  logs/
```

避免把模型、数据、输出写到 30GB 系统盘。

## 优先 baseline

1. Stable Fast 3D  
   优点：官方说明单图推理约 6GB VRAM，适合批量实验；输出 mesh 和 texture，便于评价。

2. TripoSR  
   优点：轻量、快速，适合作为基础 baseline。

3. Wonder3D / 其他可装通的多视角 baseline  
   优点：可补充多视角生成路线；缺点是环境可能更麻烦。

如果某个 baseline 在 RTX 5090 上 custom CUDA extension 编译失败，不要硬修太久；先替换成可稳定运行的 baseline，保证 benchmark 主线推进。

## 暂不建议

- 不要从头训练 text-to-3D / image-to-3D foundation model。
- 不要一开始下载完整 Objaverse。
- 不要同时上 4 个以上复杂 baseline。
- 不要第一轮就跑 1000+ 对象。
- 不要依赖只有网页 demo、没有稳定脚本和许可证不清楚的模型作为主 baseline。

## 下一步

1. 创建远程目录和缓存环境。
2. 检查 `torch.cuda.is_available()`、GPU 名称、CUDA version。
3. 安装并跑通 Stable Fast 3D 的单图 demo。
4. 安装并跑通 TripoSR 的单图 demo。
5. 下载或生成 30 个对象的 pilot 数据。
6. 跑 30 对象 pilot，确认 M03 的核心现象存在。
