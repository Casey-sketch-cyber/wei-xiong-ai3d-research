# 项目进度（交接记录）

> 每个 AI 结束工作前在"工作记录"最上方追加一条，新的在上面。

## 当前状态

已完成文献树 v1 的首轮引文核查。已有多模型画作评测、真实破损形状移植和语义幻觉分析先例。候选问题收窄为同图、同面积、同位置下，真实破损轮廓是否改变模型排序，以及这种效应是否随画材变化。仍处于调研阶段。

## 待办

- [x] 用 LaMa、ARTeFACT、Shao 2023、Kachkine 2025、Rocafort 2025 的前向引用及独立关键词检索核查文献树 v1，见 [核查记录](../literature/audit-of-claude-v1.md)
- [x] 核对文献表中 19 条 arXiv 记录，16 条找到正式发表处，另外 3 条仅确认预印本
- [x] 核对 ARTeFACT 数据卡许可和样本元数据。418 条记录中 49 条标为 Painting
- [ ] 核实 ARTeFACT 掩码单独移植和公开分发的授权范围，以及各破损类的可用掩码数
- [ ] 统计 CC0 画作按画种的可得数量（大都会、芝加哥艺术博物馆、荷兰国立博物馆、美国国家美术馆、史密森尼）
- [x] 找到 ICOM-CC 术语决议和 AIC 补失指南，已写入 [核查记录](../literature/audit-of-claude-v1.md#指标和修复伦理)
- [ ] 在 3090 上实测候选补全模型的显存：LaMa、MAT、SDXL Inpainting、BrushNet 或 PowerPaint、FLUX.1 Fill
- [x] 用 findInnovation 模板起草 [创新点评估](INNOVATION.md)
- [ ] 审查核查记录与配对先导方案。修订文献树时另起 v2

## 已知问题

- OpenAlex 与 Semantic Scholar 的引文覆盖范围不同。Rocafort 目前在两者均未返回前向引用。数据卡未提供 ARTeFACT 的逐图来源和许可字段，尚不能确认公开移植后的掩码。

---

## 工作记录

### 2026-11-18 · Codex · 核查画作补全文献与研究定位
- 追踪五个种子的前向引用，核对 Controlled-300、Imagest、MDTD-ArtIR、InkRenew、MAPGR 等直接先例；把引文覆盖和勘误写入 `literature/`。
- 核实 arXiv 发表信息，补充 ICOM-CC 和 AIC 原文。读取 ARTeFACT 的 28 个元数据分片，确认 49 条 Painting 记录。
- 用 findInnovation 模板草拟真实轮廓与合成轮廓的配对先导方案。主要待办为掩码授权、按画材统计开放画作、确认模型运行条件以及审查设计。

### 2026-11-18 · Claude · claude/painting-restoration-literature-tree
- **完成**：仓库改为新方向；旧 M03 内容保存到分支 `archive/m03-ai3d-20261118`；按 findInnovation skill 起草文献树 v1（三条脉络、文献表 36 条、难点—解法树、四种情况判断）；建立检索记录和文献表；补齐协作文档。
- **未完成**：被引列表排查；数据源许可核对；创新点评估文档。
- **注意 / 坑**：文献概括来自摘要页或对全文的检索摘录，没有通读全文；多数 arXiv 页面没写发表处。
