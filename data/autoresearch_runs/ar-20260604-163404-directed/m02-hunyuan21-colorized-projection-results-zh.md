# M02 Hunyuan3D 2.1 彩色投影后处理结果

日期：2026-06-05

## 目的

原 Hunyuan3D 2.1 小规模重跑只完成了 shape 阶段，预览图和 GLB 呈现为灰白 mesh。用户观察到形体已经明显优于第一个模型，因此本次补做一个轻量后处理：把原始绘画图像的颜色按前视投影写入 mesh 顶点颜色，生成彩色 GLB 和彩色三视图预览。

## 方法边界

本次方法是：

```text
front-view vertex color projection from input image
```

它不是 Hunyuan3D 2.1 官方 PBR texture/paint 阶段，也不声称生成了真实多视角材质。其作用是快速回答一个工程问题：如果先把颜色补上，M02 的 visual plausibility 是否明显改善。

## 输出

脚本：

```text
colorize_hunyuan21_shapes.py
```

结果目录：

```text
m02_hunyuan21_rerun\colorized_projection_results\
```

每个样本包含：

```text
colorized_shape.glb
color_preview_front.png
color_preview_side.png
color_preview_iso.png
colorized_comparison_panel.png
```

总览图：

```text
m02_hunyuan21_rerun\colorized_projection_results\previews\hunyuan21_colorized_projection_contact_sheet.png
```

结果包：

```text
m02_hunyuan21_rerun\hunyuan21_colorized_projection_results.zip
```

## 运行结果

- 样本数：8；
- 彩色 GLB：8 / 8；
- 彩色 comparison panel：8 / 8；
- contact sheet：已生成；
- 原始 shape GLB 未覆盖，彩色版本单独保存为 `colorized_shape.glb`。

## 质性观察

相较灰白 shape 预览，彩色投影明显提升了可读性：

- 花瓶样本能看到花朵、叶片和背景色块，灰白平板感减弱；
- 肖像样本虽然形体仍像竖片/薄楔，但蓝白竖向纹理和人物色彩保留下来，可读性提升；
- 绿色人物样本保留了绿色身体、深蓝布料和局部脸部色彩；
- Pop Art 和抽象圆环样本的高饱和色彩被保留，视觉冲击明显强于灰模；
- 宫廷长卷样本从灰色薄板变成带画面信息的长条浮雕，更适合展示失败模式。

仍然存在的限制：

- 颜色来自前视投影，侧面和背面会拉伸或重复；
- 如果 shape 本身碎片化，彩色只能改善视觉表达，不能恢复正确 3D 语义；
- 不能作为“官方材质生成模型完成”的证据。

## 结论

这个彩色投影版本值得保留。它可以把 M02 从“灰白模型看不出关系”推进到“至少能看出绘画颜色和局部图案被带到 3D 表面”的状态。若后续继续 M02，建议把这个作为最低成本的 textured/colorized baseline；真正论文级提升仍应转向 art-aware / texture-aware / emotion-preserving 3D 生成方法。
