# M02 Hunyuan3D 2.1 小规模重跑结果

日期：2026-06-05

## 目的

用户观察到原 M02 的 TripoSR `render.png` 与 `original.png` 明显不相关，且没有材质，真人难以评价情感保留。本次小规模重跑用于检验：换成更强的 Hunyuan3D 2.1 后，M02 是否能恢复到“可做人类评分”的程度。

## 样本

共 8 张 EmoArt/WikiArt 绘画样本：

- 4 张相对清晰主体：花瓶、人物/肖像、坐姿人物等；
- 4 张困难样本：船只场景、抽象圆环、Pop Art 场景、宫廷长卷场景。

样本和结果目录：

```text
m02_hunyuan21_rerun\
```

## 运行结果

远程环境：

- GPU：RTX 5090；
- shape 模型：`tencent/Hunyuan3D-2.1`；
- 推理设置：`num_inference_steps=25`，`octree_resolution=256`；
- 模型权重缓存：约 8.1 GB；
- shape 输出：8 / 8 成功；
- 单样本 shape 推理：约 10 秒，不含首次模型下载/加载。

本地结果包：

```text
m02_hunyuan21_rerun\hunyuan21_shape_smoke_results.zip
m02_hunyuan21_rerun\remote_hunyuan21_shape_smoke_results\
```

核心预览图：

```text
m02_hunyuan21_rerun\remote_hunyuan21_shape_smoke_results\outputs\hunyuan21_shape_smoke\previews\hunyuan21_shape_contact_sheet.png
```

## 质性观察

Hunyuan3D 2.1 shape 阶段比原 TripoSR 更稳定地生成了 mesh，但对绘画图像仍没有达到 M02 人类情感评分所需的语义/风格保真：

- 花瓶样本生成结果主要是平面画布/浮雕，没有恢复花瓶和花朵的 3D 结构；
- 肖像样本变成类似窄瓶/竖片的形体，脸部、表情和情感线索消失；
- 坐姿人物样本生成碎片化结构，主体不完整；
- 绿色人物样本有局部肢体形状，但整体姿态和语义仍不稳定；
- 船只、宫廷长卷、Pop Art、抽象圆环样本大多变成平板、薄片或低语义浮雕。

## Texture 状态

Hunyuan3D 2.1 的 PBR texture/paint 阶段未完成：

- base Python 3.12 环境已有 `torch 2.8.0+cu128`，可支持 RTX 5090；
- Hunyuan shape 依赖已补齐并可运行；
- Hunyuan paint 导入需要 `bpy`；
- Python 3.12 下 `bpy` 没有可用 pip wheel；
- Python 3.10 独立环境可创建，但重新安装 PyTorch/cu128 依赖过慢，不适合作为本次“小规模先跑完就停”的继续扩展。

因此本轮结论只针对 Hunyuan3D 2.1 shape feasibility，不声称 Hunyuan3D 2.1 PBR texture 实验已完成。

## 结论

M02 不建议继续按“original vs render 的真人情感保留评分”推进。即使换成 Hunyuan3D 2.1 shape，绘画到 3D 的结果仍常表现为平面化、浮雕化、碎片化和语义弱保真；评价者仍会面对“看不出两者关系”的问题。

更合理的后续方向是：

- M03 继续作为主论文线；
- M02 作为失败模式/动机证据，说明绘画到 3D 的前置语义与材质保真尚未解决；
- 若要把 M02 做成强论文方向，应转向“开发 art-aware / texture-aware / emotion-preserving 3D 生成改进方法”，而不是直接做人评。
