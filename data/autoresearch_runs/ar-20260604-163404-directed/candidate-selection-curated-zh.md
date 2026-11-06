# 中文增强候选清单

Run ID: `ar-20260604-163404-directed`

目标：中科院 SCI / SSCI / AHCI 二区，开源或闭源期刊均可。  
资源：远程 RTX 3090 24GB，硬盘 500GB+。  
数据策略：优先公开、易获取数据。  
停止点：筛选出具体创新点后暂停，等待用户选择。

## 推荐排序

### M01：风格一致性不等于 3D 可用性：面向 AI 生成 3D 资产的“风格-几何-材质”一致性评估与轻量修正

- 方向贴合：AI + 3D 建模 / AI + 艺术
- 核心问题：当前 style-guided 3D asset generation 往往强调视觉好看或单视角相似，但艺术风格、几何保持、PBR 材质合理性之间并不等价。一个模型可能保留了梵高式纹理，却破坏了几何轮廓或材质属性；也可能材质物理上合理，但艺术风格迁移失败。
- 创新点：构建一个三轴评估框架：style consistency、geometry preservation、material plausibility，并提出一个训练成本低的 reranking / refinement 模块，在不重训大模型的情况下改进生成结果选择。
- 可用公开数据：Objaverse / Objaverse subset，WikiArt 或 ArtEmis 风格参考图，Hi3DEval / Hi3DBench 作为 3D 评估参考。
- 3090 可行性：高。主要是渲染、多视角特征提取、CLIP/DINO/3D feature 评估、小规模 refinement，不需要从头训练 3D 生成大模型。
- 期刊适配：偏 SCI Q2，适合 Computer Graphics / Multimedia / Expert Systems / Applied AI 类期刊。
- 风险：需要控制“只是做指标”的风险，最好加一个 lightweight correction 或 model-selection module。

### M02：从绘画情感到 3D 造型：基于 ArtEmis 的情感保持式 3D 艺术资产生成评估

- 方向贴合：AI + 艺术 / AI + 绘画 / AI + 3D 建模
- 核心问题：AI 艺术生成常说“风格迁移”，但用户真正想要的经常是情绪或意图迁移，例如孤独、宁静、压迫、神圣感。2D 绘画数据有情感解释标注，3D 资产生成却缺少“情感是否被保留”的评价。
- 创新点：用 ArtEmis 的 emotion + explanation 作为公开监督信号，评估 2D 绘画风格迁移到 3D 资产后情感语义是否保持；提出 emotion-consistency score，并测试它和普通 aesthetic / CLIP similarity 的分歧。
- 可用公开数据：ArtEmis、WikiArt、Objaverse 小子集。
- 3090 可行性：高。可以先做评估型论文，生成部分用开源或现成 pipeline，小规模即可。
- 期刊适配：SCI Q2 或 SSCI/AHCI 边界型期刊。若强调人文艺术解释，可往 AI + Society / digital humanities 方向靠；若强调算法评估，往 multimedia / computer vision 方向靠。
- 风险：如果完全不做人工验证，SSCI/AHCI 说服力可能弱；但初稿可先用公开标注和自动一致性分析。

### M03：艺术化输入会不会误导 Image-to-3D？面向绘画/素描/非写实图像的 3D 生成鲁棒性基准

- 方向贴合：AI + 绘画 / AI + 3D 建模
- 核心问题：很多 image-to-3D 方法在商品图、真实照片上展示效果，但绘画、素描、儿童画、风格化图像中的轮廓夸张、透视错误、阴影非物理，会让 3D 生成模型混淆“艺术表达”和“几何事实”。
- 创新点：构造一个公开数据组合 benchmark，比较 photorealistic input、painting input、sketch input 到 3D 输出的几何稳定性；提出 style-stripped geometry prompt / edge-depth assisted prompting 作为低成本修正。
- 可用公开数据：WikiArt / ArtEmis 绘画图，QuickDraw 或 Sketchy 类素描数据，Objaverse 中可渲染真实参考的对象。
- 3090 可行性：中高。主要跑推理和评估，不做大规模训练。
- 期刊适配：SCI Q2，偏 Multimedia Tools、Visual Computer、Pattern Recognition Letters 类。
- 风险：要选好对象类别，避免绘画和 3D ground truth 不可比。

### M04：AI 绘画评价中的“审美分数”与“解释忠实性”分离：面向 MLLM 艺术评论的可靠性研究

- 方向贴合：AI + 艺术 / AI + 绘画
- 核心问题：多模态大模型可以给画作打分、写评论、解释风格，但好看的评论不一定忠实于画面内容。艺术评价里尤其容易出现“套话式解释”：情绪、流派、构图词汇听起来合理，却未必由图像证据支持。
- 创新点：基于 ArtEmis 的 emotion explanation，把艺术评价拆成 emotion prediction、visual evidence grounding、style/content disentanglement 三个维度，测试开源/闭源 MLLM 的艺术评论可靠性。
- 可用公开数据：ArtEmis、WikiArt，必要时加公开 AI-generated art 数据集。
- 3090 可行性：高。本地 3090 只需跑开源 VLM 或图像编码器；闭源模型可 API 评估。
- 期刊适配：SSCI/AHCI 或 SCI Q2 均可。若目标是人文社科二区，这个候选比纯 3D 技术更自然。
- 风险：如果目标期刊偏 SCI，需要加入更明确的算法模块，例如 explanation-faithfulness scorer。

### M05：文本到 3D 室内/艺术场景生成中的布局语义漂移：从单物体资产到可解释场景一致性

- 方向贴合：AI + 3D 建模 / AI + 艺术
- 核心问题：text-to-3D scene generation 不只是生成单个物体，还要让风格、功能布局和空间关系一致。现有方法容易出现“每个物体看起来对，但整体场景语义错”的问题，例如画室、展厅、舞台、装置艺术空间。
- 创新点：面向艺术/创作空间建立 scene-level consistency checklist：object identity、layout relation、style coherence、functional affordance，并提出一个 MLLM + 3D render 多视角审核流程。
- 可用公开数据：3D-FRONT / 3D-FUTURE / Objaverse / 室内场景公开数据，小规模即可。
- 3090 可行性：中。场景渲染和多视角评估可行；大模型生成从头训练不可行，应避免。
- 期刊适配：SCI Q2，偏 3D scene understanding / multimedia。
- 风险：公开数据许可和场景构建流程要先核实，实验设计比 M01/M04 更重。

## 不推荐直接进入的系统原始候选

- C01/C02：LoRA 理论与大模型评测，偏离你的 AI+3D/艺术/绘画方向。
- C03：3D driving scene validity 有 3D 相关性，但偏自动驾驶，不够贴合艺术或绘画。
- C04-C06：偏自动驾驶规划/推理，不建议作为本次方向。

## 当前建议

如果你想要 SCI Q2 成功率和实验可控性，我建议优先选 M01。  
如果你更想靠近 SSCI/AHCI 或数字人文/艺术评价，建议选 M04。  
如果你想做一个更像“AI + 绘画 + 3D”的交叉题，建议选 M02。
