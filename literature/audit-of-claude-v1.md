# 文献树 v1 核查

- 日期：2026-11-18
- 对象：[Claude 起草的文献树 v1](../docs/literature-tree/literature-tree-v1.md)
- 方法：按 findInnovation 追踪五个种子的前向引用，并用独立关键词检索补查。引文索引供发现线索，判断以出版社、作者全文或作者公开研究档案为准。查询和覆盖范围见[检索记录](search-log.md)。

OpenAlex 已处理 LaMa 正式版 1,748 条、预印本 223 条，ARTeFACT 7 条、Shao 22 条、Kachkine 13 条、Rocafort 0 条。LaMa 两个入口可能重复。此次按题名和可用摘要筛选，重点打开与画作、评测、画材及幻觉相关的正文。另以 Semantic Scholar 交叉核查后三个种子。零条表示索引未返回结果；索引遗漏、摘要缺失和较新论文都可能限制检索。

## 对 v1 的两项修订

1. **跨画种、跨模型评测已有近邻。** Controlled-300 已大规模比较现成补全管线，覆盖多类视觉内容。把版画单案例、单画种多模型比较与跨物质媒介分层分开。对本项目仍待检验的问题是，在同一完好图、位置和缺损面积下，真实破损轮廓与随机轮廓是否导致不同的模型误差、失效类型或排序，以及这种差异是否随画材变化。
2. **画作修复已有幻觉分析，通用补全已有自动语义指标。** 壁画、古画和艺术图像修复已有语义幻觉案例或代理指标。通用补全已有掩码内 CLIP，跨修复任务已有局部语义幻觉指标。将本文贡献写为检验这些自动指标能否识别画作中局部内容偏离，并报告它们在不同画材和破损形状下的局限。

## 最相关的一手证据

