# M03 Hunyuan3D 2.1 强模型 pilot

**状态：已完成（2026-07-14）。** 结论与下一步选择见
[`pilot-decision-report-zh.md`](pilot-decision-report-zh.md)。

本目录用于验证 M03 的主要现象是否能够从 TripoSR 复现到更强的开源
image-to-3D 模型 Hunyuan3D 2.1。现有 TripoSR 结果保留为基线，不被覆盖。

## 固定设计

- 12 个对象：按原 TripoSR photo F-score 分成 low、middle、high 三层，每层 4 个。
- 6 种匹配输入：photo、edge、flat、low_detail、sketch、watercolor。
- 2 个随机种子：20260714 和 3407。
- 几何生成：Hunyuan3D-Shape 2.1，25 steps，octree resolution 384。
- 总几何生成数：12 x 6 x 2 = 144。
- 官方 PBR：先对 2 个对象的 6 种输入生成 12 个纹理资产。
- 远程输出根目录：`/root/autodl-tmp/m03_hunyuan21_pilot_20260714`。

## 决策点

pilot 完成后停止扩展，先检查：

1. Hunyuan photo 重建是否比同对象 TripoSR photo 重建更强；
2. stylised/photo 的体积和最小包围盒尺度是否仍系统下降；
3. 两个种子是否给出一致方向；
4. 官方 PBR 资产是否足以替换论文中灰白、低质量的示例图。

只有通过上述检查后，才扩展为完整 100-object 双模型实验并重写论文。
