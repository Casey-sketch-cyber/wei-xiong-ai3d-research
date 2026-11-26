# 项目进度（交接记录）

> 每个 AI 结束工作前在"工作记录"最上方追加一条，新的在上面。

## 当前状态

*PeerJ Computer Science* 稿件结构与分段摘要已审。三位作者署名及学校级单位已确认。MIT 复现代码已注册版本 DOI，正文已写入归档链接并重编。八个机器可读评审补件已备。已按作者确认写入无基金、无利益冲突、三人贡献和 GPT-6 致谢。投稿前仍待确认译文核对责任、历史 AI 版本及署名要求，并上传评审附件。真实破损实验仍待供体出处映射和掩码授权。[投稿交接](paper/SUBMISSION_PEERJ_CS.md) · [LaTeX 复现说明](paper/peerj-cs/README.md)

## 待办

- [ ] **Gemini · 写作讨论**：先在 [写作讨论](paper/WRITING_DISCUSSION.md) 回答五个问题（诊断、§4.3 改写示范、森林图、skill 规则、评测论文写法），分支 `gemini/writing-discussion`；Claude 汇总后更新论文写作 skill

- [ ] **Gemini · 正文减数字（可读性）**（在写作讨论之后）：作者反映数字太密。Results 各节每 100 词有 17–35 个数字，§4.3 有 24 个置信区间。按 [可读性任务书](paper/READABILITY_PASS.md) 改 `peerj-cs/manuscript.tex`：每个结论最多一个核心数字，其余指向表格，不改值、不改结论；分支 `gemini/peerj-readability`

- [ ] **Codex · 核对减数字修订**：列出删掉的每个数字及其在表格或补件中的出处，核对保留值，重算密度，重编投稿包

- [x] **Codex · 图 1(a)、图 2 换明亮示例**（2026-11-25）：服务器重跑 `build.sh` 后已验收 PowerPoint 和 PDF。1(a) 新例 `watercolor_paper_02_crack_01` 漏覆盖 57.8%，已在 PR #36 告知 Gemini。[素材与清单](paper/FIGURES.md)

- [x] **Codex · 重跑图 1、图 2**（2026-11-23）：在服务器按最新布局执行 `build.sh`，更新可编辑 PPTX 与预览。图 1(b) 选中 `watercolor_paper_02_loss_05`，三臂共用 251 × 251 px 窗口，FigGenie 两图均为 0 错误。[复现与校验清单](paper/FIGURES.md)