| 工作 | 已经做到 | 与本项目的区别 |
| --- | --- | --- |
| Cipolina-Kun、Caenazzo、Mazzei，*Comparison of CoModGANs, LaMa and GLIDE for Art Inpainting Completing M.C Escher’s Print Gallery*，CVPR Workshops 2022 | 定量比较三个现成补全模型，测试图由同一幅埃舍尔石版画变换取得。另有一幅湿壁画作定性展示。版画中央未完成区域没有作者原作真值。 | 画材分层和基于已知原图的配对比较仍有空间。[会议全文](https://openaccess.thecvf.com/content/CVPR2022W/NTIRE/papers/Cipolina-Kun_Comparison_of_CoModGans_LaMa_and_GLIDE_for_Art_Inpainting_Completing_CVPRW_2022_paper.pdf) |
| Hu、Zhou、Gao、Zhang、Geng、Zhou，*Imagest*，npj Heritage Science，2025 | 在 100 幅名画的人工损伤图上比较多种模型。表 2 报告平均 FID、LPIPS、修复区 SSIM 和 PSNR，图例覆盖油画和中国画风格。 | 表 2 给出总体结果。按画材分层及真实轮廓对照仍有空间。[期刊全文](https://www.nature.com/articles/s40494-025-02167-y) |
| Maddineni，*Trustworthy Evaluation Frameworks for AI-Assisted Painting Restoration*，2026 年硕士研究档案 | Controlled-300 有 300 幅画作和四种现成管线（Telea、LaMa、HINT、Stable Diffusion），2,620 个合格案例产生 10,480 个对应候选。核心统计为 1,200 个合成损伤案例，另有 10 幅真实损伤诊断。用掩码内误差、感知相似、颜色、纹理、边界、语义特征和多种子不确定性评价。SDXL 仅做小样本可行性测试。 | 五组为肖像、风景、建筑、抽象和高纹理等视觉类别。主实验的掩码是人工生成的，包括面积、几何和摆位敏感性；真实损伤诊断无完好真值。本项目需与这些稳健性试验明确区分。[Zenodo 档案及勘误](https://zenodo.org/records/23092185) · [作者方法记录](https://github.com/Rahul-DS25M008/painting_restoration_eval/blob/main/docs/methodology_notes.md) |
| Vijendran、Chen、Shum，*MDTD-ArtIR*，2026 年 arXiv 预印本 | 从 WikiArt 抽取 1,000 幅方形画作，主要为风景。用 DTD 纹理透明罩制造破损，按不透明度比较多种通用修复及图像编辑模型。用 MAE、PSNR、SSIM、LPIPS，并讨论人物身份、内容和纹理幻觉。 | 研究盲修复半透明叠加；本项目拟研究已给定二值缺损、按画材分层的局部补全。[原文 §§3.1、3.5、4.1、4.4](https://arxiv.org/html/2608.00736v1) |
| Zhang、Zhu、Li、Liu、Jia、Zhang、Sun，*From traditional craft to digital restoration: an intelligent rebirth of ancient Chinese painting restoration technique*，Humanities and Social Sciences Communications，2026 | InkRenew 用真实破损形状模拟古画缺损，图 9 有工笔、水墨等例子；研究另用 LoRA、自动指标与专家评估，并讨论模型生成原作中没有的笔触。 | v1 所述「真实破损形状尚未用于画作修复」应删除。区别在于按画材进行同图、同面积、同位置的形状来源对照，以及比较冻结模型。[期刊全文](https://www.nature.com/articles/s41599-026-07117-y) |
| Ren、Huang，*MAPGR*，npj Heritage Science，2026 | 壁画补全以缓解语义幻觉为核心，报告 PSNR、SSIM、FID 和 LPIPS，并指出需要标准化的图像学幻觉定量方法。 | 画作修复中已经明确提出语义幻觉问题。通用指标与原创内容偏离的对应关系仍需用受控样本验证。[期刊全文](https://www.nature.com/articles/s40494-026-02607-3) |
| Wang 等，*Towards Enhanced Image Inpainting: Mitigating Unwanted Object Insertion and Preserving Color Consistency*，CVPR 2025 | 用 CLIP@mask 比较补全区域与原图的语义特征，也用 Gradient@edge 看颜色接缝。MISATO 为自然图像上的多域补全基准。 | CLIP@mask 是直接可复用的补全先例，需检验其对画作局部内容变动的敏感性。[会议全文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_Towards_Enhanced_Image_Inpainting_Mitigating_Unwanted_Object_Insertion_and_Preserving_CVPR_2025_paper.pdf) |
| Kim、Tregidgo、Jin、Figini、Alexander，*HalluGen: Synthesizing Realistic and Controllable Hallucinations for Evaluating Image Restoration*，CVPR 2026 | 用受控幻觉样本验证 SHAFE，重点测试稀疏局部的语义改变。主实验为 MRI，并跨任务验证。 | 可借鉴正负对照和局部聚合。画作上是否有效仍需验证。[会议全文](https://openaccess.thecvf.com/content/CVPR2026/papers/Kim_HalluGen_Synthesizing_Realistic_and_Controllable_Hallucinations_for_Evaluating_Image_Restoration_CVPR_2026_paper.pdf) |
| Rocafort、Su、Gomez-Villa、Vazquez-Corral，*Evaluating and Preserving High-level Fidelity in Super-Resolution*，2025 年 arXiv 预印本 | 用 723 对自然图像超分结果和真值，结合独立用户判断验证语义改变代理指标。 | 可作高层保真指标的邻域证据。本文只使用基于原图和已知扰动的自动验证，不需招募评分人。[作者全文 §§3–4](https://arxiv.org/html/2512.07037v2) |

## 其他证据与限定

- Shao、Xu、Wen、Gao、Yang、Huang 的 ICCV 2023 壁画研究同时使用模拟破损和真实破损配对。其 §5.1、表 1–2 对真实破损报告定量结果，参照是修后图像；模拟样本才具有未损原图真值。v1 的「真实破损只能目测」应改为「真实破损通常缺少未损原图，可用修后图或其他证据作参照，并注明来源」。
  [会议全文](https://openaccess.thecvf.com/content/ICCV2023/papers/Shao_Building_Bridge_Across_the_Time_Disruption_and_Restoration_of_Murals_ICCV_2023_paper.pdf)
- Zhenglang Jiang、Jianhao Liu、Wuhan Yan、Xianfang Wang、Siyu Jiang、Qingyu Yang、Zhao Li 的 *Restoring with Reason*（ACM Multimedia 2026）官方摘要说，克孜尔石窟评测考虑感知质量和历史忠实度，并使用专家核验的参照和史料。核对到大会摘要，指标定义及参照图的性质仍待全文核对。
  [会议程序](https://2026.acmmm.org/site/technical-programme.html) · [论文 DOI](https://doi.org/10.1145/3767308.3835762)
- Alex Kachkine 的 Nature 2025 研究以一幅板上油画演示可逆数字掩膜的实体修复。缺损覆盖、遗漏和越界可以检查；原作缺失处的具体内容仍无法直接验证。
  [期刊原文](https://www.nature.com/articles/s41586-025-09045-4)
- ARTeFACT 的正式发表为 Ivanova、Aversa、Henderson、Williamson，WACV 2025。论文 §4 的跨类别比较针对破损分割，指标评价掩码检测。可借用破损分类和形状来源，但其结果不能直接解释为补全质量。
  [会议全文](https://openaccess.thecvf.com/content/WACV2025/papers/Ivanova_ARTeFACT_Benchmarking_Segmentation_Models_on_Diverse_Analogue_Media_Damage_WACV_2025_paper.pdf)

## ARTeFACT 样本与许可

- **统计口径。** 固定在 Hugging Face 修订版 `eabf09542f871c6c61147474408704152e08f831`，通过 HTTP Range 逐个读取 28 个 Parquet 分片的 `id`、`type`、`material` 列。共 418 行、418 个唯一 ID，其中 `type == "Painting"` 有 49 行，基底为画布（Canvas）23、木板（Wood）26。另有湿壁画（Fresco）25、石版画（Lithograph）4，单独计数。基底标签无法推断颜料、画种或某类破损的可用掩码数。本次统计未下载图像或掩码。[固定版本的数据目录](https://huggingface.co/datasets/danielaivanova/damaged-media/tree/eabf09542f871c6c61147474408704152e08f831/data)
- **不同许可对象。** 会议论文 §3 描述底图从采用 CC 许可的来源收集，未列出逐图条款。作者发布的 Hugging Face 数据卡标为 AFL-3.0，arXiv 所列 CC BY-NC-SA 4.0 是该预印本的许可标记。三者需分别追溯。[会议全文](https://openaccess.thecvf.com/content/WACV2025/papers/Ivanova_ARTeFACT_Benchmarking_Segmentation_Models_on_Diverse_Analogue_Media_Damage_WACV_2025_paper.pdf) · [数据卡](https://huggingface.co/datasets/danielaivanova/damaged-media/blob/eabf09542f871c6c61147474408704152e08f831/README.md) · [arXiv 全文页](https://arxiv.org/html/2412.04580v1)
- **移植与公开。** AFL-3.0 第 1、6、9 条允许在许可范围内创建和发布衍生作品，并规定保留署名和许可通知、标明修改、采取合理步骤取得收件人对条款的同意。数据卡未给出逐图溯源或单独的掩码授权说明。应在公开实验包前确认哪些标注可适用该许可、底图权利是否影响对应掩码，以及怎样履行条款。在此之前，公开的试验方案可以使用程序生成且许可清楚的掩码。[AFL-3.0 正文](https://opensource.org/license/afl-3-0-php)

## 指标和修复伦理

- 将掩码内 MAE、色差和边缘连续性等作为局部原图差异。LPIPS、DISTS 和掩码内 CLIP/DINO 相似度都是有参考的指标，可分别描述感知、纹理、结构或语义的近似。DISTS 对同类纹理重采样的容忍度是其测量性质，用它单独命名「自然度」会把两类问题混在一起。感知—失真权衡刻画输出分布与真值失真的关系，结论不应外推成单幅画的两个分数必然此消彼长。
  [DISTS 原文](https://arxiv.org/abs/2004.07728) · [感知—失真权衡，CVPR 2018](https://openaccess.thecvf.com/content_cvpr_2018/html/Blau_The_Perception-Distortion_Tradeoff_CVPR_2018_paper.html)
- 先用原图构造已知类型的对照，例如局部色偏、笔触纹理扰动、结构或图案替换。报告各指标对目标改变和非目标改变的敏感性。生成种子之间的分歧提供稳定性证据，语义偏离则需要与原图比较。
- ICOM-CC 2008 术语决议以尊重原始材料为基础，并举补色为修复的例子。AIC 实务指南第 23 条要求记录补失、可以通过常见检查方法辨识，且处理可逆。数字流程可据此保留原图、输出、掩码和参数，报告未损区改动。此处借鉴保护专业原则，真实画作的处理决定由修复人员作出。
  [ICOM-CC 决议](https://www.icom-cc.org/en/terminology-for-conservation) · [AIC 实务指南](https://community.culturalheritage.org/conservation-at-work/uphold-professional-standards/code)

## 后续判据

如果等面积、同位置配对显示破损形状改变了模型选择或风险判断，可把它作为核心结果，并在独立画作和掩码组中复核。如果差异小、受少数作品驱动或无法稳定重复，应报告效应及其不确定性，避免把更换模型或扩大作品数量写成独立创新。文献核查支持这项假设值得小试；现有文献和本次检索都无法替代实验。
