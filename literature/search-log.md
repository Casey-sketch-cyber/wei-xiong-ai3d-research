# 检索记录

记录每一次检索：日期、工具、查询词、主要结果。新的检索追加在表格末尾，不要删改旧行。

工具说明：2026-11-18 这一轮用网页搜索和逐页打开论文页完成。arXiv 批量接口（robots 禁止）和 OpenAlex 接口（请求失败）在当时的环境里不可用，所以没有做被引列表排查，这是"未见"结论只是初步的主要原因。

| 日期 | 工具 | 查询词 | 主要结果 | 用于 |
| --- | --- | --- | --- | --- |
| 2026-11-18 | 网页搜索 | benchmark diffusion inpainting digital restoration of damaged paintings synthetic cracks paint loss evaluation 2025 | ARTeFACT；合成龟裂（arXiv 2602.12742）；湿壁画扩散修复（DH 2025）；壁画修复（ICCV 2023）；胶片损伤模拟（arXiv 2302.10004，未打开） | 脉络二 |
| 2026-11-18 | 网页搜索 | survey image inpainting diffusion models 2024 2025 arXiv | 补全综述 arXiv 2401.03395；低层视觉扩散综述 arXiv 2406.11138（均未打开） | 脉络一 |
| 2026-11-18 | 网页搜索 | Bertalmio Sapiro Caselles Ballester 2000 "Image inpainting" SIGGRAPH | SIGGRAPH 历史档案页 | 脉络一 |
| 2026-11-18 | 网页搜索 | Kachkine 2025 Nature physical restoration of a painting with a digitally constructed mask | Nature 642 论文书目页、MIT 新闻 | 脉络二、三 |
| 2026-11-18 | 网页搜索 | Ghent Altarpiece crack detection digital inpainting Cornelis Pizurica virtual restoration | Cornelis 等 2013 全文 PDF | 脉络二 |
| 2026-11-18 | 网页搜索 | Dunhuang mural restoration dataset deep learning inpainting challenge | 敦煌基准（arXiv 1907.04589）；Scientific Data 2024 数据集；ARIN（arXiv 2402.16188，未打开） | 脉络二 |
| 2026-11-18 | 网页搜索 | Chinese painting restoration deep learning inpainting silk paper damage dataset 2024 2025 | Applied Sciences 2024 丝绸纹样；Heritage Science 2024 ConvSRGAN；Electronics 2025（未打开） | 脉络二 |
| 2026-11-18 | 网页搜索 | Venice Charter Article 9 ... Article 12 ... | 维基百科威尼斯宪章条文摘录 | 脉络三 |
| 2026-11-18 | 网页搜索 | hallucination generative image restoration diffusion faithfulness fidelity evaluation 2025 arXiv | 生成式超分高层保真（arXiv 2512.07037）；其他几篇未打开 | 脉络三 |
| 2026-11-18 | 网页搜索（扩展） | evaluating pretrained inpainting models on artworks paintings comparison LaMa Stable Diffusion inpainting fidelity benchmark | RefPaint；I Dream My Painting；未见跨画种系统评测 | 新颖性核查 |
| 2026-11-18 | 网页搜索 | virtual restoration of paintings ethics authenticity digital inpainting conservation principles AI generated infill | Kachkine 2025；匈牙利语文章《人工智能在文物重建中的可能与局限》（未打开） | 脉络三 |
| 2026-11-18 | 网页搜索 | ARTeFACT analogue media damage restoration follow-up Ivanova 2025 diffusion restoration benchmark | ARTeFACT 为 WACV 2025；作者博士论文（格拉斯哥，未打开）；未见后续修复评测 | 新颖性核查 |
| 2026-11-18 | 网页搜索（扩展） | comparative evaluation deep learning inpainting methods damaged paintings artworks Heritage journal J. Imaging 2024 2025 | Heritage Science 多篇壁画与古画方法论文；Frontiers 2024 带风格约束的 DIP；均为单方法 | 脉络二、新颖性核查 |
| 2026-11-18 | 网页搜索 | Metropolitan Museum Open Access CC0 images API number of public domain images | 大都会博物馆 2017 年开放获取公告 | 数据来源 |
| 2026-11-18 | 网页搜索 | Johnson ... 2008 "Image processing for artist identification" IEEE Signal Processing Magazine | 卡内基梅隆书目页 | 脉络二 |
| 2026-11-18 | 打开模型页 | Hugging Face：FLUX.1-Fill-dev；stable-diffusion-xl-1.0-inpainting-0.1；danielaivanova/damaged-media | 参数量、许可、训练方式；ARTeFACT 许可显示 afl-3.0 | 脉络一、数据来源 |
| 2026-11-18 | OpenAlex 前向引用，游标分页 | `filter=cites:<Work ID>&per-page=100`，LaMa 正式 W3199003182、预印本 W4286974649 | 返回并处理 1,748 和 223 条。按标题和可用摘要筛选 painting、artwork、mural、fresco、heritage、hallucination、fidelity 等。两入口可能交叠。命中埃舍尔版画比较和中国山水补全等。 | v1 核查 |
| 2026-11-18 | OpenAlex 前向引用 | `filter=cites:<Work ID>&per-page=100`，ARTeFACT W4409262025、Shao W4390874389、Kachkine W4411205243、Rocafort W7111225829 | 返回并处理 7、22、13、0 条。Shao 命中敦煌跨洞窟风格修复；Kachkine 命中 InkRenew、MAPGR 和 Imagest。ARTeFACT 结果多为损伤检测和邻域研究。 | v1 核查 |
| 2026-11-18 | Semantic Scholar 前向引用 | `/graph/v1/paper/<DOI 或 ARXIV:id>/citations`，Shao DOI 10.1109/ICCV51070.2023.01853、Kachkine DOI 10.1038/s41586-025-09045-4、Rocafort ARXIV:2512.07037 | 分别返回 20、12、0 条。与 OpenAlex 条目数存在差异。 | v1 核查 |
| 2026-11-18 | 网页搜索并打开原文 | painting restoration cross-media comparative benchmark LaMa SDXL FLUX painting inpainting oil watercolor ink print damage fidelity paintings 2026 | 核对 Controlled-300 的画作视觉类别和掩码对照、MDTD-ArtIR 的盲修复与不透明度分层。 | 跨媒介与模型比较 |
| 2026-11-18 | 学术网页搜索并打开原文 | artwork restoration digital painting inpainting hallucination semantic faithfulness fidelity benchmark；ASUKA CVPR 2025；HalluGen CVPR 2026 | 核对 ASUKA 的 CLIP@mask 与 Gradient@edge、HalluGen 的 SHAFE 及主验证域、Rocafort 的配对验证。 | 幻觉与忠实度 |
| 2026-11-18 | 正式论文库及 arXiv | 对 `papers.csv` 的 19 条 arXiv 逐条核对标题和发表信息；搜索正式论文集、期刊卷期和 DOI | 16 条找到正式记录，3 条仅确认预印本。正式链接与核对范围已写入文献表。 | 书目核对 |
| 2026-11-18 | 作者数据卡、会议正文、OSI、Parquet 元数据读取 | ARTeFACT WACV 2025、AFL-3.0，HF 修订版 `eabf09542f871c6c61147474408704152e08f831` 的 28 个分片 | 读取 `id/type/material`，418 个唯一 ID；Painting 49、Fresco 25、Lithograph 4。数据卡许可与论文中的底图许可表述适用于不同对象，逐图/掩码权利尚待核对。 | 破损样本与许可 |
| 2026-11-18 | 发布机构原文 | ICOM-CC 2008 terminology for conservation；AIC Guidelines for Practice compensation for loss | 核对绘画补色、尊重原材料及记录、可辨识和可逆的实务要求。 | 修复伦理 |
| 2026-11-18 | Crossref、出版社及作者单位 | `10.1057/s41599-026-07117-y`，InkRenew System implementation、图 5、Authors and Affiliations | 核实正式卷 13 第 1 期、文章号 1342、浙江大学宁波与杭州单位。出版社图 5 明确说明使用现存画作真实破损掩码。 | PR #3 审查 1 |
| 2026-11-18 | 西北大学学报官网、PDF | `10.16152/j.cnki.xdxbzr.2025-01-013`，第 153 页图 2、第 156 页图 4 | 核实从真实残缺画作提取掩码并与完好绘画拼接，训练和测试与自由孔洞掩码混用。 | PR #3 审查 1 |
| 2026-11-18 | Zenodo、作者仓库和出版社 | Controlled-300 §3 与冻结快照 cases.csv，Imagest 修复小节与表 2 | 对照样本表 525 条、35 幅画，同幅同家族五变体面积一致。Imagest 汇总新方法与四个基线。 | PR #3 审查 4–6 |
| 2026-11-18 | ARTeFACT 发布历史、作者站与像素标注 | 固定 HF 修订版 `eabf09542f871c6c61147474408704152e08f831`，筛出 Painting 49 个 ID 并逐一解码单通道 TIFF | Canvas 23 件中 5 件、Wood 26 件中 1 件包含 Material loss（1）。Peel（2）分别 20 件、25 件。标注与底图路径字段为空，未定位到补充材料提到的逐件出处表。 | 真实掩码先导门槛 |
| 2026-11-20 | 网页检索、正式会议全文及作者原文 | `latent diffusion inpainting thin mask cracks mask downsampling`，`BrushNet PowerPaint mask information loss` | **明确先例**。Shamsolmoali 等，*TD-Paint: Faster Diffusion Inpainting Through Time-Aware Pixel Conditioning*，ICLR 2025，§4.3 在隔像素超分和交替线掩码中指出潜空间模型的掩码下采样可丢失关键条件信息。Ju 等，*BrushNet*，ECCV 2024，§3.2 与图 3 明确显示 512² 的二值掩码缩到 64²，与受损图 VAE 编码配合。两者提供机制背景。 [TD-Paint 会议全文](https://proceedings.iclr.cc/paper_files/paper/2025/file/fe489a28a54583ee802b8e2955c024c2-Paper-Conference.pdf) · [作者 HTML §4.3](https://arxiv.org/html/2410.09306#S4.SS3) · [BrushNet 会议全文](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/03014.pdf) | 潜空间掩码的已有认识 |
| 2026-11-20 | Diffusers 文档、问题记录和固定版本源码 | `diffusers inpaint mask downsample nearest padding_mask_crop`，`PowerPaint-v1 prepare_mask_latents interpolate` | Diffusers SDXL v0.35.2 与 PowerPaint v1 的 `prepare_mask_latents` 都缩放二值掩码。对固定 512 输入，在所测管线中回放为步长 8 的最邻近采样。Diffusers 文档另提供裁剪后放大局部掩码及图像的 `padding_mask_crop`。PowerPaint 论文的主要比较包含不同形状的常规补全和任务提示。论文结果应区分这些设置、几何覆盖图以及最终生成误差。 [SDXL 固定源码](https://github.com/huggingface/diffusers/blob/v0.35.2/src/diffusers/pipelines/stable_diffusion_xl/pipeline_stable_diffusion_xl_inpaint.py#L775-L794) · [PowerPaint 固定源码](https://github.com/open-mmlab/PowerPaint/blob/5b4c3d52291709fcec2a1870d987da693fd3549c/powerpaint/pipelines/pipeline_PowerPaint.py#L603-L622) · [Diffusers 文档](https://huggingface.co/docs/diffusers/en/using-diffusers/inpaint#padding-mask-crop) · [PowerPaint 会议全文](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/07554.pdf) | 固定管线比对 |
| 2026-11-20 | 源码、开发者问题记录及软件文档 | `SDXL inpaint black white fill strength gray original image influence`，`masked content fill original latent noise` | **明确先例**。Diffusers #8450（2024）中的用户与维护者讨论了低于 1.0 的 strength 下，把待补区域预先换成灰色或白色，以减轻原输入颜色的影响。AUTOMATIC1111 文档列有多种可选洞内初始化。固定 SDXL 实现公开了两条路径：低于 1.0 时整张受损图进入 VAE 后加噪，1.0 的主初始化用纯噪声，独立的掩码图像条件仍保留。SDEdit 论文已讨论由输入加噪起步时的保真与生成之间的关系。 [Diffusers #8450](https://github.com/huggingface/diffusers/issues/8450) · [固定 SDXL 初始化](https://github.com/huggingface/diffusers/blob/v0.35.2/src/diffusers/pipelines/stable_diffusion_xl/pipeline_stable_diffusion_xl_inpaint.py#L715-L754) · [Masked content 文档](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Features/515fb1318019e0121b8dcfa47ee996369fcb9f75#masked-content) · [Meng 等，ICLR 2022 作者稿](https://arxiv.org/abs/2108.01073) | 预填充及颜色效应 |
| 2026-11-20 | 出版社正文及既有画作基准 | `small sample diffusion inpainting archaeology spatial compliance`，`painting inpainting controlled damage fidelity benchmarks` | 文物邻域研究已经用遮挡模拟和参考图评估补全。2026 年 *Discover Artificial Intelligence* 的考古陶器研究用 LaMa、SD Inpainting 与 ControlNet 比较空间干预并报告掩码内外指标。画作侧的 Imagest、Controlled-300 也已有基线或遮挡几何对照。适合把本项目定位在绘画媒介分层、固定协议的配对诊断及独立馆藏复现。 [陶器研究](https://doi.org/10.1007/s44163-026-01767-2) · [Imagest 正文](https://www.nature.com/articles/s40494-025-02167-y?error=cookies_not_supported) · [Controlled-300 研究档案](https://zenodo.org/records/23092185) | 贡献定位 |

### 给 Gemini 的机制表述

- **漏覆盖可保留为实证结果。** 引用 `[@shamsolmoali2025tdpaint]` 说明细结构下采样的先例，引用 `[@ju2024]` 和固定实现说明条件掩码如何构造。项目提供的增量是逐形状和面积量化画作程序破损的原洞漏覆盖，并在冻结样本上比较修正前后。覆盖图描述二值掩码所指定的网格。误差比较衡量输入协议整体，扩张同时减少洞周可见上下文。 [旧覆盖与配对结果](../docs/LATENT_ALIGNMENT.md)
- **预填色可保留为单变量实证结果。** 引用 `[@diffusers8450]` 说明开发者记录，使用 `[@diffuserssdxl0352]` 准确说明整图初始化与独立的掩码图像条件。项目增量是固定 0.99 等参数，仅改黑色、灰色和洞外环带均色，量化配对亮度偏移、MAE 和 LPIPS。已遮挡的真值像素没有进入环带均值。建议英文用 *prefill influence* 或 *sensitivity to the initial fill*，以免把颜色效应写成数据泄漏。60 幅的扩展对比同时改变多个参数，单列报告。 [单变量对照](../docs/SDXL_PREFILL.md) · [60 幅参数组合对照](../docs/NATIVE_REVIEW.md#sdxl-环带均色缩小差距)
- **三项协议属于评测贡献。** 宜写 *we quantify how these choices affect painting inpainting benchmarks*；几何、颜色和可用率有各自的证据和分母。文献检索确认上述先例，首次发现或所有管线都受同样影响的说法超出本次证据。 [写作任务书](../docs/paper/WRITING_BRIEF.md)