- [x] **Codex · 图 1、图 2 PowerPoint 布局草图**：交付可编辑的 teaser 和方法流程图，按最终双栏宽度检查 PDF 并附 PNG 预览。五篇论文的六张参考缩略图位于服务器数据盘的 `paper/figure-refs/`。[布局与数字来源](paper/FIGURES.md)
- [x] ~~Codex · 图 1、图 2 精修~~：改由 Claude 用 FigGenie 重画（作者决定），见 [FIGURES.md](paper/FIGURES.md)
- [x] **Gemini · 图 1、图 2 图注**：已按 `docs/paper/figures/src/fig1/spec.json`、`fig2/spec.json` 的 `caption_draft` 改写 `draft-v3.md` 中的图 1–2 图注，保留全部数字与分母（v3 第二轮已完成）
- [x] **Codex · 图 1、图 2 换真实图片**：已用冻结例图与核验后的输出完成 FigGenie 构建，两图 lint 均为 0 错误。PPTX 和预览入库，PDF 和 300 dpi PNG 留在服务器数据盘。[素材、清单和复现](paper/FIGURES.md)
- [x] **Claude · 图 1、图 2 最后检查**：PR #30 真实素材已审；图 2 标记移到右下角（PR #31）
- [x] **Codex · 正式版 PDF 字距**：确认 Arimo 已嵌入。通过 SVG 精确定位修正 Chromium 整数像素推进，从最新主线重建图 1 和图 2。[正式版及校验清单](paper/FIGURES.md)
- [x] **Codex · 复核 v3 第二轮**：指定数字、八个共同样本均值与 52 个引用键已核对。请 Gemini 收紧三处表述。[PR #23 复核](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/23#issuecomment-7129658292)
- [x] **Codex · 图 3–6 套用统一样式**：数据盘已生成四张图的 PDF、300 dpi PNG 与清单。图 5 使用四模型同案的绝对 MAE 均值与作品级 bootstrap 95% 区间。[生成说明](paper/FIGURES.md)
- [x] **Codex · v3 首轮数字及引文核查**：表 1–7 与源报告一致，51 个引用键全部解析。已登记待修订项。[PR #23 核查意见](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/23#issuecomment-7063082708)
- [x] 用 LaMa、ARTeFACT、Shao 2023、Kachkine 2025、Rocafort 2025 的前向引用及独立关键词检索核查文献树 v1，见 [核查记录](../literature/audit-of-claude-v1.md)
- [x] 核对文献表中 19 条 arXiv 记录，16 条找到正式发表处，另外 3 条仅确认预印本
- [x] 核对 ARTeFACT 数据卡许可和样本元数据。418 条记录中 49 条标为 Painting
- [x] 核查 ARTeFACT 补充材料及两个公开发布的逐图出处字段。两个版本的图像和标注路径均为空，整理了底图条款与标注授权的边界。[补查记录](../literature/audit-of-claude-v1.md#2026-11-20-补查逐图出处与许可)
- [ ] 从 ARTeFACT 作者取得发布 ID 与藏品、图像来源及条款的映射，并确认掩码改编与分发范围，再核对供体的技法和独立性
- [x] 按四个组别核查克利夫兰及五家外部馆藏的开放画作供给，分别记录目录命中、逐件许可和尺寸筛查。[馆藏计数](CC0_AVAILABILITY.md)
- [x] 找到 ICOM-CC 术语决议和 AIC 补失指南，已写入 [核查记录](../literature/audit-of-claude-v1.md#指标和修复伦理)
- [x] 在 3090 实测先导模型 LaMa 和 SDXL Inpainting 的显存与耗时
- [x] 在 3090 实测追加的 MAT 和 PowerPaint v1，记录显存和覆盖率
- [x] 用 findInnovation 模板起草 [创新点评估](INNOVATION.md)
- [x] 审查 1 已核实 InkRenew 的正确 DOI、卷期和文章号、作者单位及图 5，并补充薛文喆等的独立证据
- [x] 审查 2 已选择形状来源真实性，真实掩码与目标画作逐件匹配技法和基底，并明确纸本与绢本的条件
- [x] 审查 3 已写明掩码内 MAE 差中差、局部 LPIPS、按画作 bootstrap、排序判定、实用阈值和退路
- [x] 审查 4 已注明 Controlled-300 在 35 幅上的固定家族和像素面积对照，并明确档案性质及项目区别
- [x] 审查 5 已将画材和基底分层列为并列主问题，先用画布与木板油画比较基底分组
- [x] 审查 6 已用 Imagest 表 2 核实，100 幅名画用于新模型对四个基线的总体比较
- [x] Claude 复审 PR #3，2026-11-19 已合并
- [x] 用统一程序掩码完成画布油画、木质基底油画、纸本水彩、纸本水墨四组对照，各 15 幅 CC0 作品（PR #3 复审建议）
- [x] 检查 ARTeFACT 真实掩码先导门槛。含目标类别的候选最多 5 件和 1 件，改跑程序掩码分层（PR #3 复审建议）
- [x] 根据程序掩码先导的作品级配对差方差估算三组计划对照在 0.01 MAE 目标差下的样本量（PR #3 复审建议）
- [x] Claude 复审 PR #5，2026-11-19 已合并
- [x] 修正初版结论口径：在已测的两模型和 512 配置下，四个画材组的选择均为 LaMa。组间差的检出样本量另行解读（PR #5 复审）
- [x] 对同一批 60 幅补跑 SDXL 1024 和 512 空提示词，每项采用同一预定种子，与初版同种子对照（PR #5 复审）
- [x] 在原结果和追加输出计算 CIEDE2000、平均 Lab 色偏、局部 DISTS，记录语义归因的证据边界（PR #5 复审）
- [x] 推理前固定原像素取样、随机位置和裂缝／剥落／广片缺失的 1% 与 5% 档。四组各四幅，15 幅全尺寸源文件和 1 幅馆方备选图（PR #5 复审）
- [x] 原尺度增加 MAT 和 PowerPaint v1。MAT 96/96，PowerPaint 88/96，自带安全检查拦截 8 个条件。FLUX.1 Fill 完成静态全常驻显存与访问预检（PR #5 复审）
- [x] 按 PR #7 审查用旧输出诊断掩码漏覆盖，记录分区 MAE 和亮度。1% 细破损漏覆盖过半，亮度结果未支持黑预填是高误差主因
- [x] 在修正推理前单独提交网格对齐和共享输入方案。原裁片、原计分掩码、种子和模型配置沿用冻结计划
- [x] 完成初版 SDXL 240 次、两项 SDXL 敏感性 120 次、原尺度扩散条件 192 次和像素模型共享输入 312 次。重算两种 CIEDE2000 和局部 DISTS，保留旧结果为补充
- [x] 核验 853 份输出和 11 个拦截记录，确认评分掩码外像素与原图一致，修正旧报告的 SHA-256 誊写错误
- [x] Claude 复审 PR #7，2026-11-19 已合并。潜空间漏覆盖属实（细裂缝和小剥落最多漏 56%），修正后 PowerPaint 明显改善，SDXL 仍远差于 LaMa；四组模型选择不变
- [x] 在 `a7bf504` 固定模型卡参数敏感性方案。对 60 幅中心掩码和 16 幅原尺度作品重跑 SDXL，含同种子的 512 与 1024 对照。核验全部 216 个输出、五项指标和亮度偏移
- [x] 核对 PowerPaint、MAT 作者设置与本项目适配差异，在决策记录说明保留历史结果作对照的原因
- [x] Claude 复审模型卡参数敏感性报告和作品级配对（PR #9 已合并）
- [x] 在 `d5ca4d5` 先固定预填充方案。固定 512 和同一种子，完成中灰与环带均色的 312 次推理，与黑色历史结果比较 MAE、局部 LPIPS 和亮度（PR #9 复审）
- [x] 依据三种填色对照，正文 SDXL 保留 strength 1.0，0.99 分颜色作为敏感性并在决策记录说明（PR #9 复审）
- [x] 在模型卡报告中补充黑色进入整图 VAE 初始化的机制、t=901 的归一化系数和固定版源码（PR #9 复审）
- [x] 在运行记录与汇总 JSON 写入实际 UTC 起止和冻结方案时间（PR #9 复审）
- [x] Claude 复审填色结果和正文设置（PR #11 已合并）。SDXL 参数敏感性到此收尾，不再追加 SDXL 设置实验
- [x] 在填色和模型卡报告中注明每张图使用一个洞外环带平均色，中心 1024 的 0.99 数据仅对应黑色预填充（PR #11 复审）
- [x] 先固定原尺度抽样顺序和拦截分母，再完成四组各 15 幅的四模型主比较及原掩码输入敏感性。[原尺度主实验](NATIVE_MAIN.md)
- [x] Claude 复审原尺度主结果、计数口径和文献树 v2（PR #13 已合并）
- [x] 核查随机 12 个 SDXL 输出，保存三列联系表，记录实际颜色、纹理和结构差异。核对固定 VAE，并同种子逐像素复现两个抽样输出。 [复审核查](NATIVE_REVIEW.md#sdxl-抽样核查)
- [x] 先冻结方案，再在克利夫兰 60×6 上补跑 SDXL strength 0.99 加环带均色，配对对照主设置、LaMa 和 MAT。 [对照结果](NATIVE_REVIEW.md#sdxl-环带均色缩小差距)
- [x] 核对 PowerPaint 拦截的 19 幅原作目录与 79 个条件日志，报告分组覆盖。单次补齐 79 个原拦截条件，补齐敏感性和安全检查开启的主结果分别报告。 [覆盖与敏感性](NATIVE_REVIEW.md#powerpaint-安全拦截)
- [x] 先冻结独立馆藏抽样，从芝加哥艺术博物馆每组取 15 幅，完成同一 360 条件、四模型主配置和两条原掩码敏感性。 [独立馆藏复现](AIC_REPLICATION.md)
- [x] 完成复审实验后按 paperwrite 技能起草英文论文，包含两馆结果、证据表和适用范围。 [论文初稿](PAPER_DRAFT.md)
- [x] Claude 复审 PR #15：实验部分通过并已合并；论文初稿需大改，详见 [复审意见](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/15#issuecomment-7057262583)
- [x] **Gemini · 重写论文**：按 [任务书](paper/WRITING_BRIEF.md) 把 v1 重写为 `docs/paper/draft-v2.md`，分支 `gemini/paper-rewrite-v2`。v1 只读（待 Claude 审查与 Codex 核对）
- [x] **Codex · 新颖性检索**：TD-Paint 已指出下采样的掩码信息损失，Diffusers #8450 已讨论低于 1.0 的预填色影响。稿件保留对画作条件的定量结果，以文献和源码定位机制。 [检索和 Gemini 口径](../literature/search-log.md#给-gemini-的机制表述)
- [x] **Codex · 参考文献池**：逐项核对 59 条来源，包括 44 篇正式论文、4 篇预印本和 11 条档案或官方资源。Controlled-300 标为未经同行评审。 [文献池](../literature/papers.csv)
- [x] **Codex · 配图**：图 1–5 已生成，服务器数据盘保留 PDF、300 dpi PNG 及校验清单。 [生成说明](paper/FIGURES.md)
- [x] **Codex · 核对 Gemini 稿**：在作者提交 `67a0d6d` 上核对 v2 表 1–7、证据范围和所有引用。补全 15 个引用占位和表 3 的逐条件差值，附经验证的图注及全量对照结果，成果在 `codex/verify-gemini-v2`。
- [x] **Codex · 可选实验**：先冻结方案，再在克利夫兰 60×6 上完成 PowerPaint 和 SDXL 的 720 个原掩码条件，按两组共同可用条件汇总。 [原掩码全量对照](NATIVE_APERTURE.md)
- [x] **流程**：运行记录写入代码提交、工作区状态和 diff 哈希（PR #18 完成，见 [RUN_PROVENANCE](RUN_PROVENANCE.md)）
- [x] Claude 复审 PR #18、#19，均已合并；v2 作为草稿保留，修改意见见 [#19 复审](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/19#issuecomment-7062267993)
- [x] **Codex · 图 1、图 2 PowerPoint 草图**：布局已审，PR #24 合并
- [x] **Gemini · v3 首轮**：按 [#19 复审](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/19#issuecomment-7062267993) 的 9 条修改，交付 `docs/paper/draft-v3.md`、`SUPPLEMENT.md` 与 `HANDOFF.md`（PR #23）
- [x] **Gemini · v3 第二轮**：已完成
- [x] **Gemini · v3 三处措辞**：已按 [PR #23 第二轮复审](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/23#issuecomment-7129366479) 把全部 6 处 `preregistered` 改为 `pre-specified`（首次写全 `pre-specified protocol, committed to version control before each inference run`，含 §3.1 标题并统一连字符），并将摘要末句与 §4.5 标题/结句的 `invariant` 限定在本研究范围内
- [x] **Codex · 复核 v3 第二轮**：数字与 52 条引文一致（PR #23 留言）；v3 已合并，只读
- [x] **Gemini · 投稿稿 v4**：以只读 v3 为底稿完成 `docs/paper/draft-v4.md`，修正 [Codex 三处口径](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/23#issuecomment-7129658292)、补齐五项投稿声明，并按 [Codex 四项核查](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/36#issuecomment-7156517893) 修订；PR #36 已合并
- [x] **Codex · 核对 v4**：表 1–7 数值、52 个引文键和声明事实已复核。[PR #36 复核](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/36#issuecomment-7156517893)
- [x] **作者 · 定目标期刊**：MDPI *Applied Sciences*（2026-11-25）
- [x] **Gemini · v5 正文与投稿信**：已完成（`6a34c78`），正文与既有证据用于 PeerJ 版排版。
- [x] **Codex · PeerJ Computer Science 投稿模板**：已编译正文、补充材料与投稿表单说明，核对 59 行表数据、56 条作者—年份参考文献、6 张独立图与 7 份表源。已为 Claude 准备审查包。[排版与复现](paper/peerj-cs/README.md)
- [x] **Claude · 摘要分段**：按 PeerJ 须知拆成 Background / Methods / Results / Conclusions 四段加粗小标题，字句不变（PR #44 审查）
- [x] **Codex · 公开代码与评审补件**：代码按作者选定使用 MIT，固定提交 `0b34175`。八个补件共 7,675 条条件记录，约 5.59 MB，已核准哈希、掩码关联、分母与主要评分汇总。[代码快照](https://github.com/liangdagongjue-code/mengwei/tree/0b3417599e6dfd88b9597789cfca762a91c66251)
- [x] **Codex · 软件归档 DOI**：Zenodo 已公开 MIT 源码 1.0.0，核验版本 DOI、匿名下载校验值和重编 PDF 的可点击链接。[软件归档](https://doi.org/10.5281/zenodo.24561409)
- [x] **Codex · 重编审查包**：已使用四段摘要和学校级单位，复验源 ZIP 编译。PeerJ LaTeX 正文 PDF 可内嵌图表，投稿时另传六张独立图件和七份可编辑表格。[作者须知](https://peerj.com/journals/computer-science/author-instructions/)
- [x] **Codex · PeerJ 作者声明**：更新无基金、无利益冲突、三人贡献和作者提供的 GPT-6 致谢，重编正文和投稿说明。
- [ ] **作者 · PeerJ 投稿前**：补齐译文核对责任人和历史模型版本，确认署名要求及稿件状态。按投稿界面上传八个评审补件并核对访问。[投稿交接](paper/SUBMISSION_PEERJ_CS.md)
- [ ] FLUX.1 Fill 原版全 BF16 常驻超出 24 GiB 且下载受限。取得授权组件后另测低显存配置的实际推理峰值
- [x] 按 findInnovation 模板起草[文献树 v2](literature-tree/literature-tree-v2.md)，核对通用补全、画作修复及自动评价的代表来源

## 已知问题

- OpenAlex 与 Semantic Scholar 的引文覆盖范围不同。Rocafort 目前在两者均未返回前向引用。ARTeFACT 现有目标类别的候选不足以支持两组各 15 个独立供体。
- 原尺度主实验四模型共同总体有 41 幅六条件完整，油画两组拦截较多。其余模型的配对保留全部 60 幅。原尺度实验及 SDXL 1024、空提示词敏感性均使用单种子。
- 两馆分别采用全尺寸档与 1686 像素宽 JPEG，等像素裁片对应的物理范围可以不同。克利夫兰有一张全黑源裁片，芝加哥有一幅纸贴卡水彩。均保留冻结口径并另做排除检查。

---

## 工作记录

### 2026-11-26 · Claude · claude/author-roles-discussion
- **作者贡献**：按作者决定，Wei Xiong 和 Zhanhao Liang 补上 “reviewed and edited the manuscript”。
- **写作讨论**：按作者建议，减数字修订前先请 Gemini 讨论写法，并在论文写作 skill 中加入初版规则 “Numbers in the text”（paperwrite `ed564c5`）。
- **AI 声明**：作者希望两处统一并以致谢为准；方法部分如何处理待作者回复，暂不修改。

### 2026-11-26 · Claude · claude/readability-pass
- **审查并合并 PR #46**：Zenodo DOI 已解析核实（1.0.0 版、MIT、提交 `0b34175`）；补件不含彩色图和权重。留给作者：Xiong、Liang 是否参与撰写或修订（ICMJE），致谢 GPT-6 与方法部分 AI 说明的衔接，Gemini/Codex 版本号。
- **按作者反馈写 [可读性任务书](paper/READABILITY_PASS.md)**：统计各节数字密度，派 Gemini 减数字、Codex 核对。

### 2026-11-26 · Codex · 更新作者声明与投稿说明
- 写入无基金、无利益冲突及作者提供的三人贡献。按原文加入 GPT-6 翻译润色致谢。
- 方法部分保留实际 AI 用途，依据提交记录补明 Claude Opus 5.5。译文核对责任、Gemini 和历史 Codex 的版本、署名的撰写或实质性修订要求列入[投稿交接](paper/SUBMISSION_PEERJ_CS.md)。
- 重编正文和投稿表单说明并校验审查包。新版在服务器数据盘 `paper/peerj-cs-submission/declarations-20261126/`。

### 2026-11-26 · Codex · 公开归档软件并更新 PeerJ 审查包
- 将固定提交 `0b34175` 的 MIT 源码归档为 Zenodo 1.0.0。匿名下载与已核验的源码 ZIP 一致。[版本 DOI](https://doi.org/10.5281/zenodo.24561409)
- 在正文 Data Availability 加入可点击的版本 DOI，复编并核对 29 页正文和 56 条参考文献。
- 更新源码 ZIP 和审查清单，保留原审查版。新包放在服务器数据盘的 `paper/peerj-cs-submission/doi-20261126/`。[审查包说明](paper/peerj-cs/README.md)

### 2026-11-26 · Codex · 补齐 MIT 代码与机器可读评审数据
- 作者确认前两位采用学校级单位，公开复现代码按 MIT 发布。匿名检出验证固定的源文件后生成软件归档 ZIP。
- 两馆、敏感性和先导数据分八个 ZIP，共 7,675 条条件记录，5,585,974 字节。核对 SHA-256、CSV 与 prepared 和掩码关联，并复算主要评分和 bootstrap 区间。主清单 SHA-256 为 `0aa073a0d45d341f71538a966c3d81d7555cff534b22420e735cfa8dcfcadcc3`，其中记录源方案与补件哈希。
- 复编四段摘要的审查版，并确认 LaTeX PDF 可内嵌图表。待注册软件 DOI 后补入最终版。[投稿交接](paper/SUBMISSION_PEERJ_CS.md)

### 2026-11-26 · Claude · claude/peerj-abstract
- **审查并合并 PR #44**（PeerJ CS 排版底座）。按须知把摘要改为四段加粗小标题，字句不变；登记代码 DOI、评审数据、院系与重编四项投稿前待办。正文唯一来源改为 `peerj-cs/manuscript.tex`。

### 2026-11-26 · Codex · 公开复现代码并填写 PeerJ 署名
- 公开指定复现仓库的 51 个研究代码和说明文件，匿名克隆逐件核对，9 项轻量测试通过。[固定提交](https://github.com/liangdagongjue-code/mengwei/tree/c1b6998f764f77c70318db5dde602324b1c78c60)
- 正文已加公开仓库链接，并在正文、补件和投稿说明登记三位作者，Wei Xiong 通讯。记录全体作者同意投稿。待确认资助、贡献、利益冲突、AI 版本和冻结数据归档。
- 复编审查包并验收署名页、PDF 链接及其余图表哈希。主清单 SHA-256 为 `a6f5a81dfc84bb126c1ad798940f461b4e5aef267ac3c9052a5b1730a440754e`。

### 2026-11-25 · Codex · 格式转为 PeerJ Computer Science
- 改用 PeerJ LaTeX 模板及初投规则，生成 29 页带行号正文、3 页 Supplemental Article S1、1 页投稿表单说明。保留 v5 的 193 词摘要和排序口径。
- 表 1–7 共 59 行逐格核对，56 条参考文献含四个权重发布件。六张独立 PNG 宽度 3000 px，另提供七份可编辑表源。
- 投稿 ZIP、PDF 和图表位于数据盘审查包。主清单 SHA-256 为 `040b0aeb34ddab7b3e9b71625fb9d6f5e107d793ebabcaff72dad0f1793b3bd0`。[投稿交接](paper/SUBMISSION_PEERJ_CS.md)

### 2026-11-25 · Claude · claude/pr38-followup
- **审查 PR #38**：权重版本与溯源说法核对无误，但改的是已合并只读的 v4，未合并，请 Codex 关闭。其内容已转入投稿任务书：Gemini 写进 v5 的 Data Availability，Codex 写进 `references.bib`。

### 2026-11-25 · Claude · claude/applsci-target
- **完成**：审查并合并 PR #37（Hopper 例图）与 PR #36（投稿稿 v4，解决 PROGRESS 冲突）。按作者决定定投 *Applied Sciences*，查阅作者须知后写 [投稿任务书](paper/SUBMISSION_APPLSCI.md)，给 Gemini 与 Codex 派活，同步 GEMINI.md、AGENTS.md 与决策记录。

### 2026-11-25 · Gemini · gemini/paper-v4（按 PR #36 Codex 核查修订四项）
- **完成**：在 PR #36（`gemini/paper-v4`）逐条落实 Codex 四项事实核查意见并同步 `docs/paper/HANDOFF.md`：
  1. 图 1 图注单例漏覆盖由 `52.9%` 更新为 `57.8%`（Hopper *Lighthouse Village* 主实验大图裁片 `watercolor_paper_02_crack_01`；并注明 1(b) 为同作品预填色实验备选图裁片，60 幅平均仍为 `59.5%`）；
  2. `Data Availability` 明确区分三层来源（公开馆藏、Git 仓库脚本与汇总、服务器归档中的 `prepared.json` / 清单 / 完整 JSON 汇总），并留作者确认归档访问方式占位；
  3. `Code Availability` 将 SDXL 权重许可改写为 `CreativeML Open RAIL++-M License`（按模型卡注明研究用途），LaMa/MAT/PowerPaint 各自指向所用发布工件，收紧 Git 与归档运行溯源表述（注明历史非 Git 运行提交字段可为空），并标明仓库许可证待作者确认；
  4. `Author Contributions` 按 NISO CRediT 拆分 `Investigation` 与 `Supervision`，并在利益冲突、作者贡献与生成式 AI 声明中清晰标明待作者投稿前确认项。
- **验证**：脚本校验题目 12 词、摘要 248 词、图 1(a) `57.8%`、52 个引用键与 `papers.csv` 及文末 52 条文献一一对应、`git diff --check` 通过。

### 2026-11-25 · Gemini · gemini/paper-v4（投稿稿 v4）
- **完成**：以只读 v3 为底稿新建 `docs/paper/draft-v4.md` 并更新 `docs/paper/HANDOFF.md`（`PAPER_DRAFT.md`、`draft-v2.md`、`draft-v3.md` 均未改动）：
  1. 落实 PR #23 Codex 三处口径修正：表 5 脚注与 §4.4 明确 19 幅受影响作品仅重放各自拦截条件（1–6 条不等，《The Trinity》全 6 条）并先幅内均值再对 19 幅等权；摘要与贡献 2 明确 `0.0725` 为中心掩码总体黑到环带差，§4.3 明确 `0.1137` 为原尺度 16 幅 5% 广片缺失条件均值；§2.1 将三项因素限定为本文所测潜空间扩散管线的操作与部署选择（明确安全检查为部署选择）。
  2. 补齐 `## Declarations` 五项投稿必需声明：`Data Availability`（CMA CC0、AIC 1686px 公有领域、确定性裁片与掩码生成代码、不二次分发原图）、`Code Availability`（仓库地址、开源许可证待投稿前补齐、四模型上游权重许可）、`Competing Interests`、`Author Contributions`（CRediT 占位模板待作者填署名）、`Declaration of Generative AI and AI-Assisted Technologies`（说明 Claude、Gemini、Codex 辅助写作与代码，作者审阅并负全责，AI 不列为作者）。
- **待同步项**：待 Codex 在服务器重跑 PR #35 明亮图 1(a) 示例后，把图 1(a) 图注的单例漏覆盖比例（当前仍为旧例 `52.9%`）更新为新例数值（60 幅均值 `59.5%` 不变）。
- **验证**：脚本校验题目 12 词、摘要 ≤ 250 词、52 个引用键与 `literature/papers.csv` 及文末 52 条文献一一对应、0 处 `preregister*`/`invariant`/`LaMa < MAT`/`unresized`、`git diff --check` 通过。

### 2026-11-25 · Codex · 重建 Hopper 例图并核对投稿稿 v4
- 用同一克利夫兰主实验裁片重建图 1(a) 与图 2，逐像素重算默认掩码漏覆盖 1,514 / 2,621（57.8%）。核对图 1(b) 三张预览图块与上版哈希相同，图 1 图注更新值已交 Gemini。
- 验收两张正式 PDF 的渲染、文字和嵌入字体，并在 PowerPoint 开启两份可编辑文件。服务器清单含两张图的素材与成品哈希。[正式版归档](paper/FIGURES.md)
- 核过 v4 的 65 行表格数值、52 个引文键与投稿声明。把公开文件范围、SDXL 权重许可和作者确认项写入 [PR #36](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/36#issuecomment-7156517893)。

### 2026-11-25 · Claude · claude/brighter-example
- **完成**：作者反映图 1(a)、图 2 的素材太黑。改为沿用 1(b) 已选中的作品（同一 artwork_id 的 1% 裂缝条件），洞的叠加色按画面明暗切换。`make_teaser_assets.py` 已改，待 Codex 在服务器重跑。

### 2026-11-24 · Claude · claude/after-v3
- **完成**：合并 PR #33（图 1、图 2 字距修复）和 PR #23（论文 v3，Codex 已复核数字与引文）；登记投稿稿 v4 待办（三处口径、投稿声明含生成式 AI 使用声明、作者通读与选刊）。

### 2026-11-24 · Gemini · gemini/paper-v3（三处措辞微调）
- **完成**：合并最新 `origin/main`（PR #30–#32）解决 `PROGRESS.md` 冲突；按 PR #23 Claude 第二轮复审意见完成 `docs/paper/draft-v3.md` 全部三处措辞修改并同步 `HANDOFF.md`（只读稿 v1、v2 未动）：
  1. 全部 6 处 `preregistered`/`Preregistering` 改为 `pre-specified`（引言首次出现写全为 `pre-specified protocol, committed to version control before each inference run`，含 §3.1 标题并统一全文 `pre-specified` 连字符）；
  2. 摘要末句改为 `In these cohorts, the best-performing model did not depend on painting medium, whereas reporting these three choices is essential for reproducible comparison.`；
  3. §4.5 标题改为 `Rankings held across damage geometries and painting media, whereas between-group contrasts varied across collections`（并同步收束 §4.5 结句的 `invariant`）。
- **验证**：脚本核对 0 处 `preregister*`、0 处 `prespecified`、0 处 `invariant`、题目 12 词、摘要 247 词、52 个引用键与 `papers.csv` 及文末条目一一对应，`git diff --check` 通过。

### 2026-11-24 · Claude · claude/review-followups-pr23-30
- **完成**：审查并合并 PR #30（新版布局的图 1、图 2）与 PR #31（图 2 标记位置）；审查 PR #23 第二轮，八条已落实，剩三处措辞加 Codex 复核。

### 2026-11-24 · Codex · 核对 v3 第二轮并修复成稿字距
- 比较正式 PDF 实际嵌入的 Arimo 与字形推进宽度，通过 SVG 精确定位修正 Chromium 导出。重建两张 PPTX、PDF 和预览，并核对图 2 右下角三个标记。
- 复核 v3 第二轮数字和引文。从服务器逐条件评分重算 40 幅、240 个共同条件的八个四模型均值。三处统计与部署表述已在 [PR #23](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/23#issuecomment-7129658292) 留言。

### 2026-11-23 · Codex · 用固定广片缺失例重建图 1 与图 2
- 从 16 个冻结的 5% 广片缺失条件按指定盐值选中 `watercolor_paper_02_loss_05`。按输出差异确定同一 251 × 251 px 窗口，验证全部 13,107 个差异像素均在计分洞内。
- 在数据盘重跑 FigGenie，图 1 为 2 × 2 通栏，图 2 为单栏两行。审查版 PPTX 和预览入库，论文版 PDF、300 dpi PNG、自包含 SVG 与清单保存在 `paper/figgenie-20261123/publication/`。

### 2026-11-23 · Gemini · gemini/paper-v3（第二轮修订）
- **完成**：合并最新 `origin/main` 解决 `PROGRESS.md` 冲突；按 PR #23 中 Codex 5 条事实核查与 Claude 3 条意见及最新 `fig1/spec.json`、`fig2/spec.json` 完成 `docs/paper/draft-v3.md` 第二轮修订，同步更新 `docs/paper/HANDOFF.md` 与 `literature/papers.csv`（只读稿 v1、v2 未动）。
- **关键改动**：题目压至 12 词；摘要 242 词并写明每项数字的分母与范围；引言四条贡献各控制在 1–2 个数字；图 1、图 2 图注按 FigGenie 最新 `caption_draft` 改写；§4.1 将 `≈` 严格限定于设阈值的 MAE/LPIPS；§4.2 改用 Codex 重算的 40 幅 / 240 条四模型共同样本（原掩码 0.0274/0.0284/0.1055/0.3087 vs. 扩张 0.0313/0.0337/0.0583/0.3115），移除仅归因于上下文的写法，并准确表述 SDXL 各条件正负变化；表 5 将重放行 19 幅移至表注并区分口径；补引固定版 PowerPaint 源码 `@powerpaintv1src`（同步入 `papers.csv`），明确 CIEDE2000 无符号、MISATO 两项指标、SDXL 0.99 示例与 MAT 固定种子确定性；修正 `TD-Paint` 署名顺序与 `Vicent Caselles` 拼写。
- **验证**：脚本核对 52 个正文引用键与 52 条文献条目及 `literature/papers.csv` 全部一一对应；题目 12 词、摘要 242 词；零 `LaMa < MAT`、零 `once...controlled`、零 `Vincent Caselles`、零 `unresized`、正文零超链接、`git diff --check` 通过。

### 2026-11-23 · Claude · claude/figures-grid-layout
- **完成**：审查并合并 PR #28（真实素材的图 1–6）。按作者意见把图 1 改为 2 × 2、图 2 改为单栏两行蛇形。1(b) 改为在 5% 广片缺失中选例，并放大到洞周围（`hole_window`）。
- **注意 / 坑**：本地预览用的是从 PPTX 中取出的旧素材，正式稿需由 Codex 在服务器重跑。

### 2026-11-21 · Codex · 交付真实素材图 1–2 与统一样式图 3–6
- 核验图 1(a) 和图 2 的同幅画裁片、六份冻结掩码及 LaMa 合成。图 1(b) 以独立固定哈希顺序选择同一条件的三种填色，使用归档输入算出实际环带色。
- 在服务器数据盘用 FigGenie 导出两图，lint 均为 0 错误。图库只收可编辑 PPTX、审查预览及文本源，正式 PDF 与 300 dpi PNG 在数据盘。
- 重绘图 3–6。图 5 的四模型均值和区间按同馆、同条件、共同可评分作品重新汇总。两套归档清单和复现命令见 [FIGURES.md](paper/FIGURES.md)。

### 2026-11-21 · Claude · claude/figures-less-text
- **完成**：按作者意见重画图 1、图 2：图中去掉解释文字和全部数字，只留图片、图形和短名称，数字移入图注；图 2 只给三个协议控制点着色。FIGURE_SPEC 补"图里几乎不放文字和数字"规则。

### 2026-11-21 · Claude · claude/figgenie-figures
- **完成**：按作者要求引入 FigGenie，用它重画图 1（teaser）和图 2（流程图），lint 均 0 错误，导出 PDF 与可编辑 PPTX（已去主题阴影）；新增 `experiments/make_teaser_assets.py` 与 `docs/paper/figures/src/build.sh`；FIGURE_SPEC 加"当前做法"一节调和规则。
- **注意 / 坑**：预览里画作和模型输出是占位图；svg2pptx 默认引用主题阴影，必须跑 `pptx_noshadow.py`；PPTX 中 ΔE 的下标会变成普通文字。

### 2026-11-21 · Claude · claude/review-followups-pr23-24
- **完成**：审查并合并 PR #24（图 1、图 2 布局草图），给出精修意见；审查 PR #23（论文 v3），九条修改均已落实，但需按 Codex 五条和 Claude 三条再改一轮，暂不合并。

### 2026-11-21 · Gemini · gemini/paper-v3
- **完成**：按 PR #19 复审全部 9 条修改意见与 `docs/paper/FIGURE_SPEC.md` 完成英文正文 `docs/paper/draft-v3.md`（未改动只读的 v1 `docs/PAPER_DRAFT.md` 与 v2 `docs/paper/draft-v2.md`），并将方法细节与交接附录分别移至 `docs/paper/SUPPLEMENT.md` 和 `docs/paper/HANDOFF.md`。
- **关键修订**：全稿修正因果表述（改为受控协议下排序一致，三项协议改变误差幅度与参与评分样本但未反转排序）；摘要压至 235 词以内且仅保留 6 个核心数字；§4.2、摘要和贡献 1 改以 60 幅全量原掩码对照（`docs/NATIVE_APERTURE.md`，含 PowerPaint 0.1055→0.0583、可用率 300/360→281/360、SDXL +0.0008 及分条件反向变化）为主、16 幅先导作佐证；全稿统一排序写法为 `LaMa ≈ MAT < PowerPaint v1 < SDXL`；删去 §4.2 近黑像素旧假设段落；按 `FIGURE_SPEC.md` 重排并重写图 1（teaser）至图 6 图注；§3.1 补入自全量原掩码对照起运行记录写入代码提交的说明。
- **验证**：脚本核对 51 个引用键全数命中 `literature/papers.csv`、零 `LaMa < MAT`、零 `once...controlled`、零 `near-black`、正文零超链接、`git diff --check` 通过。

### 2026-11-21 · Claude · claude/figure-palette
- **完成**：按作者要求把配色改为顶会图实测配色（BrushNet、PowerPaint、4K4D 原图像素统计），补充 4K4D、PowerPaint 两项画法参考；美化改由 Claude 完成，预览 PNG 进 Git 供审查。

### 2026-11-21 · Codex · 交付论文图 1、图 2 的 PowerPoint 布局草图
- 用 python-pptx 生成图 1 的三栏与 MAE 底栏、图 2 的六步流程。原生分组和命名，两个可用率方块图各含 360 个原生方格。
- 核对图 1 的 60 幅裂缝漏覆盖、40 幅 PowerPaint 配对、16 幅 SDXL 填色对照及两馆安全检查分母。PowerPoint 导出后检查 PDF 成图，预览随草图入库。
- 服务器数据盘保留六张论文风格参考缩略图及来源校验清单。布局确认后由 Claude 按任务书精修。
- 核对 v3 表 1–7 和 51 个引用键，在服务器归档复核两馆八个分层和克利夫兰 40 幅共同配对样本的 MAE 排序。图注分母、结论范围及两处书目已在 [PR #23](https://github.com/Casey-sketch-cyber/wei-xiong-ai3d-research/pull/23#issuecomment-7063082708) 留言。

### 2026-11-21 · Claude · claude/figure-spec
- **完成**：写配图设计说明 `docs/paper/FIGURE_SPEC.md`（参考画法、统一配色与字体、图 1–6 元素、图标来源、草图到精修的交付流程）；任务书的配图一节改为指向它。
- **注意 / 坑**：彭老师写作模板第 1、6 步是画 pipeline 草图和美化 teaser，模板里的"论文画图模板"未公开。

### 2026-11-21 · Claude · claude/review-followups-pr18-19
- **完成**：复审并合并 PR #18（配图、文献池、全量原掩码对照）和 #19（Gemini v2 与 Codex 核对）；登记 v3 九条修改；按作者要求改为用 PowerPoint 画 teaser 和流程图，并写图 1 规格。
- **注意 / 坑**：v2 把"控制三项后排序一致"写成了因果，v3 必须改；第 4.2 节要以 60 幅全量对照为主。

### 2026-11-20 · Codex · 完成文献、配图、v2 核对和 60 幅原掩码补跑
- 核对 TD-Paint 与 Diffusers 既有机制讨论，文献池补至 59 条。Gemini 稿 51 个引用键均解析，Controlled-300 标明为非同行评审档案。
- 用 `985d2c8` 在服务器生成五张论文图及校验清单，逐图核查 PDF、300 dpi PNG 与联系表。图 2 来源为克利夫兰馆方 CC0。
- `f2c6a32` 冻结全量原掩码对照。实际推理从干净提交 `a174360` 启动。共享扩张使 PowerPaint 的配对 MAE 下降 0.0471，可用输出从 300/360 降至 281/360。SDXL 在细裂缝和小片剥落上改善，总体差为 +0.0008。
- 核对 Gemini 稿表 1–7 与各自分母，补齐 15 个引用占位及先导逐条件结果，在 §4.2 附 60 幅的全量结果。

### 2026-11-21 · Gemini · gemini/paper-rewrite-v2
- **完成**：按 `docs/paper/WRITING_BRIEF.md` 和 `paperwrite` 技能将英文论文重写为 `docs/paper/draft-v2.md`（未改动只读的 `docs/PAPER_DRAFT.md`）。确立“三项协议选择大幅改变测得误差，控制后四模型排序在两馆、四画种、六破损上完全一致”的核心故事线；补齐 Related Work 三条脉络、引言贡献列表、§4.1–§4.5 完整结果小节（表 1–7）、图 1 Mermaid 流程图与图 2–5 占位及图注；局限集中写入 §5.3；正文无超链接、无“first/novel”类宣称、无“unresized”措辞。
- **交接给 Codex**：正文共使用 33 条 `literature/papers.csv` 已有引用键（全数匹配）和 15 条 `[@TODO-...]` 待入库核对键，另在表 3 标注 1 处可选逐条件差值占位 `[TODO-table3-per-condition-deltas]`，全部清单见 `docs/paper/draft-v2.md` 附录及分支提交说明。

### 2026-11-21 · Claude · claude/gemini-rewrite-brief
- **完成**：按作者决定改为 Gemini 重写正文、Codex 负责配图和文献；写 Gemini 任务书 `docs/paper/WRITING_BRIEF.md`，新增 `GEMINI.md`，更新 AGENTS.md 的阶段和分工，重新分配论文待办。
- **注意 / 坑**：任务书里修正了我在 PR #15 的说法：三个协议细节大幅改变测得的误差，但没有改变排名，不能写成"影响超过模型差别"。

### 2026-11-21 · Claude · claude/review-followups-pr15
- **完成**：复审并合并 PR #15（克利夫兰复审、芝加哥复现、论文初稿）；核对 Kachkine 2025 与 Imagest 的 DOI；登记论文修改五项和运行记录流程一项。
- **注意 / 坑**：实验阶段基本完成，接下来以改稿为主；潜空间漏覆盖和预填充是论文的主要卖点，写之前先做新颖性检索。

### 2026-11-20 · Codex · 完成复审实验、独立馆藏复现和英文初稿
- 在 `2cbad02` 先冻结复审与芝加哥抽样。核对 12 个随机案例的联系表、固定 VAE 哈希与两次逐像素 SDXL 复算。
- 克利夫兰 SDXL 环带配置的 MAE 为 0.1114，与 LaMa 的配对差为 +0.0789。PowerPaint 79 个原拦截条件的单次重放全部输出，补齐后的比较排序维持。
- 核验芝加哥 60 幅来源及 2,150 个输出。PowerPaint 主设置可评分 350/360，四模型完整作品 54 幅。两馆按自身分母报告。
- 按 paperwrite 完成英文初稿、流程图和主张证据表。原图、权重、联系表、逐项结果和运行日志保存在服务器数据盘。

### 2026-11-21 · Claude · claude/review-followups-pr13
- **完成**：复审并合并 PR #13（原尺度主实验、馆藏计数、文献树 v2）；登记 SDXL 核查、最有利设置、PowerPaint 拦截和独立馆藏复现四项待办。
- **注意 / 坑**：主实验的 60 幅与先导重叠，论文需写明并用独立馆藏复现。

### 2026-11-20 · Codex · 完成原尺度主实验与资料扩展
- 单独提交 `8e66b90` 固定队列、遮挡和分母。60 幅均取得馆方全尺寸，冻结四组各 15 幅、共 360 个裁片条件。先导的 16 幅保留在队列。
- RTX 3090 完成 2,160 个计划条件并逐图核验 2,081 份输出。PowerPaint 的 79 个无输出条件均为安全检查拦截。四模型共同完整 41 幅，其他模型配对使用 60 幅。
- 共享遮挡与原掩码敏感性均支持 LaMa、MAT 的总体接近。汇总记录五个指标、两种比较的分母、作品级区间和实际运行时间。
- 补齐克利夫兰及五家外部馆藏的供给证据并完成文献树 v2。ARTeFACT 补查两个版本及作者资料，记录逐图出处映射和掩码再用条款仍待提供。

### 2026-11-20 · Claude · claude/review-followups-pr11
- **完成**：复审并合并 PR #11；确认先方案后结果、环带取色不读洞内像素；同意正文保留 strength 1.0。
- **注意 / 坑**：SDXL 设置已连续三轮复查，结论稳定；后续优先做原尺度扩样、CC0 计数和文献树 v2。

### 2026-11-20 · Codex · 完成 SDXL 预填充颜色配对
- 先单独提交冻结方案。环带只用扩张模型掩码外 8 像素的已知区域。复核 Euler 首次输入的图像潜变量系数约为 0.118，并将两条图像路径写入模型卡报告。
- 新增 312 份输出，和 156 个旧黑色输出配对。全部重算 MAE 并核对洞外像素。汇总保留实际起止时间和输入、输出哈希，完整产物留在服务器数据盘。
- 中心掩码的黑色、环带 MAE 为 0.2342、0.1618，原尺度为 0.1513、0.0981。两类场景中更换填色明显增亮，原尺度低 MAE 在改用环带后进一步降低。正文采用 1.0 主比较及 0.99 三色敏感性。

### 2026-11-20 · Claude · claude/review-followups-pr9
- **完成**：复审并合并 PR #9；在 PR 留言说明黑色预填充经 strength 0.99 进入初始潜变量的机制，登记预填充对照等待办。
- **注意 / 坑**：本项目为防止答案泄漏用预遮挡输入，所以 strength<1 的结果取决于预填充颜色，不等同于模型卡原意。

### 2026-11-19 · Codex · 完成上游参数核对与 SDXL 重跑
- 在推理前提交 `a7bf504`，冻结 0.99、CFG 8、20 请求步的模型卡组合。在中心掩码 512 和 1024 各完成 60 次，在原尺度 512 完成 96 次。复核固定调度器实际去噪步数为 19。
- 按同作品同条件报告五项全参考指标和亮度。模型卡组合在原尺度将 SDXL 的 MAE 从 0.2730 降到 0.1513，在中心 1024 由 0.2492 增到 0.3465。输出整体转暗或进一步变暗。两种尺寸的四组中心掩码仍选 LaMa。
- 对齐核对 PowerPaint 的任务词、推理尺寸与步数，以及 MAT 的作者权重、噪声路径和播种。保留各自现有配置用于配对，详见决策记录。模型、输出及诊断存于服务器数据盘。

### 2026-11-19 · Claude · claude/review-followups-pr7
- **完成**：复审并合并 PR #7；确认修正协议在重跑前单独提交（be32fca），诊断表与修正结果和代码一致。
- **待办**：SDXL 按模型卡推荐设置重跑，已写入上方待办。
- **注意 / 坑**：之前审查推测漏覆盖像素会保留黑色预填，诊断显示漏覆盖区偏亮而非偏黑（管线在标准化空间置零，相当于灰色），这一推测不成立；漏覆盖本身属实。

### 2026-11-19 · Codex · 按 Claude 审查完成掩码修订与重跑
- 用 796 份旧输出复核网格覆盖。确认 1% 裂缝和剥落的漏覆盖过半，亮度和区域 MAE 未支持黑预填是主要原因。用 PyTorch 复核 39 份掩码在两种推理分辨率下对齐后无原洞漏格。
- 按独立提交 `be32fca` 的协议，在 RTX 3090 重跑六组，864 个计划条件保存 853 份图像，11 个均为 PowerPaint 内置安全检查拦截。数据、模型、日志和诊断存于服务器数据盘。
- 初版四组仍选 LaMa。修正后，1024 的单种子 MAE 差区间覆盖零，空提示词的 MAE 下降。原尺度保留同一批 16 幅作品，四模型共同完整 12 幅，另见修正前后各模型的匹配比较。
- 重算两种色差和局部 DISTS，逐图验证原掩码外像素与 MAE。校正旧报告中的汇总校验值，确认历史文件与本轮开跑前逐字节一致。把修正结果推回 PR #7 并登记复审。

### 2026-11-19 · Codex · 完成复审后的敏感性与原尺度先导
- 推理前提交追加协议。初版四组均选 LaMa。新 1024 与空提示词各 60 次，保留原主结果不变。量化色差和局部 DISTS。
- 原尺度四组各四幅，三类两面积档。LaMa、SDXL、MAT 各 96 次成功，PowerPaint 88 次成功和 8 次安全检查拦截。全部 496 份新增输出已逐图核查。
- FLUX.1 Fill 纯 BF16 权重最低约 31.43 GiB，官方访问返回 401，记录预检状态。全量输入、权重、缓存与结果继续保存在服务器数据盘。

### 2026-11-19 · Claude · claude/review-followups-pr5
- **完成**：复审并合并 PR #5（程序掩码四组先导）；核对了模型调用、合成、指标、裁剪和掩码生成代码，未发现数据或许可问题。
- **待办**：设计与公平性修订已写入上方待办。
- **注意 / 坑**：先导结果按协议执行无误，但受分辨率和掩码位置设计限制，暂不能当作论文主结论。

### 2026-11-18 · Codex · 完成 RTX 3090 程序掩码先导
- 核对 ARTeFACT 全部 49 条画作的像素标注，确认局部材料缺失的候选数低于门槛。按已审协议执行程序掩码分层。
- 新增 `experiments/`，固定馆藏、掩码、模型版本、随机种子和指标。服务器数据盘保留输入、权重、缓存、输出和日志。
- 四组各 15 幅，LaMa 与 SDXL 共 300 次成功，零失败。逐图核对像素与分数，汇报作品级区间及样本量估计。详见 [结果报告](PROCEDURAL_PILOT.md)。

### 2026-11-19 · Claude · claude/review-followups-pr3
- **完成**：复审并合并 PR #3（Codex 文献核查与先导协议）；独立核实 InkRenew（Crossref 10.1057/s41599-026-07117-y）、Controlled-300、Imagest、MAPGR、MDTD-ArtIR、HalluGen 的书目与关键描述。
- **待办**：已把复审建议写入上方待办。
- **注意 / 坑**：InkRenew 图 5 原句与薛文喆等论文的图注，Claude 当前环境打不开，未独立核对，依据为 Codex 的核查记录。

### 2026-11-18 · Codex · 按 Claude 审查修订 PR #3
- 用 Crossref、出版社图 5 和作者单位核实 InkRenew。补核中文期刊正文、Controlled-300 发布快照及 Imagest 表 2。
- 选择真实形状同技法、同基底移植。统一程序掩码下的分层比较单列为主问题。方案写明评分、区间、阈值、技术失败和缺供体时的处理。
- 将审查六项处理结果写入待办，等待复审。供体逐件核查与 3090 实测仍待完成。

### 2026-11-18 · Codex · 核查画作补全文献与研究定位
- 追踪五个种子的前向引用，核对 Controlled-300、Imagest、MDTD-ArtIR、InkRenew、MAPGR 等直接先例；把引文覆盖和勘误写入 `literature/`。
- 核实 arXiv 发表信息，补充 ICOM-CC 和 AIC 原文。读取 ARTeFACT 的 28 个元数据分片，确认 49 条 Painting 记录。
- 用 findInnovation 模板草拟真实轮廓与合成轮廓的配对先导方案。主要待办为掩码授权、按画材统计开放画作、确认模型运行条件以及审查设计。

### 2026-11-18 · Claude · claude/painting-restoration-literature-tree
- **完成**：仓库改为新方向；旧 M03 内容保存到分支 `archive/m03-ai3d-20261118`；按 findInnovation skill 起草文献树 v1（三条脉络、文献表 36 条、难点—解法树、四种情况判断）；建立检索记录和文献表；补齐协作文档。
- **未完成**：被引列表排查；数据源许可核对；创新点评估文档。
- **注意 / 坑**：文献概括来自摘要页或对全文的检索摘录，没有通读全文；多数 arXiv 页面没写发表处。
