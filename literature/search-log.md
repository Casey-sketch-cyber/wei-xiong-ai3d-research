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
