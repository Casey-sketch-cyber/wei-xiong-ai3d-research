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
| Hu、Zhou、Gao、Zhang、Geng、Zhou，*Imagest*，npj Heritage Science，2025 | 提出 Imagest，在 100 幅名画的人工损伤图上将新方法与 VQGAN、Stable Diffusion 1.4、Stable Diffusion 1.5、DALL·E 2 四个基线比较。表 2 汇总 FID、LPIPS、修复区 SSIM 和 PSNR。 | 此表是新模型与基线的总体对照。图例覆盖油画和中国画风格，表中未按画材分层。[期刊全文](https://www.nature.com/articles/s40494-025-02167-y?error=cookies_not_supported) · [表 2](https://www.nature.com/articles/s40494-025-02167-y/tables/2?error=cookies_not_supported) |
| Maddineni，*Trustworthy Evaluation Frameworks for AI-Assisted Painting Restoration*，2026 年 10 月硕士研究档案 | Controlled-300 有 300 幅画作和四种现成管线（Telea、LaMa、HINT、Stable Diffusion），2,620 个合格案例产生 10,480 个对应候选。核心统计有 1,200 个合成损伤案例。在 35 幅画上做了形状或摆位的稳健性对照，每幅画的三个掩码家族各有五种变体，同组像素面积固定。另有 10 幅真实损伤诊断，缺少完好真值。 | 主实验按肖像、风景、建筑、抽象和高纹理分组。差别在于纳入同画材、同基底的真实轮廓来源，以及按技法和基底分层。Zenodo 类型为 Software，未见同行评审论文版本。[Zenodo 档案及勘误](https://zenodo.org/records/23092185) · [作者方法记录 §3](https://github.com/Rahul-DS25M008/painting_restoration_eval/blob/main/docs/methodology_notes.md) · [发布快照的对照样本表](https://media.githubusercontent.com/media/Rahul-DS25M008/painting_restoration_eval/2378961a8accb2ecde610ed60428879e8f52a8a8/outputs/06_mask_robustness_dataset_generation/data/cases.csv) |
| Vijendran、Chen、Shum，*MDTD-ArtIR*，2026 年 arXiv 预印本 | 从 WikiArt 抽取 1,000 幅方形画作，主要为风景。用 DTD 纹理透明罩制造破损，按不透明度比较多种通用修复及图像编辑模型。用 MAE、PSNR、SSIM、LPIPS，并讨论人物身份、内容和纹理幻觉。 | 研究盲修复半透明叠加；本项目拟研究已给定二值缺损、按画材分层的局部补全。[原文 §§3.1、3.5、4.1、4.4](https://arxiv.org/html/2608.00736v1) |
| Zhang、Zhu、Li、Liu、Jia、Zhang、Sun，*From traditional craft to digital restoration: an intelligent rebirth of ancient Chinese painting restoration technique*，Humanities and Social Sciences Communications 13(1), 1342，2026 | InkRenew 图 5 用真实破损形状模拟古画缺损，展示工笔、水墨等四种风格。研究另用 LoRA、自动指标与专家评估。 | 研究中借用真实破损轮廓已有先例。按同画材、同基底以同图、同面积、同位置对照形状来源，仍是可检验的问题。[书目与图注核查](#inkrenew-书目与图注核查) |
| 薛文喆、董兴宇、胡琦瑶、曹瑞、彭先霖，《基于孪生级联空间滤波的中国传统画修复》，《西北大学学报（自然科学版）》55(1), 150–167，2025 | 正文 §2.1、图 2 从残缺画作提取掩码并与完好作品拼接。第 156 页图 4 展示从真实破损实例构造的掩码。 | 独立支持真实破损掩码移植已有先例。文中在训练和测试中混用真实样例掩码与自由孔洞掩码。[期刊页面](https://xdxbzk.nwu.edu.cn/zh/article/doi/10.16152/j.cnki.xdxbzr.2025-01-013/) · [出版社 PDF，图 4](https://xdxbzk.nwu.edu.cn/rc-pub/front/front-article/download/82025628/lowqualitypdf/%E5%9F%BA%E4%BA%8E%E5%AD%AA%E7%94%9F%E7%BA%A7%E8%81%94%E7%A9%BA%E9%97%B4%E6%BB%A4%E6%B3%A2%E7%9A%84%E4%B8%AD%E5%9B%BD%E4%BC%A0%E7%BB%9F%E7%94%BB%E4%BF%AE%E5%A4%8D.pdf#page=7) |
| Ren、Huang，*MAPGR*，npj Heritage Science，2026 | 壁画补全以缓解语义幻觉为核心，报告 PSNR、SSIM、FID 和 LPIPS，并指出需要标准化的图像学幻觉定量方法。 | 画作修复中已经明确提出语义幻觉问题。通用指标与原创内容偏离的对应关系仍需用受控样本验证。[期刊全文](https://www.nature.com/articles/s40494-026-02607-3) |
| Wang 等，*Towards Enhanced Image Inpainting: Mitigating Unwanted Object Insertion and Preserving Color Consistency*，CVPR 2025 | 用 CLIP@mask 比较补全区域与原图的语义特征，也用 Gradient@edge 看颜色接缝。MISATO 为自然图像上的多域补全基准。 | CLIP@mask 是直接可复用的补全先例，需检验其对画作局部内容变动的敏感性。[会议全文](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_Towards_Enhanced_Image_Inpainting_Mitigating_Unwanted_Object_Insertion_and_Preserving_CVPR_2025_paper.pdf) |
| Kim、Tregidgo、Jin、Figini、Alexander，*HalluGen: Synthesizing Realistic and Controllable Hallucinations for Evaluating Image Restoration*，CVPR 2026 | 用受控幻觉样本验证 SHAFE，重点测试稀疏局部的语义改变。主实验为 MRI，并跨任务验证。 | 可借鉴正负对照和局部聚合。画作上是否有效仍需验证。[会议全文](https://openaccess.thecvf.com/content/CVPR2026/papers/Kim_HalluGen_Synthesizing_Realistic_and_Controllable_Hallucinations_for_Evaluating_Image_Restoration_CVPR_2026_paper.pdf) |
| Rocafort、Su、Gomez-Villa、Vazquez-Corral，*Evaluating and Preserving High-level Fidelity in Super-Resolution*，2025 年 arXiv 预印本 | 用 723 对自然图像超分结果和真值，结合独立用户判断验证语义改变代理指标。 | 可作高层保真指标的邻域证据。本文只使用基于原图和已知扰动的自动验证，不需招募评分人。[作者全文 §§3–4](https://arxiv.org/html/2512.07037v2) |

## InkRenew 书目与图注核查

- **书目。** 正确 DOI 为 `10.1057/s41599-026-07117-y`。Crossref 核实为 Humanities and Social Sciences Communications 第 13 卷第 1 期、文章号 1342，2026 年 4 月 22 日在线发表。[Crossref 记录](https://api.crossref.org/works/10.1057/s41599-026-07117-y) · [出版社全文](https://www.nature.com/articles/s41599-026-07117-y?error=cookies_not_supported)
- **单位。** 出版社作者信息列 Ying Zhang、Kewen Zhu、Zejian Li、Zhongni Liu、Kaixin Jia 和 Jiesi Zhang 为浙江大学（宁波），Lingyun Sun 为浙江大学（杭州）。[出版社作者信息](https://www.nature.com/articles/s41599-026-07117-y?error=cookies_not_supported#author-information) · [浙江大学介绍](https://ai.zju.edu.cn/2026/0528/c90228a3167491/page.htm)
- **证据边界。** 正式版 “System implementation” 小节的**图 5**图注给出下面的原句。它支持用真实破损掩码模拟古画缺损。逐个定量样本的掩码来源、供体和目标是否材料匹配、供体许可均需独立证据。[出版社图 5](https://www.nature.com/articles/s41599-026-07117-y/figures/5?error=cookies_not_supported) · [出版社预出版 PDF](https://www.nature.com/articles/s41599-026-07117-y_reference.pdf)

  > The damage masks used in our study are borrowed from real damage in existing paintings rather than synthetic masks.

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

- **统计口径。** 固定在 Hugging Face 修订版 `eabf09542f871c6c61147474408704152e08f831`，通过 HTTP Range 逐个读取 28 个 Parquet 分片的 `id`、`type`、`material` 列。共 418 行、418 个唯一 ID，其中 `type == "Painting"` 有 49 行，基底为画布（Canvas）23、木板（Wood）26。另有湿壁画（Fresco）25、石版画（Lithograph）4，单独计数。基底标签无法推断颜料、画种或某类破损的可用掩码数。本次统计未下载图像或掩码。论文补充材料 §1 提到有来源归属记录，当前公开分片未提供对应逐图出处字段。[固定版本的数据目录](https://huggingface.co/datasets/danielaivanova/damaged-media/tree/eabf09542f871c6c61147474408704152e08f831/data) · [会议补充材料 §1](https://openaccess.thecvf.com/content/WACV2025/supplemental/Ivanova_ARTeFACT_Benchmarking_Segmentation_WACV_2025_supplemental.pdf)
- **不同许可对象。** 会议论文 §3 描述底图从采用 CC 许可的来源收集，未列出逐图条款。作者发布的 Hugging Face 数据卡标为 AFL-3.0，arXiv 所列 CC BY-NC-SA 4.0 是该预印本的许可标记。三者需分别追溯。[会议全文](https://openaccess.thecvf.com/content/WACV2025/papers/Ivanova_ARTeFACT_Benchmarking_Segmentation_Models_on_Diverse_Analogue_Media_Damage_WACV_2025_paper.pdf) · [数据卡](https://huggingface.co/datasets/danielaivanova/damaged-media/blob/eabf09542f871c6c61147474408704152e08f831/README.md) · [arXiv 全文页](https://arxiv.org/html/2412.04580v1)
- **移植与公开。** AFL-3.0 第 1、6、9 条允许在许可范围内创建和发布衍生作品，并规定保留署名和许可通知、标明修改、采取合理步骤取得收件人对条款的同意。数据卡未给出逐图溯源或单独的掩码授权说明。应在公开实验包前确认哪些标注可适用该许可、底图权利是否影响对应掩码，以及怎样履行条款。在此之前，公开的试验方案可以使用程序生成且许可清楚的掩码。[AFL-3.0 正文](https://opensource.org/license/afl-3-0-php)
- **先导供体门槛。** 对同一发布版的 49 条 Painting 记录逐一解码单通道标注 TIFF，按数据卡标签统计含至少一个 `Material loss`（值 1）像素的唯一发布 ID。画布 23 条中有 5 条，木质基底 26 条中有 1 条。另有 `Peel`（值 2）分别 20 条和 25 条，按类别独立计数。六条含局部材料缺失的记录即使全部通过油画技法和许可复核，仍不足以达到两组各 15 个独立供体的要求。数据卡的文字描述不能替代像素标签，六条的文字均用了 tears。先执行统一程序掩码下的分层比较。[数据卡标签](https://huggingface.co/datasets/danielaivanova/damaged-media) · [先导协议](../docs/INNOVATION.md#退路)

### 2026-11-20 补查逐图出处与许可

- 会议补充材料 §1 列出 17 家机构和几个网络集合，称文本标注表带有来源归属。正文将另两类来源写为 WikiArt 和 Flickr，补充材料写为 Wikimedia 和 Flickr。补充材料概述为公共领域，同时列出 CC0、CC BY 和 CC BY-NC 三类采集条款。原 PDF 有 21 页，链接指向机构主页或网络集合，文件内无逐图出处表和嵌入附件。按逐图具体条款核实，需要把记录 ID 与原图或对象页匹配。[会议正文 §3](https://openaccess.thecvf.com/content/WACV2025/papers/Ivanova_ARTeFACT_Benchmarking_Segmentation_Models_on_Diverse_Analogue_Media_Damage_WACV_2025_paper.pdf) · [会议补充材料 §1](https://openaccess.thecvf.com/content/WACV2025/supplemental/Ivanova_ARTeFACT_Benchmarking_Segmentation_WACV_2025_supplemental.pdf)
- 作者项目站转向 Hugging Face。项目站的初始提交是建站模板，现有作者演示仓也未附来源表。发布目录只有数据卡、Git 属性文件和 Parquet 分片。数据卡示例生成的 `metadata.csv` 以 ID 命名下载后新保存的本地图像与掩码，路径不包含原摄制来源。[作者项目站](https://daniela997.github.io/ARTeFACT/) · [初始站点代码](https://github.com/daniela997/ARTeFACT/blob/240abb7646ccfb7c495ed9767e82a491f554994c/index.html) · [作者演示代码](https://huggingface.co/spaces/danielaivanova/artefact-damage-demo/blob/main/app.py) · [固定发布目录](https://huggingface.co/datasets/danielaivanova/damaged-media/tree/eabf09542f871c6c61147474408704152e08f831) · [固定数据卡](https://huggingface.co/datasets/danielaivanova/damaged-media/blob/eabf09542f871c6c61147474408704152e08f831/README.md)
- 通过 HTTP Range 对照两个发布版。旧版 `e052de6` 的 8 个 Parquet 分片和固定版 `eabf095` 的 28 个分片各有 418 个不同记录 ID，三个媒体列 `image`、`annotation`、`annotation_rgb` 的 `path` 叶字段全部为空。固定版新增的分类与描述未提供来源 URL，49 条 Painting 的三类描述均无链接。两次读取只使用 schema 和元数据列。固定版还把 23 条 Fresco 标为 Lime plaster、2 条标为 Paper，4 条 Lithograph 标为 Paper，均按发布标签计数。[旧版文件树](https://huggingface.co/datasets/danielaivanova/damaged-media/tree/e052de60659a33fcf4ee49dba417051cbd8ccedd) · [固定版文件树](https://huggingface.co/datasets/danielaivanova/damaged-media/tree/eabf09542f871c6c61147474408704152e08f831)
- Daniela Ivanova 的 2025 年博士论文将 ARTeFACT 数据集链接指向同一个项目站。第 4 章的作者贡献说明写明，她收集底图并手工标注，标注另经核查。§4.9.1 再次提到带来源的表格，链接仍指向机构或集合，并无发布 ID 与具体来源的对照。[博士论文数据集清单](https://theses.gla.ac.uk/85461/2/2025ivanovaphd%20%282%29.pdf#page=19) · [第 4 章贡献说明](https://theses.gla.ac.uk/85461/2/2025ivanovaphd%20%282%29.pdf#page=86) · [§4.9.1](https://theses.gla.ac.uk/85461/2/2025ivanovaphd%20%282%29.pdf#page=103)
- 数据卡的 AFL-3.0 公告适用于发布方有权许可的内容。补充材料中单列的底图条款仍需按记录核对。将标注转成二值形状、重新缩放并公开掩码或衍生图，都需要确认标注许可的覆盖范围和署名要求。当前可报的是按发布 ID、基底标签与像素类别计的候选上限。油画技法、同一馆藏对象是否有多条记录、掩码改编与分发授权尚无逐件核验结果。[固定数据卡](https://huggingface.co/datasets/danielaivanova/damaged-media/blob/eabf09542f871c6c61147474408704152e08f831/README.md) · [AFL-3.0 第 1、6、7、9 条](https://opensource.org/license/afl-3.0)

继续这一数据分支需要作者提供发布 ID 与馆藏对象页、原图来源及许可的映射，并确认标注可否转为形状、移植和重新分发。获得映射后再对候选复查颜料和基底。同一对象的多张拍摄图共享供体计数。

## 指标和修复伦理

- 将掩码内 MAE、色差和边缘连续性等作为局部原图差异。LPIPS、DISTS 和掩码内 CLIP/DINO 相似度都是有参考的指标，可分别描述感知、纹理、结构或语义的近似。DISTS 对同类纹理重采样的容忍度是其测量性质，用它单独命名「自然度」会把两类问题混在一起。感知—失真权衡刻画输出分布与真值失真的关系，结论不应外推成单幅画的两个分数必然此消彼长。
  [DISTS 原文](https://arxiv.org/abs/2004.07728) · [感知—失真权衡，CVPR 2018](https://openaccess.thecvf.com/content_cvpr_2018/html/Blau_The_Perception-Distortion_Tradeoff_CVPR_2018_paper.html)
- 先用原图构造已知类型的对照，例如局部色偏、笔触纹理扰动、结构或图案替换。报告各指标对目标改变和非目标改变的敏感性。生成种子之间的分歧提供稳定性证据，语义偏离则需要与原图比较。
- ICOM-CC 2008 术语决议以尊重原始材料为基础，并举补色为修复的例子。AIC 实务指南第 23 条要求记录补失、可以通过常见检查方法辨识，且处理可逆。数字流程可据此保留原图、输出、掩码和参数，报告未损区改动。此处借鉴保护专业原则，真实画作的处理决定由修复人员作出。
  [ICOM-CC 决议](https://www.icom-cc.org/en/terminology-for-conservation) · [AIC 实务指南](https://community.culturalheritage.org/conservation-at-work/uphold-professional-standards/code)

## 后续判据

先按[先导协议](../docs/INNOVATION.md#预先固定的判定规则)估计同画材、同基底的配对来源效应，及统一程序掩码下的分层模型差。达到预设阈值的结果用独立画作及掩码组复核。效应小或不确定时，报告区间及样本局限。
