# M02 / M03 正式查新报告

日期：2026-06-04  
Run ID：`ar-20260604-163404-directed`  
目标：中科院 SCI / SSCI / AHCI 二区，公开数据优先，RTX 3090 24GB 可执行。

## 结论摘要

### M02：从绘画情感到 3D 造型

原始候选不能直接写成“没人做过”。已有大量艺术情感数据集、情感艺术生成、情感 3D avatar / animation 工作。

但目前查到的 closest prior 主要集中在：

- 2D 艺术情感理解 / 解释：ArtEmis、EmoArt、AGSR。
- 2D 情感艺术生成：EmoArt / emotion-aware artistic generation。
- 3D 情感头像 / 动画：Emo3D、EmoTaG、EMOCA 等。

暂未查到“把 2D 绘画情感语义系统性迁移到通用 3D 艺术资产生成，并评价情感保持性”的直接工作。因此 M02 仍有机会，但必须避开“艺术情感理解”或“3D 人脸情感动画”这两个已成熟方向。

建议保留的新命题：

> Emotion-Preserving 2D-to-3D Art Asset Generation: evaluating whether emotion and affective explanations from 2D artworks survive after lifting into stylized 3D assets.

中文题目可写：

> 面向 AI 艺术资产生成的情感保持性评价：从二维绘画到三维风格化资产

建议 verdict：`PARTIAL-OPEN`。有相关基础，但未发现直接同题。

### M03：艺术化输入误导 Image-to-3D

原始候选“艺术化输入会不会误导 Image-to-3D”已经被部分覆盖，不能声称没人做过。

关键撞题：

- Art3D 已经明确指出 image-to-3D 模型在 flat-colored illustration / hand drawing 上困难，并提出 training-free 修正与 Flat-2D benchmark。
- 2026 年 medieval manuscript miniatures 工作已经评测多个 image-to-3D 方法在手稿插图上的表现。
- Sketch-A-Shape、Sketch3D、DrawingSpinUp、PAniC-3D 分别覆盖 sketch-to-3D、角色绘图动画、anime portrait 3D reconstruction 等子域。

因此 M03 的原始表述过宽，已被 Art3D 和手稿 3D reconstruction 明显压缩。

仍可保留的新命题：

> Controlled cross-style robustness benchmark for image-to-3D: render the same Objaverse objects into matched photorealistic / sketch / watercolor / oil-painting / flat-illustration / abstract-style inputs, keep known 3D ground truth, and quantify which artistic cues cause geometry hallucination, thickness collapse, backside invention, or material-shape entanglement.

中文题目可写：

> 艺术风格迁移是否破坏 Image-to-3D 几何事实？一个带真实三维 GT 的跨风格鲁棒性基准

这个版本区别于 Art3D：

- Art3D 更像“如何让 flat-colored illustration 生成更好的 3D”。
- 新命题更像“同一物体在不同艺术风格输入下，现代 image-to-3D 模型的几何事实如何系统性漂移”。
- 关键创新必须是 paired benchmark：同一 Objaverse 物体产生多种受控风格图像，因此有真实 3D GT，可做 Chamfer / normal / silhouette / thickness / topology / back-view consistency，而不是只用 2D 参考图评价。

建议 verdict：`PARTIAL-OPEN`，但比 M02 更容易形成 SCI Q2 技术论文。

## M02 查新详情

### 查新查询

- `"ArtEmis" "3D" "emotion" "asset"`
- `"emotion-aware" "3D" "art" "generation"`
- `"affective" "3D" "art" "generation"`
- `"emotion consistency" "3D" "art"`
- `"EmoArt" "3D" "generation"`
- `"emotion-aware Text-to-3D avatar generation"`

### Closest prior

1. ArtEmis: Affective Language for Visual Art  
   https://artemisdataset.org/  
   https://arxiv.org/abs/2101.07396  
   相关性：提供 WikiArt 上大规模 emotion attribution + explanation，是 M02 的关键数据基础。  
   不构成直接撞题：它是 2D visual art emotion understanding，不做 3D asset generation 或 2D-to-3D emotion preservation。

2. EmoArt: A Multidimensional Dataset for Emotion-Aware Artistic Generation  
   https://arxiv.org/abs/2506.03652  
   相关性：132k 艺术图像，包含风格、视觉属性、valence-arousal、emotion 等，用于评估 emotion-aligned text-to-image diffusion。  
   不构成直接撞题：重点是 2D image generation，不是 3D asset lifting。

