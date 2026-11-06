# M03 Hunyuan3D 2.1 强模型切换 pilot 决策报告

## 一句话结论

换用 Hunyuan3D 2.1 是有效的，但不建议简单删除 TripoSR、只用 Hunyuan
重写原论文。pilot 支持一个更强且更诚实的新创新点：**艺术化输入造成的几何偏差
具有明显的模型依赖性；更强的 3D 先验能抑制总体几何漂移，但仍保留少量对象级失败，
并且不保证对每个类别都优于轻量模型。**

因此，最有价值的正式研究不是“证明所有 image-to-3D 模型都会塌缩”，而是比较
TripoSR 与 Hunyuan3D 2.1 的 `model x input style` 交互，回答哪些风格偏差会随模型
能力增强而消失，哪些偏差仍然存在。

## Pilot 设计

- 12 个 Objaverse 对象，按原 TripoSR photo F-score 分为 low、middle、high 三层。
- 每个对象使用 photo、edge、flat colour、low detail、sketch、watercolour 六种匹配输入。
- Hunyuan3D-Shape 2.1：25 steps，octree resolution 384，两个随机种子。
- 几何任务共 144 个，成功 144，失败 0。
- 官方 Hunyuan3DPaintPipeline：2 个对象、6 种风格，共 12 个 PBR 资产。
- PBR 采用官方默认 40,000 面重网格化；几何指标始终使用未重网格化的原始 GLB。

## 关键结果

### 1. Photo 基线质量提高，但不是全面胜出

- Hunyuan photo 中位 F-score@0.05：`0.3162`。
- 同对象 TripoSR photo 中位 F-score@0.05：`0.2439`。
- Hunyuan 在 `9/12` 个对象上 F-score 更高。
- 反例很重要：Gas Stove 和 C64 Monitor 上，Hunyuan 的 F-score 明显低于 TripoSR；
  Aviator sunglasses 也略低。因此不能写成“Hunyuan 对所有对象都更好”。

### 2. Hunyuan 的总体风格几何较稳定

Hunyuan 输出只有 `39.6%` 严格 watertight，所以严格 mesh volume 只在有效子集报告；
覆盖全部样本的主要体积诊断采用 convex-hull envelope volume。

| 风格 | convex-hull 体积比中位数 | 低于 0.8 的比例 | 平均 F-score 变化 | 严格体积有效数 |
|---|---:|---:|---:|---:|
| Edge | 1.0117 | 12.5% | +0.0025 | 5/24 |
| Flat colour | 0.9987 | 8.3% | +0.0063 | 7/24 |
| Low detail | 0.9580 | 12.5% | -0.0162 | 8/24 |
| Sketch | 0.9852 | 8.3% | -0.0002 | 7/24 |
| Watercolour | 0.9977 | 8.3% | -0.0101 | 5/24 |

五种风格的中位体积比都没有低于 0.8，风格引起的平均 F-score 变化也很小。这与
TripoSR 上明显的总体塌缩现象不同。不过，每种风格仍有约 `8.3%-12.5%` 的单例
低于 0.8，说明对象级脆弱性尚未消失。

### 3. 两随机种子方向稳定

- 各风格 convex-hull 体积比的种子间中位绝对差为 `0.0119-0.0423`。
- 两种子的 Spearman 相关为 `0.713-0.916`。
- 汇总中位绝对差为 `0.0184`。

这表明主要趋势不是由单次随机采样偶然造成，但 12 个对象仍只是 pilot，不能代替
正式样本量。

### 4. 官方 PBR 材质链路已打通

- `12/12` 个 GLB 成功，Blender 实际导入和渲染 `12/12` 成功。
- 每个资产均包含 albedo、metallic、roughness 三类纹理。
- PBR GLB 均为官方默认重网格化后的最多 40,000 面。
- 输入平均饱和度仅 `0.0171`，生成 albedo 平均饱和度为 `0.1410`。

Flat-colour 输入能得到明显颜色；其余输入大多本来就是灰度或低饱和图，因此输出仍
偏灰。PBR 解决了“无材质白模”的展示问题，但不能从没有颜色信息的输入中恢复真实
物体颜色。论文应把 PBR 用作代表性可视化，不应把颜色真实性当作本实验贡献。

## 对原论文的影响

原 TripoSR 论文的核心现象仍有价值，但它目前更像一个**模型特定的失败模式**，而非
可直接推广到所有 image-to-3D 模型的普遍规律。若只用 Hunyuan 替换 TripoSR，主要
中位塌缩现象会变弱，论文反而可能失去原来的冲突性。

更合适的论文主线是：

> 在严格配对的同对象、同视角输入下，艺术化表征对 image-to-3D 几何的影响是否随
> 模型能力而变化？更强的 3D 先验消除了哪些总体偏差，又留下了哪些对象级脆弱性？

这条主线允许同时保留：

- TripoSR：展示明显的风格偏差和 metric paradox。
- Hunyuan3D 2.1：展示更强模型对总体偏差的缓解。
- 反例对象：展示“模型更强”并不等于所有类别都更准确。
- PBR：提供可读的代表性结果，不参与核心几何统计。

## 推荐正式方案

**推荐选择：保留 TripoSR 基线，新增 Hunyuan3D 2.1 强模型臂。**

1. 先对“跨模型风格鲁棒性、model-style interaction”做一次针对性 novelty scan。
2. novelty scan 通过后，在 100 个对象上运行 Hunyuan 几何：6 风格 x 2 种子，
   共 1,200 个网格；按当前速度约需 7-8 GPU 小时。
3. 复用现有 TripoSR 100 对象结果，不重复无必要的基线计算。
4. 主要统计使用配对层级 bootstrap 或 mixed-effects model，显式检验
   `model x style` 交互；对象作为随机效应。
5. 同时报 watertight rate、convex-hull envelope volume、extent、Chamfer 和 F-score；
   不把非 watertight 网格的 signed volume 当作有效体积。
6. PBR 只扩展到 2-4 个代表对象 x 6 风格，不需要给 600 个结果全部生成材质。

## 当前选择点

- **A（推荐）**：开展跨模型 novelty scan；通过后扩展 100 对象双模型论文。
- **B**：只保留 Hunyuan，放弃 TripoSR 主线。风险是总体风格效应较弱，论文贡献会变薄。
- **C**：保留当前 TripoSR 论文，仅把 Hunyuan pilot 写入局限性或补充实验。

在选择 A、B 或 C 之前，不应覆盖现有论文正文或启动 100 对象扩展。

## 主要产物

- `remote_results/analysis/pilot_key_results.png`：核心结果图。
- `remote_results/previews/shape_contact_sheet.png`：12 对象几何联系表。
- `remote_results/previews/pbr_contact_sheet.png`：2 对象官方 PBR 联系表。
- `remote_results/analysis/hunyuan21_aggregate.csv`：风格汇总指标。
- `remote_results/analysis/photo_model_comparison.csv`：逐对象跨模型比较。
- `remote_results/analysis/seed_stability.csv`：随机种子稳定性。
- `remote_results/analysis/pbr_visual_qc.csv`：PBR 文件与饱和度质检。
- `remote_results/provenance.json`：GPU、提交号、包版本和推理参数。
- `remote_results/pbr_glb/`：12 个可直接打开的带材质 GLB。

远程原始高密度几何保存在：
`/root/autodl-tmp/m03_hunyuan21_pilot_20260714/outputs/shape`。
