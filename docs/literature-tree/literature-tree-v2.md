# 画作数字补全文献树

- 版本 v2，Codex，2026-11-20，待复审。
- 检索记录截至 2026-11-18，本文选用的一手来源于 2026-11-20 复核。保留 [v1](literature-tree-v1.md)，勘误、检索式和证据边界见 [核查记录](../../literature/audit-of-claude-v1.md) 与 [检索日志](../../literature/search-log.md)。

现成模型比较、固定面积的掩码对照和真实轮廓移植都已有先例。本项目优先检验在有完好原图的 CC0 画作上，采用同样的原像素取样和评分协议，模型误差及相对表现怎样随绘画技法、基底、缺损形状和面积而变化。四组原尺度探索结果已经取得。主实验扩大到每组 15 幅，抽样顺序和安全检查拦截后的分母已冻结。六家馆藏的供给已按许可和图像证据核查。真实轮廓分支仍受供体数量、出处和许可限制。[网格修正](../LATENT_ALIGNMENT.md) · [PR #11 复审](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/11) · [冻结方案](../INNOVATION.md#pr-11-复审后的原尺度主实验) · [馆藏计数](../CC0_AVAILABILITY.md)

## 怎么读

- 按彭思达的选题方法和 findInnovation 模板组织通用补全管线、画作修复与基准、评价与修复规范三条脉络。画材分层问题取自三条线相交处。里程碑标签表示它改变了哪类任务或评价方法。[选题课件](https://pengsida.net/files/research_topic_selection.pdf) · [findInnovation](https://github.com/Casey-sketch-cyber/findInnovation)
- 时间线列出正式发表版本、作者预印本、研究档案或发布者文档。表中注明用于判断的摘要、章节、图表或档案。前向筛查在 OpenAlex 中覆盖 LaMa、ARTeFACT、Shao、Kachkine、Rocafort 五个种子，对后三个用 Semantic Scholar 交叉核查，再用独立关键词找近邻。索引重复、时滞与摘要缺失限制覆盖范围。[覆盖范围与核对结果](../../literature/audit-of-claude-v1.md)
- 项目在单张 RTX 3090（24 GiB）上使用冻结的现成模型，完好底图来自可核实的开放许可馆藏，没有可用评分人。面向数字修复研究人员和需要选择补全管线的从业者，交付可以复核的比较协议、区间和适用边界。[运行环境与数据流](../ARCHITECTURE.md)

## 长远目标与路线图

让使用画作数字补全的人能根据画材和缺损条件选择工具，并知道对原貌的判断有多少证据。

| 里程碑任务 | 内容 | 现状 | 判断 |
| --- | --- | --- | --- |
| 通用局部补全 | 在给定掩码下延续边缘、纹理或语义内容 | 大洞与不规则洞有成熟的卷积、注意力和扩散方案 | 本项目使用冻结权重作为比较对象 |
| 分层的已知原图评测 | 以统一裁片与掩码协议比较现成模型在四组画作上的表现 | 已有单幅版画、多画种图例及按图像内容分组的大型研究。项目原尺度先导每组四幅，扩样方案已冻结 | 优先检验画材分层与破损条件能否提供稳定的选型信息 |
| 形状来源效应 | 在同画材、同基底内，配对比较真实供体轮廓与程序轮廓 | 真实轮廓移植已有先例。目标破损类的合格供体尚不足以确认 | 条件成熟后另做配对先导 |
| 内容偏离诊断 | 用完好原图和已知局部扰动检验指标能分辨哪些错误 | 已有局部语义代理与受控幻觉样本。画作上的验证仍有限 | 作为指标解释的后续验证 |
| 实体修复 | 将数字方案用于原作处置 | 有单件油画的可逆介入实例 | 需要独立的实体条件和专业决策 |

## 领域视野六问

| 问题 | 回答 | 依据 |
| --- | --- | --- |
| 里程碑有哪些 | Image Inpainting、样例补全、Context Encoders、LaMa、Latent Diffusion、Shao 的壁画数据与 ARTeFACT | 时间线一、二 |
| 技术怎样演变 | 从局部延拓与复制本图样例，发展到学得的全局上下文、潜空间生成和任务提示 | 时间线一 |
| 领域的终极目标 | 对已知内容作可追溯的重建，对缺乏证据的区域表达不确定性，并保存原始数字记录供核查 | 时间线二、三 |
| 目前达到什么水平 | 通用大洞补全已有可用管线。画作研究已比较现成模型及专用模型，模拟破损可与完好原图比较，部分真实破损采用修后参照 | Controlled-300、Imagest、Shao |
| 哪些重要问题未解决 | 在各画材组共享条件下的模型差大小、破损条件的交互、扩张遮挡和安全检查对比较人群的影响，以及自动语义代理在画作上的误检 | 时间线二、三和项目诊断 |
| 当前热点 | 真损伤检测及可控模拟、通用扩散模型的画作适配、局部高层保真度和修复记录可追溯性 | ARTeFACT、InkRenew、MAPGR、HalluGen |

## 时间线一　通用补全管线

早期方法靠图内可见结构约束缺失区。学习方法加入全局先验，模型能生成原图缺失处可能出现的内容。掩码、条件图和推理尺度如今也是实验变量。

| 年份 | 工作与发表处 | 角色 | 问题与技术启发 | 留下的问题及核对依据 |
| --- | --- | --- | --- | --- |
| 2000 | Bertalmio、Sapiro、Caselles、Ballester，*Image Inpainting*，SIGGRAPH | 里程碑 | 用沿等照度线的局部传播延续边缘，列举画作修补应用 | 大片纹理与内容缺失需更多证据。[大会原文档案与摘要](https://history.siggraph.org/?p=118295) |
| 2004 | Criminisi、Pérez、Toyama，*Region Filling and Object Removal by Exemplar-Based Image Inpainting*，IEEE Transactions on Image Processing 13(9) | 里程碑 | 按结构和填补置信度定顺序，从已知区域采样图块延续结构和纹理 | 依赖局部存在合适的样例。[作者全文 §§I–III](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/criminisi_tip2004.pdf) |
| 2016 | Pathak、Krähenbühl、Donahue、Darrell、Efros，*Context Encoders: Feature Learning by Inpainting*，CVPR | 里程碑 | 上下文编码结合重建与对抗损失，对缺失区学习语义先验 | 规则缺口与照片实验的结论需在画作上检验。[会议摘要与论文](https://openaccess.thecvf.com/content_cvpr_2016/html/Pathak_Context_Encoders_Feature_CVPR_2016_paper.html) |
| 2018 | Liu、Reda、Shih、Wang、Tao、Catanzaro，*Image Inpainting for Irregular Holes Using Partial Convolutions*，ECCV | 后续 | 在有效像素上归一化卷积并逐层更新掩码，处理不规则缺口 | 通用掩码覆盖范围宽，画材损伤几何需专门取样。[会议摘要与论文](https://openaccess.thecvf.com/content_ECCV_2018/html/Guilin_Liu_Image_Inpainting_for_ECCV_2018_paper.html) |
| 2022 | Suvorov、Logacheva、Mashikhin、Remizova、Ashukha、Silvestrov、Kong、Goka、Park、Lempitsky，*Resolution-Robust Large Mask Inpainting With Fourier Convolutions*，WACV | 里程碑 | LaMa 用快速傅里叶卷积获取全局感受野，以大掩码训练并测试分辨率泛化 | 照片上的基准不能覆盖绘画技法与基底变化。[会议摘要与论文](https://openaccess.thecvf.com/content/WACV2022/html/Suvorov_Resolution-Robust_Large_Mask_Inpainting_With_Fourier_Convolutions_WACV_2022_paper.html) |
| 2022 | Li、Lin、Zhou、Qi、Wang、Jia，*MAT: Mask-Aware Transformer for Large Hole Image Inpainting*，CVPR | 后续 | 在注意力中依据动态掩码聚合有效位置，处理高分辨率的大洞 | 作为结构不同的非扩散对照，需记录实际权重和推理设置。[会议摘要与论文](https://openaccess.thecvf.com/content/CVPR2022/html/Li_MAT_Mask-Aware_Transformer_for_Large_Hole_Image_Inpainting_CVPR_2022_paper.html) |
| 2022 | Rombach、Blattmann、Lorenz、Esser、Ommer，*High-Resolution Image Synthesis With Latent Diffusion Models*，CVPR | 里程碑 | 将扩散放入自编码器的潜空间，并在多个任务中验证条件生成与补全 | 压缩和掩码的采样尺度可能改变细破损的条件输入。[会议摘要与论文](https://openaccess.thecvf.com/content/CVPR2022/html/Rombach_High-Resolution_Image_Synthesis_With_Latent_Diffusion_Models_CVPR_2022_paper.html) |
| 2023 | Diffusers 团队，*SD-XL Inpainting 0.1*，Hugging Face 模型卡 | 后续 | 1024² 上训练，增加掩码和遮挡后图像的输入通道。示例在 1024 推理 | 模型卡的 strength 0.99 在本项目预遮挡条件下引入填补颜色的影响。[固定模型卡](https://huggingface.co/diffusers/stable-diffusion-xl-1.0-inpainting-0.1/blob/115134f363124c53c7d878647567d04daf26e41e/README.md) · [填色对照](../SDXL_PREFILL.md) |
| 2024 | Zhuang、Zeng、Liu、Yuan、Chen，*A Task Is Worth One Word: Learning with Task Prompts for High-Quality Versatile Image Inpainting*，ECCV 2024（文集为 2025 年） | 后续 | PowerPaint 用任务提示区分上下文补全、对象补全等需求 | 项目通用修复提示、预算和拦截后的样本分母需随结果记录。[会议论文及摘要](https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/7554_ECCV_2024_paper.php) · [决策记录](../DECISIONS.md) |

LaMa 和 MAT 为查验图内延续提供两个非扩散对照，SDXL 和 PowerPaint 提供条件生成对照。正文 SDXL 采用网格对齐后的 strength 1.0。0.99 按黑色、中灰、洞外环带平均色单列。每幅裁片从扩张掩码外的 8 像素环带求一个颜色，整个输入洞使用同一个颜色。历史 1024 的 0.99 只有黑色条件。原尺度填色敏感性包含 16 幅，网格修正后四模型总体采用 12 幅完整作品，跨报告数值只能作量级参考。[填色对照](../SDXL_PREFILL.md) · [网格修正](../LATENT_ALIGNMENT.md) · [复审口径](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/11)

## 时间线二　画作修复、真实损伤与比较基准

画作研究同时推进了专用复原、多模型比较和真实破损标注。需要区分给定掩码补全、未知损伤修复、破损检测，以及数字结果和物理处置。

| 年份 | 工作与发表处 | 角色 | 问题与技术启发 | 留下的问题及核对依据 |
| --- | --- | --- | --- | --- |
| 2022 | Cipolina-Kun、Caenazzo、Mazzei，*Comparison of CoModGans, LaMa and GLIDE for Art Inpainting Completing M.C Escher's Print Gallery*，CVPR Workshops | 直接先例 | 比较三个现成模型。其定量用同一幅石版画的变换图，另有湿壁画定性示例 | 版画未完成区没有作者原作真值，画材组间比较仍需多幅作品。[会议全文](https://openaccess.thecvf.com/content/CVPR2022W/NTIRE/papers/Cipolina-Kun_Comparison_of_CoModGans_LaMa_and_GLIDE_for_Art_Inpainting_Completing_CVPRW_2022_paper.pdf) |
| 2023 | Shao、Xu、Wen、Gao、Yang、Huang，*Building Bridge Across the Time: Disruption and Restoration of Murals In the Wild*，ICCV | 里程碑 | 用 Blender 模拟壁画损伤，另对真实破损定量。模拟数据有未损原图，真实数据以修后图作参照 | 原图与修后参照各有不同证据含义。壁画结果可用于设计域转移检验。[会议全文 §5.1、表 1–2](https://openaccess.thecvf.com/content/ICCV2023/papers/Shao_Building_Bridge_Across_the_Time_Disruption_and_Restoration_of_Murals_ICCV_2023_paper.pdf) |
| 2024 | Sun、Lei、Wu，*Ancient paintings inpainting based on dual encoders and contextual information*，Heritage Science 12，266 | 后续 | 双编码器、上下文融合和颜色损失用于中国古画，含 LaMa 对照、程序掩码和真实破损图例 | 专用网络比较给出邻域证据，统一四组原像素设计需另建样本。[期刊正文](https://www.nature.com/articles/s40494-024-01391-2?error=cookies_not_supported) |
| 2025 | Ivanova、Aversa、Henderson、Williamson，*ARTeFACT: Benchmarking Segmentation Models on Diverse Analogue Media Damage*，WACV | 里程碑 | 为 418 张多媒材图像提供真实损伤像素标注，构成跨媒材破损分割基准 | 划定的是损伤位置。形状供体仍需查到油画技法、基底和逐项许可。[会议全文 §3–4](https://openaccess.thecvf.com/content/WACV2025/papers/Ivanova_ARTeFACT_Benchmarking_Segmentation_Models_on_Diverse_Analogue_Media_Damage_WACV_2025_paper.pdf) |
| 2025 | 薛文喆、董兴宇、胡琦瑶、曹瑞、彭先霖，《基于孪生级联空间滤波的中国传统画修复》，《西北大学学报（自然科学版）》55(1)，150–167 | 直接先例 | 从残缺画作提取掩码并与完好图拼接。在训练与测试涉及真实样例掩码和自由孔洞掩码 | 掩码移植已有独立先例。来源效应需用同图、同面积、同位置配对估计。[期刊正文 §2.1、图 2 和图 4](https://xdxbzk.nwu.edu.cn/zh/article/doi/10.16152/j.cnki.xdxbzr.2025-01-013/) |
| 2025 | Kachkine，*Physical restoration of a painting with a digitally constructed mask*，Nature 642，343–350 | 实体应用里程碑 | 在单件板上油画用可逆数字掩膜实施实体修复，展示可记录的缺损覆盖和补色操作 | 操作边界可以检查，缺失处原内容依然未知。[期刊原文和摘要](https://www.nature.com/articles/s41586-025-09045-4?error=cookies_not_supported) |
| 2025 | Hu、P. Zhou、Gao、Zhang、Geng、M. Zhou，*Imagest: a style conditioned art painting synthesis and generation networks*，npj Heritage Science 13，613 | 直接先例 | 100 幅名画的人工损伤测试中，比对 Imagest 与 VQGAN、SD 1.4、SD 1.5、DALL·E 2 | 表 2 汇总 FID、LPIPS、修复区 SSIM 与 PSNR，画材分层效果需另报。[期刊正文](https://www.nature.com/articles/s40494-025-02167-y?error=cookies_not_supported) · [表 2](https://www.nature.com/articles/s40494-025-02167-y/tables/2?error=cookies_not_supported) |
| 2026 | Y. Zhang、Zhu、Li、Liu、Jia、J. Zhang、Sun，*From traditional craft to digital restoration: an intelligent rebirth of ancient Chinese painting restoration technique*，Humanities and Social Sciences Communications 13(1)，1342 | 直接先例 | InkRenew 图 5 说明使用真实破损轮廓模拟缺损，展示四种古画风格。研究也使用 LoRA、自动指标和专家评价 | 工笔、水墨等类别说明风格覆盖，定量样本逐个来源、供体匹配与许可待查。[期刊正文](https://www.nature.com/articles/s41599-026-07117-y?error=cookies_not_supported) · [图 5](https://www.nature.com/articles/s41599-026-07117-y/figures/5?error=cookies_not_supported) |
| 2026 | Vijendran、Chen、Shum，*MDTD-ArtIR: Benchmarking Image Editing and Restoration Models for Art Image Restoration under Texture-Overlay Degradations*，arXiv 预印本 | 相邻基准 | 1,000 幅 WikiArt 画作多为风景。以不同不透明度的纹理叠加测盲修复并分析内容、身份、纹理错误 | 透明纹理叠加与给定二值缺损是不同输入条件。[作者全文 §§3.1、3.5、4.1、4.4](https://arxiv.org/html/2608.00736v1) |
| 2026 | Maddineni，*Trustworthy Evaluation Frameworks for AI-Assisted Painting Restoration: Controlled-300 Research Artifacts*，Zenodo 硕士研究档案 | 最近的评测先例 | 300 幅按肖像、风景、建筑、抽象、高纹理分组。2,620 个合格案例生成四管线的 10,480 个候选，核心统计有 1,200 个合成损伤案例。另在 35 幅做固定家族和像素面积的形状或摆位对照 | 项目重点是技法与基底分组和原像素协议的模型差，保留此前已有的固定面积思路。档案发布类型为 Software。[发布档案与勘误](https://zenodo.org/records/23092185) · [作者方法记录](https://github.com/Rahul-DS25M008/painting_restoration_eval/blob/main/docs/methodology_notes.md) |

Controlled-300 已报告 LaMa 在其匹配样本上具有较低平均掩码内 MAE，因此单报 LaMa 总平均占优的增量有限。可验证的增量来自四组共享原像素协议下的作品级差、条件级不确定性和技术失败分母。相机、数字化流程、馆藏来源与题材仍可能随组变化。画布与木质基底两组同限定为油画，适合优先观察基底分组差异。[Controlled-300 发布说明](https://zenodo.org/records/23092185) · [原尺度取样设计](../INNOVATION.md#原尺度裁片试跑)

## 时间线三　全参考指标、语义代理与保护规范

已知原图时可计算局部像素、色差、感知距离与语义特征差。这些读数的用途取决于原图、评价区域和受控扰动的定义。

| 年份 | 工作与发表处 | 角色 | 问题与技术启发 | 留下的问题及核对依据 |
| --- | --- | --- | --- | --- |
| 2005 | Sharma、Wu、Dalal，*The CIEDE2000 color-difference formula: Implementation notes, supplementary test data, and mathematical observations*，Color Research & Application 30(1)，21–30 | 计量依据 | 给出 CIEDE2000 的实现细节与测试例 | 项目分别报告逐像素色差和两图各自洞内平均 Lab 之间的色差。局部结构和题材变化需结合其他证据。[期刊页](https://onlinelibrary.wiley.com/doi/10.1002/col.20070) · [作者测试材料](https://hajim.rochester.edu/ece/sites/gsharma/ciede2000/) |
| 2018 | Blau、Michaeli，*The Perception-Distortion Tradeoff*，CVPR | 理论里程碑 | 分析复原结果的分布可辨识性与期望失真之间的约束 | 分布层面的理论不能推出单幅画上任意两个指标的分数反向变化。[会议摘要与论文](https://openaccess.thecvf.com/content_cvpr_2018/html/Blau_The_Perception-Distortion_Tradeoff_CVPR_2018_paper.html) |
| 2018 | Zhang、Isola、Efros、Shechtman、Wang，*The Unreasonable Effectiveness of Deep Features as a Perceptual Metric*，CVPR | 指标里程碑 | 用深层特征距离度量感知相似，原文以人对图像对的判断验证 LPIPS | 本项目只用公开固定指标，报告局部全参考距离，仍需注意画作域的适用范围。[会议摘要与论文](https://openaccess.thecvf.com/content_cvpr_2018/html/Zhang_The_Unreasonable_Effectiveness_CVPR_2018_paper.html) |
| 2022 | Ding、Ma、Wang、Simoncelli，*Image Quality Assessment: Unifying Structure and Texture Similarity*，IEEE TPAMI 44(5)，2567–2581（2020 年先行） | 指标后续 | DISTS 结合结构和纹理特征，对同类纹理重采样具有一定容忍度 | 输出与原图的全参考相似性与独立自然度是不同量，DISTS 也不能单独识别内容替换。[作者论文](https://arxiv.org/abs/2004.07728) · [正式卷期](https://pubmed.ncbi.nlm.nih.gov/33338012/) |
| 2025 | Wang、Cao、Yu、Fan、Xue、Fu，*Towards Enhanced Image Inpainting: Mitigating Unwanted Object Insertion and Preserving Color Consistency*，CVPR | 补全评价后续 | MISATO 用 CLIP@mask 衡量自然图像补全区与原图的语义特征，用 Gradient@edge 表征接缝 | 画作上的笔触、色偏和内容变化需要可区分的已知扰动。[会议全文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_Towards_Enhanced_Image_Inpainting_Mitigating_Unwanted_Object_Insertion_and_Preserving_CVPR_2025_paper.pdf) |
| 2025 | Rocafort、Su、Gomez-Villa、Vazquez-Corral，*Evaluating and Preserving High-level Fidelity in Super-Resolution*，arXiv 预印本 | 邻域后续 | 用 723 对自然图像超分输出与真值，结合用户判断，检验高层保真代理指标 | 画作补洞可借鉴验证思路，以相对原图的已知扰动代替人工评分。[作者全文 §§3–4](https://arxiv.org/html/2512.07037v2) |
| 2026 | Kim、Tregidgo、Jin、Figini、Alexander，*HalluGen: Synthesizing Realistic and Controllable Hallucinations for Evaluating Image Restoration*，CVPR | 邻域后续 | 构造受控的局部语义改变以检验 SHAFE，主要实验在 MRI，另有跨任务检验 | 应在画作上验证代理对已知内容变动的敏感性及对色偏的误报。[会议全文](https://openaccess.thecvf.com/content/CVPR2026/papers/Kim_HalluGen_Synthesizing_Realistic_and_Controllable_Hallucinations_for_Evaluating_Image_Restoration_CVPR_2026_paper.pdf) |
| 2026 | Ren、Huang，*MAPGR: Multi-Agent Prompt-Guided Residual Diffusion for ancient mural restoration*，npj Heritage Science | 画作修复后续 | 将壁画中的语义幻觉作为方法问题，报告 PSNR、SSIM、FID、LPIPS，并讨论标准化的图像学幻觉量化 | 画作修复已有问题分析，现成指标与局部史实或题材偏离的对应仍需验证。[期刊全文](https://www.nature.com/articles/s40494-026-02607-3?error=cookies_not_supported) |

ICOM-CC 的 2008 年术语决议强调尊重原始材料，举补色为修复活动。AIC《Code of Ethics and Guidelines for Practice》第 23 条要求记录补失处理、可通过常见检查辨识并可逆。数字实验据此保留原图、掩码、输出、参数和洞外一致性核验，使人能追查改动。实体画作的处置另需专业判断。[ICOM-CC 决议](https://www.icom-cc.org/en/terminology-for-conservation) · [AIC 专业指南](https://community.culturalheritage.org/conservation-at-work/uphold-professional-standards/code)

## 按里程碑任务归类的代表性管线

| 任务 | 代表性管线 | 代表工作 |
| --- | --- | --- |
| 延续已见的画线和纹理 | 局部传播与图内图块匹配 | Bertalmio、Criminisi |
| 不规则及大面积缺损 | 有效像素卷积、傅里叶全局卷积、掩码感知注意力 | Partial Convolutions、LaMa、MAT |
| 条件生成和任务控制 | 潜空间扩散、图像与掩码条件、任务提示 | Latent Diffusion、SDXL Inpainting、PowerPaint |
| 在画作上比较补全 | 人工损伤与原图成对、多个模型共享场景、按内容或损伤分组 | 石版画对照、Shao、Imagest、Controlled-300 |
| 标注或移植损伤形状 | 像素级破损检测、模拟生成、残画轮廓配完好图 | ARTeFACT、Shao、薛等、InkRenew |
| 检验结果偏离原貌 | 局部原图差异、感知距离、受控语义扰动 | LPIPS、DISTS、MISATO、HalluGen |

## 难点与解法树

现成方法解决了补全的工程入口。画作基准的难点在于参照的含义、模型实际收到的输入、分层样本和指标解释。

| 难点 | 现有解法 | 依据 | 对本研究还缺什么 | 邻域同类问题 |
| --- | --- | --- | --- | --- |
| 真实缺失区域无法取得未损原图 | 修后参照、完好图加模拟损伤、移植真实轮廓 | Shao、薛等、InkRenew | 分别标明三种证据。用成对原图检验程序条件，再以合法匹配供体验证形状来源 | 自然图像编辑、超分辨率 |
| 已有大基准分组与画材问题不同 | 内容类别、单画种现成模型对照 | Controlled-300、石版画比较 | 固定程序掩码材料对照，检验条件级模型差。跨水墨、水彩和油画比较需注明材料与题材等共变 | 自然图像跨任务基准 |
| 细破损经过潜空间网格可能漏采 | 重放最近邻取样，扩张至命中的完整网格 | 项目网格诊断 | 共享扩张遮挡作为主比较，另评估 LaMa/MAT 原掩码输入敏感性。原洞用于最终合成和定义评分区域 | 潜空间编辑与小目标生成 |
| 部分补全候选无可用结果 | 记录技术失败、安全拦截和完整配对 | 项目网格修正后 PowerPaint 可用 85/96，四模型六条件完整为 12 幅 | 主实验按已冻结的分母规则报告计划数、可评分数和拦截数 | 多模型比较的选择性缺失 |
| 指标读数不能分辨偏色、纹理和内容错误 | 多项全参考指标、掩码内语义特征、受控改动 | LPIPS、DISTS、MISATO、HalluGen | 先用已知的色偏、纹理和图案替换检查代理性质。局部 LPIPS、DISTS 取原掩码外接框并留 8 像素上下文 | 长距离结构评价、生成超分、MRI 复原 |

项目已复查细掩码漏采和 0.99 初始化的预填充依赖，当前比较沿用经核查的推理设置。参数敏感性的作用是约束结论适用范围，进一步证据优先来自扩大作品样本。[网格诊断](../LATENT_ALIGNMENT.md) · [模型卡参数对照](../OFFICIAL_INFERENCE.md) · [PR #11 复审](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/11)

## 候选课题

| 候选 | 设定 | 待检验问题 | 来源 |
| --- | --- | --- | --- |
| C1 原像素画材分层评测 | CC0 画作四组 × 程序裂缝、剥落、广片缺失 × 1% 与 5%，评估冻结的四条补全管线 | 画材分组和损伤条件是否改变模型差的量级、排序或可用率 | 选型需求、Controlled-300、原尺度先导 |
| C2 真实形状来源对照 | 同一完好裁片与落点，同面积真实轮廓和程序轮廓，供体按技法和基底匹配 | 真实轮廓来源是否改变模型差，效应是否随基底变化 | InkRenew、薛等、Shao 和 ARTeFACT |
| C3 指标失效分析 | 原图与已知色偏、纹理改变、图案替换，比较像素级和语义代理 | 哪些自动分数能对内容替换敏感，并容忍轻微非语义差异 | MISATO、HalluGen、Rocafort |
| C4 数字修补过程记录 | 原图、输出、掩码和参数形成可追溯记录 | 在分享或复查时能否确定补全位置、重现处理，并发现洞外改动 | 保护规范与修复从业者的核查需求 |

## 按四种情况判断

彭思达课件用四类描述解法成熟度。第一种是相同输入输出已有好方案。第二种是输入或输出有变化，或同一技术内核已在多个领域解决。第三种是少数一两个邻域已有好方案。第四种是相关领域均缺少好方案。类别用于描述技术状态，优先级还取决于价值、资源和可检验性。[选题课件](https://pengsida.net/files/research_topic_selection.pdf)

| 候选 | 情况 | 区别与判断 |
| --- | --- | --- |
| C1 | 第二种 | 已有现成管线和大型画作评测，输入按技法、基底和原像素破损条件统一。优先提高组选型结论的精度，也报告未见实际排序变化的条件及区间。 |
| C2 | 第一到第二种 | 移植管线已有，控制画材、位置和面积后可测来源带来的模型差。供体门槛决定何时可做。可依条件开展。 |
| C3 | 第二到第三种 | 局部语义代理和受控幻觉测试在邻域已有先例。画作域需验证指标对特定错误的反应，可作为小型后续。 |
| C4 | 第一种 | 数字记录与可逆补失有成熟原则。将可追溯性用于本项目报告，单独立题的增量有限。 |

## 未核实事项与下一步

- 现有检索未找到同时采用四个指定材料组合、原像素裁片、共享两档三类掩码及相同评分的已发表评测。已找到最接近的 Controlled-300、Imagest、石版画比较和 MDTD-ArtIR。结论限于检索覆盖，引用索引的未返回记录和检索时滞须保留。[检索细目](../../literature/search-log.md)
- CC0 可得性按馆藏对象逐项查验授权、技法、基底和可下载的尺寸。馆藏开放图的总量与四个画材组的可用数量应分别记录。原尺度主实验已冻结同一克利夫兰馆藏队列的画布油画、木质基底油画、纸本水彩和纸本水墨各 15 幅，其中包含先导的 16 幅。安全检查拦截保留在计划分母。总体结果按比较所需模型的六条件完整作品计算，逐条件按相应成功配对计算。[冻结方案](../INNOVATION.md#pr-11-复审后的原尺度主实验) · [项目待办](../PROGRESS.md)
- 真形状分支在 ARTeFACT 固定版统计到 49 条 Painting，其中画布 23、木质基底 26。有至少一个 Material loss 像素的独立条目分别至多 5 和 1，技法、对象身份和授权仍须逐件确认。论文补充材料提及出处记录，公开分片未核实到逐图对应表。数据卡标注 AFL-3.0，底图逐项条款与掩码再用、公开分发的范围须核实。先跑程序掩码。获得每组至少 15 个匹配且明确允许研究使用的独立供体后，再做真实轮廓的配对先导。[样本与许可核查](../../literature/audit-of-claude-v1.md#artefact-样本与许可) · [来源配对设计](../INNOVATION.md)