3. Attribute-Grounded Selective Reasoning for Artwork Emotion Understanding with MLLMs  
   https://arxiv.org/abs/2605.15755  
   相关性：已指出 MLLM 艺术情感解释会出现 attribute flooding，并加入 human salience extension。  
   对 M02 的影响：如果 M02 只做“MLLM 判断艺术情绪是否解释忠实”，会撞上这个方向；必须转到 3D asset / 2D-to-3D transfer。

4. Towards Rich Emotions in 3D Avatars: A Text-to-3D Avatar Generation Benchmark  
   https://arxiv.org/abs/2412.02508  
   相关性：做 text-to-3D emotional avatar generation benchmark，覆盖 emotion-content consistency、expression diversity、fluidity。  
   不构成直接撞题：这是 3D face/avatar expression，不是通用艺术资产或绘画风格到 3D 物体。

5. EmoTaG: Emotion-Aware Talking Head Synthesis on Gaussian Splatting  
   https://arxiv.org/abs/2603.21332  
   相关性：3DGS talking head 中的 emotion-aware motion modeling。  
   不构成直接撞题：仍是人物头像/语音驱动动画。

6. DeepSpace: Mood-Based Image Texture Generation for Virtual Reality from Music  
   https://www.media.mit.edu/publications/deepspace-mood-based-image-texture-generation-for-virtual-reality-from-music/  
   相关性：较早的情绪驱动 VR texture / environment 生成。  
   不构成直接撞题：不是现代 image-to-3D / text-to-3D asset pipeline。

### M02 风险

- 如果做成“艺术情感分类 / 解释”，创新性被 ArtEmis、EmoArt、AGSR 压住。
- 如果做成“3D 情感人脸 / avatar”，会被 Emo3D / EmoTaG / EMOCA 系列压住。
- 最可行的差异化必须是“2D 绘画情感语义在 3D 艺术资产生成后是否保持”。

### M02 可执行实验草案

- 数据：ArtEmis / EmoArt 选择具有明确 emotion + explanation 的绘画图像；Objaverse 选择对象类别；可加 WikiArt style references。
- 生成：现成 image-to-3D / text-to-3D pipeline，小规模生成即可。
- 指标：
  - emotion consistency：2D 输入和 3D 多视角渲染的 emotion prediction / explanation similarity。
  - explanation grounding：生成 3D 多视角是否保留原图解释中提到的视觉证据。
  - style-content disentanglement：情感保留是否以几何破坏或材质过拟合为代价。
- 3090 可行性：高，主要是推理、渲染、VLM/CLIP/MLLM 评估。

## M03 查新详情

### 查新查询

- `"painting-to-3D" "image-to-3D"`
- `"non-photorealistic" "image-to-3D" "generation"`
- `"sketch-to-3D" "generation" "benchmark"`
- `"artistic" "image-to-3D"`
- `"Art3D" "Flat-2D" "image-to-3D"`
- `"paired" "photorealistic" "stylized" "image-to-3D" benchmark`
- `"style shift" "image-to-3D" generation benchmark`
- `"domain shift" "image-to-3D" "stylized"`

### Closest prior

1. Art3D: Training-Free 3D Generation from Flat-Colored Illustration  
   https://arxiv.org/abs/2504.10466  
   https://joy-jy11.github.io/  
   相关性：强。明确指出现代 image-to-3D 模型处理 flat-colored / hand drawing 输入困难，提出 Art3D 和 Flat-2D benchmark。  
   对 M03 的影响：M03 原始版本“艺术化输入会误导 image-to-3D”不能原样成立为新题。

2. A Semi-Automated Framework for 3D Reconstruction of Medieval Manuscript Miniatures  
   https://arxiv.org/abs/2604.08610  
   相关性：强。评测 TripoSR、SF3D、SPAR3D、TRELLIS、Wonder3D、SAM 3D、Hi3DGen 在 69 个 manuscript figures 上的表现。  
   对 M03 的影响：历史艺术图像 / manuscript-to-3D 也已有直接评测。

3. Sketch-A-Shape: Zero-Shot Sketch-to-3D Shape Generation  
   https://arxiv.org/abs/2307.03869  
   相关性：中强。覆盖 sketch-to-3D，强调 limited paired data 和 sketch abstraction。  
   对 M03 的影响：素描子域不是空白。

4. Sketch3D: Style-Consistent Guidance for Sketch-to-3D Generation  
   https://arxiv.org/abs/2404.01843  
   相关性：中强。生成 realistic 3D assets，形状对齐 sketch，颜色由 text description 控制。  
   对 M03 的影响：如果只做 sketch-to-3D 修正会撞题。

5. DrawingSpinUp: 3D Animation from Single Character Drawings  
   https://arxiv.org/abs/2409.08615  
   相关性：中。说明 character drawings 中 contour lines 会带来 texture ambiguity，thin regions 难重建。  
   对 M03 的影响：角色绘图到 3D 动画已有专门方法。

6. PAniC-3D: Stylized Single-view 3D Reconstruction from Portraits of Anime Characters  
   https://arxiv.org/abs/2303.14587  
   相关性：中。覆盖 anime portrait illustration 到 3D character head reconstruction。  
   对 M03 的影响：anime 人物头部子域已有数据和方法。

### M03 风险

- 原始题目太宽，Art3D 已经直接挡住一大块。
- 如果只评测 flat illustration 或 hand drawing，会被认为 Art3D 的 follow-up。
- 如果只做某一类艺术图像到 3D，如手稿、动漫头、角色绘图，也容易撞已有专门工作。

### M03 可保留创新点

最强可发表缝隙不是“某类艺术图像到 3D”，而是：

1. 同一真实 3D 对象的多风格受控输入；
2. 已知 3D ground truth；
3. 比较不同风格如何造成几何事实漂移；
4. 提出 style-stripping / geometry-preserving preprocessing 或 model-selection rule。

建议正式 candidate：

> Cross-Style Geometry Hallucination in Image-to-3D Generation: A Paired Benchmark with Known 3D Ground Truth

中文题目：

> Image-to-3D 生成中的跨风格几何幻觉：一个带真实三维标注的成对鲁棒性基准

### M03 可执行实验草案

- 数据：
  - Objaverse / Objaverse curated subset 中选择 100-300 个简单物体。
  - 对每个物体渲染 clean photorealistic view，作为可控基准输入。
  - 用图像风格化方法生成 sketch、watercolor、oil painting、flat illustration、anime/toon、abstract low-detail 等输入版本。
  - 保留原始 3D mesh 作为 GT。
- 模型：
  - TripoSR / Stable Fast 3D / Wonder3D / open Hi3DGen or TRELLIS-like models，按可获得性选择。
- 指标：
  - geometry：Chamfer / F-score / normal consistency / depth consistency。
  - projection：multi-view silhouette IoU / LPIPS。
  - topology：watertight rate / connected components / thickness collapse。
  - style-induced hallucination：相对 photorealistic input 的性能下降。
- 修正模块：
  - edge-depth assisted preprocessing；
  - style-stripped reference generation；
  - multi-candidate reranking by geometry proxy。
- 3090 可行性：中高。数据量控制在 100-300 个对象，重点推理与评估，不从头训练 3D 生成模型。

## 最终推荐

1. 首推 M03 的窄化版本：`Cross-Style Geometry Hallucination in Image-to-3D Generation`。
   - 更适合 SCI Q2。
   - 数据公开且可控。
   - 有真实 3D GT，证据比纯 MLLM 评价更硬。
   - 风险是需要明确区别于 Art3D。

2. 次推 M02 的窄化版本：`Emotion-Preserving 2D-to-3D Art Asset Generation`。
   - 更有 AI + 艺术 / 数字人文味道。
   - 对 SSCI/AHCI 更友好。
   - 技术风险较低，但需要把“情感保持性”定义得足够严谨，否则容易显得软。

3. 不建议继续使用原始宽泛表述。
   - M02 原始表述会被 ArtEmis / EmoArt / AGSR / Emo3D 分散压缩。
   - M03 原始表述会被 Art3D / manuscript 3D reconstruction / sketch-to-3D 压缩。

## 下一步建议

如果选择 M03：

- 进入 Gate 2，生成正式 candidate。
- 先做 dataset-access check：Objaverse subset 下载与渲染、模型可用性、评估脚本。
- 设计最小实验：30 个对象 × 5 种风格 × 2 个 image-to-3D 模型，验证是否存在稳定 style-induced geometry degradation。

如果选择 M02：

- 先确认目标更偏 SCI 还是 SSCI/AHCI。
- 若偏 SCI：加入自动评分器和多视角证据对齐。
- 若偏 SSCI/AHCI：加入小规模人工评价或专家 rubric，否则人文社科说服力不够。
